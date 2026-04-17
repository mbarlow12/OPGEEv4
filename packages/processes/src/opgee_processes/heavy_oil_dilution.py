#
# HeavyOilDilution class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import TemperaturePressure
from ..import_export import DILUENT
from ..process import Process
from ..thermodynamics import Oil, Water
from .shared import get_energy_carrier
from .transport_energy import TransportEnergy


class HeavyOilDilution(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        water: Water,
        transport_energy: TransportEnergy,
        transport_share_fuel: pd.Series,
        transport_parameter: pd.DataFrame,
        transport_by_mode: pd.Series,
        frac_diluent: Quantity[float],
        downhole_pump: bool,
        oil_sands_mine: str,
        mined_bitumen_t: Quantity[float],
        mined_bitumen_p: Quantity[float],
        diluent_API: Quantity[float],
        dilbit_API: Quantity[float],
        dilution_type: str,
        diluent_temp: Quantity[float],
        before_diluent_temp: Quantity[float],
        before_diluent_press: Quantity[float],
        final_mix_temp: Quantity[float],
        final_mix_press: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "oil for dilution"
        ]

        self._required_outputs = [
            ("oil for storage",
             "oil for upgrading")
        ]

        self.oil = oil
        self.water = water
        self.water_density = water.density()

        self.transport_energy = transport_energy
        self.transport_share_fuel = transport_share_fuel
        self.transport_parameter = transport_parameter
        self.transport_by_mode = transport_by_mode

        self.frac_diluent = frac_diluent
        self.downhole_pump = downhole_pump
        self.oil_sands_mine = oil_sands_mine

        self.bitumen_tp = TemperaturePressure(mined_bitumen_t, mined_bitumen_p)
        self.diluent_tp = TemperaturePressure(diluent_temp, diluent_temp)
        self.before_diluent_tp = TemperaturePressure(before_diluent_temp, before_diluent_press)
        self.final_mix_tp = TemperaturePressure(final_mix_temp, final_mix_press)

        self.diluent_API = diluent_API
        self.dilution_SG = oil.specific_gravity(diluent_API)
        self.dilbit_API = dilbit_API
        self.dilbit_SG = oil.specific_gravity(dilbit_API)
        self.dilution_type = dilution_type

    def run(self):
        self.print_running_msg()

        # mass rate
        input_oil = self.find_input_streams("oil for dilution", combine=True)

        # TODO: need to raise error message
        # if self.frac_diluent.m == 0.0:
        #     return

        if input_oil.is_uninitialized():
            return

        input_liquid_mass_rate = input_oil.liquid_flow_rate("oil")
        oil_SG = self.oil.specific_gravity(input_oil.API)
        input_liquid_volume_rate = input_liquid_mass_rate / (oil_SG * self.water_density)

        frac_diluent = self.frac_diluent
        expected_volume_oil_bitumen = input_liquid_volume_rate if abs(frac_diluent.to("frac").m - 1) <= 0.01 else \
            input_liquid_volume_rate / (1 - frac_diluent)
        required_volume_diluent = expected_volume_oil_bitumen * frac_diluent

        if self.dilution_type == DILUENT:
            required_mass_dilution = required_volume_diluent * self.dilution_SG * self.water_density
            total_mass_diluted_oil = required_mass_dilution + input_liquid_mass_rate
            diluent_LHV = self.oil.mass_energy_density(API=self.diluent_API)
        else:
            total_mass_diluted_oil = expected_volume_oil_bitumen * self.dilbit_SG * self.water_density
            required_mass_dilution = total_mass_diluted_oil if frac_diluent == 1 else \
                max(0, total_mass_diluted_oil - input_liquid_mass_rate)
            diluent_SG = required_mass_dilution / required_volume_diluent / self.water_density
            diluent_LHV = self.oil.mass_energy_density(API=self.oil.API_from_SG(diluent_SG))

        output_oil = self.find_output_stream("oil for storage", raiseError=False)
        if output_oil is None:
            output_oil = self.find_output_stream("oil for upgrading")
        output_oil.set_liquid_flow_rate("oil", total_mass_diluted_oil, tp=self.final_mix_tp)
        self.set_iteration_value(output_oil.total_flow_rate())

        self.ctx.process_data["final_diluent_LHV_mass"] = diluent_LHV

        final_diluent_SG = \
            total_mass_diluted_oil / expected_volume_oil_bitumen / self.water_density
        final_diluent_API = self.oil.API_from_SG(final_diluent_SG)
        output_oil.set_API(final_diluent_API)

        diluent_energy_rate = required_mass_dilution * diluent_LHV

        # Calculate imported diluent energy consumption
        fuel_consumption = self.transport_energy.get_transport_energy_dict(
            self.transport_parameter,
            self.transport_share_fuel,
            self.transport_by_mode,
            diluent_energy_rate,
            DILUENT,
            diluent_LHV,
        )

        energy_use = self.energy
        for name, value in fuel_consumption.items():
            energy_use.set_rate(get_energy_carrier(name), value.to("mmBtu/day"))

        # import/export
        self.set_import_from_energy(energy_use)
        self.import_export.set_export(self.name, DILUENT, diluent_energy_rate)

        # emissions
        self.set_combustion_emissions()
