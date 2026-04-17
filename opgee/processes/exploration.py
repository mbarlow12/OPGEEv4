#
# Exploration class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging
import math

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..energy import EN_DIESEL
from ..process import Process
from ..thermodynamics import Oil
from ..units import ureg
from .transport_energy import TransportEnergy

_logger = logging.getLogger(__name__)


class Exploration(Process):
    """
        The Exploration class represents the exploration phase of an oil field project.

        This class calculates the energy consumption and emissions associated with
        drilling, surveying, and transporting crude oil during the exploration phase.
    """
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        transport_energy: TransportEnergy,
        transport_parameter: pd.DataFrame,
        vertical_drill_df: pd.DataFrame,
        horizontal_drill_df: pd.DataFrame,
        well_size: str,
        well_complexity: str,
        eta_rig: str,
        oil_sands_mine: str,
        offshore: bool,
        weight_land_survey: Quantity[float],
        weight_ocean_survey: Quantity[float],
        distance_survey: Quantity[float],
        number_wells_dry: int,
        number_wells_exploratory: int,
        num_prod_wells: int,
        natural_gas_reinjection: bool,
        gas_flooding: bool,
        num_water_inj_wells: int,
        depth: Quantity[float],
        frac_wells_horizontal: Quantity[float],
        length_lateral: Quantity[float],
        field_production_lifetime: Quantity[float],
        diesel_LHV: Quantity[float],
        days_per_year: Quantity[float],
    ):
        super().__init__(name, ctx)

        self.oil = oil
        self.transport_energy = transport_energy
        self.transport_parameter = transport_parameter

        self.well_size = well_size
        self.well_complexity = well_complexity
        self.eta_rig = eta_rig
        self.oil_sands_mine = oil_sands_mine
        self.offshore = offshore
        self.weight_land_survey = weight_land_survey
        self.weight_ocean_survey = weight_ocean_survey
        self.distance_survey = distance_survey
        self.number_wells_dry = number_wells_dry
        self.number_wells_exploratory = number_wells_exploratory
        self.depth = depth
        self.frac_wells_horizontal = frac_wells_horizontal
        self.length_lateral = length_lateral
        self.field_production_lifetime = field_production_lifetime
        self.days_per_year = days_per_year

        self.vertical_drill_energy_intensity = \
            (vertical_drill_df.loc[eta_rig]).loc[well_size][well_complexity]
        self.horizontal_drill_energy_intensity = \
            (horizontal_drill_df.loc[eta_rig]).loc[well_size][well_complexity]

        num_prod_wells_effective = num_prod_wells if oil_sands_mine == "None" else 0
        self.num_gas_inj_wells = 0.25 * num_prod_wells_effective if natural_gas_reinjection or gas_flooding else 0
        self.num_water_inj_wells = num_water_inj_wells
        self.num_wells = math.ceil(num_prod_wells_effective + self.num_water_inj_wells + self.num_gas_inj_wells)

        self.drill_fuel_consumption = \
            (self.vertical_drill_energy_intensity * (1 - frac_wells_horizontal) * depth +
             self.horizontal_drill_energy_intensity * frac_wells_horizontal * length_lateral) * self.num_wells
        self.drill_energy_consumption = diesel_LHV * self.drill_fuel_consumption

    def run(self):
        self.print_running_msg()

        oil_mass_energy_density = self.oil.mass_energy_density()
        if self.ctx.process_data.get("crude_LHV") is None:
            self.ctx.process_data["crude_LHV"] = oil_mass_energy_density

        ocean_tank_energy_intensity = \
            self.transport_energy.get_ocean_tanker_dest_energy_intensity(self.transport_parameter)
        truck_energy_intensity = self.transport_energy.energy_intensity_truck

        export_LHV = self.ctx.process_data.get("exported_prod_LHV")
        cumulative_export_LHV = export_LHV * self.field_production_lifetime * self.days_per_year

        survey_vehicle_energy_consumption = (truck_energy_intensity * self.weight_land_survey *
                                             self.distance_survey if not self.offshore else
                                             ocean_tank_energy_intensity * self.weight_ocean_survey *
                                             self.distance_survey)

        drill_consumption_per_well = (self.drill_energy_consumption / self.num_wells
                                      if self.oil_sands_mine == "None" else ureg.Quantity(0.0, "mmbtu"))

        drill_energy_consumption = drill_consumption_per_well * (self.number_wells_dry + self.number_wells_exploratory)
        frac_energy_consumption = (survey_vehicle_energy_consumption + drill_energy_consumption) / cumulative_export_LHV
        diesel_consumption = frac_energy_consumption * export_LHV

        self.ctx.process_data["cumulative_export_LHV"] = cumulative_export_LHV
        self.ctx.process_data["drill_energy_consumption"] = self.drill_energy_consumption
        self.ctx.process_data["num_wells"] = self.num_wells

        # energy-use
        energy_use = self.energy
        energy_use.set_rate(EN_DIESEL, diesel_consumption)

        # emissions
        self.set_combustion_emissions()
