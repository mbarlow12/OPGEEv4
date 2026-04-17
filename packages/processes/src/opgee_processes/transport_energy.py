#
# TransportEnergy class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import pandas as pd

from pint.facets.plain import PlainQuantity as Quantity

from ..units import ureg
from ..error import OpgeeException
from ..energy import EN_DIESEL


class TransportEnergy:
    """Helper class that computes energy consumed by various transport modes.

    All field-specific physical parameters are passed explicitly at construction
    time (``residual_oil_LHV``, ``residual_oil_density``, ``ocean_tanker_size``)
    so that this class carries no ``field`` reference.

    The per-call product-type denominator (LHV per unit mass for the product
    being transported) is passed as an explicit ``denominator`` argument to
    ``get_transport_energy_dict``.
    """

    def __init__(
        self,
        residual_oil_LHV: Quantity[float],
        residual_oil_density: Quantity[float],
        ocean_tanker_size: Quantity[float],
    ):
        self.residual_oil_LHV = residual_oil_LHV
        self.residual_oil_density = residual_oil_density
        self.ocean_tanker_size = ocean_tanker_size

        self.pipeline_dest_orig_energy_intensity = ureg.Quantity(0.0, "btu/tonne/mile")
        self.rail_dest_orig_energy_intensity = ureg.Quantity(200.0, "btu/tonne/mile")
        self.energy_intensity_truck = ureg.Quantity(969.0, "btu/(tonne*mile)")
        self.truck_dest_orig_energy_intensity = self.energy_intensity_truck

    def get_transport_energy_dict(
        self,
        parameter_table,
        transport_share_fuel,
        transport_by_mode,
        LHV_rate,
        prod_type: str,
        denominator: Quantity[float],
    ):
        """Calculate transport energy consumption and return fuel consumption for different transport modes.

        :param parameter_table: DataFrame with transport parameters
        :param transport_share_fuel: DataFrame with transport fuel share
        :param transport_by_mode: DataFrame with transport fractions and distances
        :param LHV_rate: LHV rate for the product type
        :param prod_type: can be "diluent", "lng", "crude", or "petrocoke"
        :param denominator: mass-energy density for the product type (Quantity with energy/mass units).
            Caller is responsible for providing the correct value:
            - "diluent"   → ctx.process_data["final_diluent_LHV_mass"]
            - "lng"       → gas.component_LHV_mass["C1"]
            - "crude"     → ctx.process_data["crude_LHV"]
            - "petrocoke" → petro_coke_heating_value / 1.10231
        :return: Fuel consumption dict for different transport modes
        """
        known_types = ["diluent", "lng", "crude", "petrocoke"]
        prod_type = prod_type.lower()
        if prod_type not in known_types:
            raise OpgeeException(f"{prod_type} is not in the known product type: {known_types}")

        parameter_dict = TransportEnergy.get_parameter_dict(parameter_table)
        ocean_tanker_load_factor_dest = parameter_dict["load_factor_to_dest_tanker"]
        barge_load_factor_dest = parameter_dict["load_factor_to_dest_barge"]
        ocean_tanker_load_factor_origin = parameter_dict["load_factor_to_orig_tanker"]
        barge_load_factor_origin = parameter_dict["load_factor_to_orig_barge"]
        barge_capacity = parameter_dict["capacity_barge"]
        ocean_tanker_speed = parameter_dict["speed_tanker"]
        ocean_tanker_size = self.ocean_tanker_size
        barge_speed = parameter_dict["speed_barge"]
        energy_intensity_pipeline_turbine = parameter_dict["energy_intensity_pipeline_turbine"]
        energy_intensity_pipeline_engine_current = parameter_dict["energy_intensity_pipeline_engine_current"]
        frac_power_pipeline_turbine = parameter_dict["frac_power_pipeline_turbine"]
        frac_power_pipeline_engine_current = parameter_dict["frac_power_pipeline_engine_current"]
        energy_intensity_pipeline_engine_future = parameter_dict["energy_intensity_pipeline_engine_future"]
        frac_power_pipeline_engine_future = parameter_dict["frac_power_pipeline_engine_future"]
        energy_intensity_rail_transport = parameter_dict["energy_intensity_rail_to_dest"]
        feed_loss = parameter_dict["feed_loss"]
        fraction_transport = transport_by_mode["Fraction"]
        transport_distance = transport_by_mode["Distance"]

        # Calculate transport energy intensity
        ocean_tanker_orig_dest_energy_intensity = \
            self.transport_energy_intensity(
                ocean_tanker_load_factor_dest,
                "tanker",
                ocean_tanker_speed=ocean_tanker_speed,
                ocean_tanker_size=ocean_tanker_size,
            )

        ocean_tanker_dest_orig_energy_intensity = \
            self.transport_energy_intensity(
                ocean_tanker_load_factor_origin,
                "tanker",
                ocean_tanker_speed=ocean_tanker_speed,
                ocean_tanker_size=ocean_tanker_size,
            )

        barge_orig_dest_energy_intensity = \
            self.transport_energy_intensity(
                barge_load_factor_dest,
                "barge",
                barge_capacity=barge_capacity,
                barge_speed=barge_speed,
            )

        barge_dest_orig_energy_intensity = \
            self.transport_energy_intensity(
                barge_load_factor_origin,
                "barge",
                barge_capacity=barge_capacity,
                barge_speed=barge_speed,
            )

        pipeline_orig_dest_energy_intensity = (energy_intensity_pipeline_turbine *
                                               frac_power_pipeline_turbine +
                                               energy_intensity_pipeline_engine_current *
                                               frac_power_pipeline_engine_current +
                                               energy_intensity_pipeline_engine_future *
                                               frac_power_pipeline_engine_future)


        transport_orig_dest_energy_consumption = \
            pd.Series([ocean_tanker_orig_dest_energy_intensity, barge_orig_dest_energy_intensity,
                       pipeline_orig_dest_energy_intensity, energy_intensity_rail_transport,
                       self.energy_intensity_truck], dtype="pint[btu/tonne/mile]")

        transport_dest_origin_energy_consumption = \
            pd.Series([ocean_tanker_dest_orig_energy_intensity, barge_dest_orig_energy_intensity,
                       self.pipeline_dest_orig_energy_intensity, self.rail_dest_orig_energy_intensity,
                       self.truck_dest_orig_energy_intensity], dtype="pint[btu/tonne/mile]")

        transport_energy_consumption = \
            (transport_orig_dest_energy_consumption + transport_dest_origin_energy_consumption) / denominator

        fuel_consumption = \
            TransportEnergy.fuel_consumption(
                fraction_transport,
                transport_distance,
                transport_share_fuel,
                transport_energy_consumption,
                feed_loss,
                LHV_rate)

        return fuel_consumption

    def get_ocean_tanker_dest_energy_intensity(self, parameter_table):
        """Calculate the energy intensity for ocean tankers from origin to destination.

        :param parameter_table: DataFrame with transport parameters
        :return: Energy intensity for ocean tankers from origin to destination (unit: btu/tonne/mile)
        """
        parameter_dict = TransportEnergy.get_parameter_dict(parameter_table)
        ocean_tanker_load_factor_dest = parameter_dict["load_factor_to_dest_tanker"]
        ocean_tanker_speed = parameter_dict["speed_tanker"]
        ocean_tanker_size = self.ocean_tanker_size

        ocean_tanker_orig_dest_energy_intensity = \
            self.transport_energy_intensity(
                ocean_tanker_load_factor_dest,
                "tanker",
                ocean_tanker_speed=ocean_tanker_speed,
                ocean_tanker_size=ocean_tanker_size,
            )

        return ocean_tanker_orig_dest_energy_intensity

    @staticmethod
    def get_parameter_dict(parameter_table):
        """Given Dataframe with name, value and unit, return parameter dictionary where key is
        the name and value is the ureg.Quantity with unit specified.
        """
        parameter_value = parameter_table.iloc[:, 0]
        parameter_unit = parameter_table["Units"]

        parameter_dict = {name: ureg.Quantity(float(value), parameter_unit[name])
                          for name, value in parameter_value.items()}

        return parameter_dict

    def transport_energy_intensity(self, load_factor, type, ocean_tanker_speed=None,
                                   ocean_tanker_size=None, barge_capacity=None, barge_speed=None):
        """Calculate transport energy intensity using load factor and water transport energy consumption.

        :param load_factor: (pint.Quantity) Load factor for the transport.
        :param type: (str) Transport type: "tanker" or "barge".
        :param ocean_tanker_speed: (pint.Quantity, optional) Speed of the ocean tanker, required if type is "tanker".
        :param ocean_tanker_size: (pint.Quantity, optional) Size of the ocean tanker, required if type is "tanker".
        :param barge_capacity: (pint.Quantity, optional) Capacity of the barge, required if type is "barge".
        :param barge_speed: (pint.Quantity, optional) Speed of the barge, required if type is "barge".
        :return: (float) Transport energy intensity.
        """
        residual_oil_LHV = self.residual_oil_LHV
        residual_oil_density = self.residual_oil_density

        known_types = ["tanker", "barge"]
        if type not in known_types:
            raise OpgeeException(f"{type} is not in the known transport type: {known_types}")

        # Calculate water transport energy consumption
        const = 150 if type == "tanker" else 350
        energy_consumption = (14.42 / load_factor.m + const) * 0.735 * residual_oil_LHV.m / residual_oil_density.m
        energy_consumption = ureg.Quantity(energy_consumption, "btu/hp/hr")

        hp = (ureg.Quantity(9070 + 0.101 * ocean_tanker_size.m, "hp") if type == "tanker"
              else ureg.Quantity(5600 / 22500 * barge_capacity.m, "hp"))

        common = energy_consumption * load_factor * hp
        if type == "tanker":
            result = common / ocean_tanker_speed / ocean_tanker_size
        else:  # must be "barge" since we checked.
            result = common / barge_capacity / barge_speed
        return result

    @staticmethod
    def fuel_consumption(fraction_transport,
                         transport_distance,
                         transport_share_fuel,
                         transport_energy_consumption,
                         feed_loss,
                         LHV):
        """Calculate fuel consumption for different transport types.

        :param fraction_transport: Series with fractions of transport types
        :param transport_distance: Series with transport distances for each transport type
        :param transport_share_fuel: Dictionary with fuel shares for each transport type
        :param transport_energy_consumption: Series with transport energy consumption for each transport type
        :param feed_loss: float, feed loss during transportation
        :param LHV: float, lower heating value of the fuel
        :return: Dictionary with fuel consumption for each transport type
        """
        transport_energy_consumption.index = transport_distance.index

        result = {
            type: (transport_energy_consumption * transport_distance * fraction_transport * frac).sum() * LHV + (
                LHV * feed_loss if type == EN_DIESEL else 0)
            for type, frac in transport_share_fuel.items()
        }
        return result
