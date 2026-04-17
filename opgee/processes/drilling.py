#
# Drilling class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import numpy as np
import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..emissions import EM_LAND_USE
from ..energy import EN_DIESEL
from ..process import Process
from ..stream import Stream
from ..thermodynamics import Oil
from ..units import ureg

_logger = logging.getLogger(__name__)


class Drilling(Process):
    """
        A class representing the drilling process in a field.

    Attributes
        fraction_wells_fractured : float
            The fraction of wells that are fractured.
        fracture_consumption_tbl : pandas.DataFrame
            The table containing fracture energy consumption data.
        pressure_gradient_fracturing : pint.Quantity
            The pressure gradient for fracturing.
        volume_per_well_fractured : pint.Quantity
            The volume per fractured well.
        oil_sands_mine : str
            The type of oil sands mine (if any).
        land_use_EF : pandas.DataFrame
            The table containing land use emission factors.
        ecosystem_richness : str
            The ecosystem richness category of the field.
        field_development_intensity : str
            The field development intensity category.
        num_water_inj_wells : int
            The number of water injection wells.
        num_wells : int
            The total number of wells (production + water injection).
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        fraction_wells_fractured: Quantity[float],
        pressure_gradient_fracturing: Quantity[float],
        volume_per_well_fractured: Quantity[float],
        oil_sands_mine: str,
        ecosystem_richness: str,
        field_development_intensity: str,
        oil_volume_rate: Quantity[float],
        offshore: bool,
        diesel_LHV: Quantity[float],
        fracture_consumption_tbl: pd.DataFrame,
        land_use_EF: pd.DataFrame,
    ):
        super().__init__(name, ctx)

        self.oil = oil
        self.fraction_wells_fractured = fraction_wells_fractured
        self.pressure_gradient_fracturing = pressure_gradient_fracturing
        self.volume_per_well_fractured = volume_per_well_fractured
        self.oil_sands_mine = oil_sands_mine
        self.ecosystem_richness = ecosystem_richness
        self.field_development_intensity = field_development_intensity
        self.oil_volume_rate = oil_volume_rate
        self.offshore = offshore
        self.diesel_LHV = diesel_LHV
        self.fracture_consumption_tbl = fracture_consumption_tbl
        self.land_use_EF = land_use_EF

    def run(self):
        self.print_running_msg()

        fracture_energy_constant = self.get_fracture_constant()
        fracture_diesel_use = self.get_fracture_diesel(fracture_energy_constant)
        num_wells = self.ctx.process_data.get("num_wells")
        fracture_fuel_consumption = self.fraction_wells_fractured * num_wells * fracture_diesel_use
        fracture_energy_consumption = fracture_fuel_consumption * self.diesel_LHV

        tot_energy_consumption = fracture_energy_consumption + self.ctx.process_data.get("drill_energy_consumption")
        wellhead_LHV_rate = self.ctx.process_data.get("wellhead_LHV_rate")
        cumulative_export_LHV = self.ctx.process_data.get("cumulative_export_LHV")
        diesel_consumption = wellhead_LHV_rate / cumulative_export_LHV * tot_energy_consumption

        # calculate land use emissions

        index_name = self.ecosystem_richness if self.oil_sands_mine == "None" else "Oil sands mining"
        land_use_intensity_df = self.land_use_EF.loc[index_name]
        land_use_intensity = land_use_intensity_df.loc[self.field_development_intensity]
        stream = Stream("stream_stp", tp=self.ctx.stp)

        oil_SG = self.oil.oil_specific_gravity
        boundary_API = self.ctx.process_data.get("boundary_API")
        if boundary_API is not None:
            oil_SG = self.oil.specific_gravity(boundary_API)
            stream.set_API(boundary_API)

        land_use_emission = \
            (land_use_intensity.sum() * self.oil_volume_rate * self.oil.volume_energy_density(
                stream,
                oil_SG,
                self.oil.gas_specific_gravity,
                self.oil.gas_oil_ratio)) if not self.offshore else ureg.Quantity(0, "tonne/day")

        # energy-use
        energy_use = self.energy
        energy_use.set_rate(EN_DIESEL, diesel_consumption)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_rate(EM_LAND_USE, "CO2", land_use_emission)

    def get_fracture_constant(self):
        """
        Calculate fracturing rig energy consumption constant a, b, c

        :return:Array list of const [a, b, c]
        """

        value = self.pressure_gradient_fracturing
        tbl = self.fracture_consumption_tbl
        result = [np.interp(value.m, tbl[col].index, tbl[col].values) for col in ['a', 'b', 'c']]

        return result

    def get_fracture_diesel(self, constants):
        """
        Calculate diesel use per well for fracturing

        :return: diesel use (unit=gallon)
        """
        volume = self.volume_per_well_fractured.m
        variables = [volume * volume, volume, 1]

        result = np.dot(variables, constants)
        result = ureg.Quantity(result, "gallon")
        return result
