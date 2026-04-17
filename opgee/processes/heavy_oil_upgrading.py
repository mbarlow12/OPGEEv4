#
# HeavyOilUpgrading class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import STP
from ..emissions import EM_FLARING
from ..energy import EN_NATURAL_GAS, EN_ELECTRICITY, EN_UPG_PROC_GAS, EN_PETCOKE
from ..import_export import ELECTRICITY, H2
from ..process import Process
from ..stream import PHASE_GAS, Stream
from ..thermodynamics import Gas, Oil, Water
from ..units import ureg

_logger = logging.getLogger(__name__)


class HeavyOilUpgrading(Process):
    """
    Synthetic crude oil (SCO) upgrading of heavy oil / bitumen.

    Takes bitumen (``oil for upgrading``) and produces SCO (``oil for storage``),
    exported process gas, flared gas, and petrocoke. Energy use is split across
    natural gas, upgrader process gas, petcoke heat, and imported electricity.
    Electricity and hydrogen are exported via ``self.import_export``.

    The ``upgrader_type`` string selects a column in ``heavy_oil_upgrading_df``
    that drives all yield ratios. When ``upgrader_type == "None"``, the caller
    is expected to omit this process from the field; no internal gating remains.
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        NG_comp: pd.Series,
        upgrader_gas_comp: pd.Series,
        NG_heating_value: Quantity[float],
        petro_coke_heating_value: Quantity[float],
        mole_to_scf: Quantity[float],
        cogeneration_upgrading: Quantity[float],
        fraction_elec_onsite: Quantity[float],
        oil_sands_mine: str,
        upgrader_type: str,
        oil: Oil,
        water: Water,
        gas: Gas,
        heavy_oil_upgrading_df: pd.DataFrame,
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "oil for upgrading"
        ]

        self._required_outputs = [
            "oil for storage",
            "gas",
            "gas for flaring",
            "petrocoke",
        ]

        self.NG_comp = NG_comp
        self.upgrader_gas_comp = upgrader_gas_comp
        self.NG_heating_value = NG_heating_value
        self.petro_coke_heating_value = petro_coke_heating_value
        self.mole_to_scf = mole_to_scf
        self.cogeneration_upgrading = cogeneration_upgrading
        self.fraction_elec_onsite = fraction_elec_onsite
        self.oil_sands_mine = oil_sands_mine
        self.upgrader_type = upgrader_type
        self.oil = oil
        self.water = water
        self.gas = gas
        self.heavy_oil_upgrading_df = heavy_oil_upgrading_df

        self.water_density = water.density()

    def run(self):
        self.print_running_msg()

        # mass rate
        input_oil = self.find_input_streams("oil for upgrading", combine=True)

        if input_oil.is_uninitialized():
            return

        df = self.heavy_oil_upgrading_df
        totals = df.query("Fraction == 'total'")
        d = {}
        for i, row in totals.iterrows():
            item = row.Items
            fractions = df.query("Fraction != 'total' and Items == @item")[["Fraction", self.upgrader_type, "Unit"]]
            total = totals.query("Items==@item")[self.upgrader_type]
            frac_with_unit = pd.Series(fractions.set_index("Fraction")[self.upgrader_type], dtype="pint[frac]")
            d[item] = frac_with_unit * ureg.Quantity(total.values[0], row.Unit)

        heavy_oil_upgrading_table = df[self.upgrader_type]
        heavy_oil_upgrading_table.index = df["Items"]

        upgrader_process_gas_heating_value = (self.upgrader_gas_comp *
                                              self.oil.component_LHV_molar[self.upgrader_gas_comp.index] *
                                              self.mole_to_scf).sum()
        SCO_bitumen_ratio = heavy_oil_upgrading_table["SCO/bitumen ratio"]

        self.ctx.process_data["SCO_bitumen_ratio"] = SCO_bitumen_ratio  # used in the Flaring process

        SCO_API = heavy_oil_upgrading_table["API gravity of resulting upgraded product output"]
        SCO_specific_gravity = self.oil.specific_gravity(SCO_API)

        input_liquid_mass_rate = input_oil.liquid_flow_rate("oil")
        input_liquid_SG = self.oil.specific_gravity(input_oil.API)

        input_liquid_vol_rate = input_liquid_mass_rate / (input_liquid_SG * self.water_density)
        SCO_output = input_liquid_vol_rate * SCO_bitumen_ratio

        SCO_output_mass_rate = SCO_output * SCO_specific_gravity * self.water_density
        SCO_to_storage = self.find_output_stream("oil for storage")
        SCO_to_storage.set_liquid_flow_rate("oil", SCO_output_mass_rate, tp=self.ctx.stp)
        SCO_to_storage.set_API(SCO_API)

        # Process gas calculation
        proc_gas_dict = d["Process gas (PG) yield per bbl SCO output"] * SCO_output
        proc_gas_to_heat = proc_gas_dict["Fraction PG to self use - Heating (W/O cogen)"]
        proc_gas_to_H2 = proc_gas_dict["Fraction PG to self use - H2 gen"]
        proc_gas_exported = proc_gas_dict["Fraction PG exported"]
        proc_gas_flared = proc_gas_dict["Fraction PG flared"]

        def calculate_mass_rate_from_volume_rate(volume_rate, gas_comp):
            return gas_comp * self.oil.component_MW[gas_comp.index] * volume_rate * self.mole_to_scf

        proc_gas_exported_mass_rate = calculate_mass_rate_from_volume_rate(proc_gas_exported, self.upgrader_gas_comp)
        proc_gas_to_H2_mass_rate = calculate_mass_rate_from_volume_rate(proc_gas_to_H2, self.upgrader_gas_comp)
        output_proc_gas = self.find_output_stream("gas")
        output_proc_gas.set_rates_from_series(proc_gas_exported_mass_rate, PHASE_GAS)
        output_proc_gas.set_tp(STP)

        # Electricity calculation
        electricity_yield = ureg.Quantity(heavy_oil_upgrading_table["Electricity intensity"], "kWh/bbl_oil")
        frac_electricity_self_gene = self.fraction_elec_onsite * self.cogeneration_upgrading
        elect_cogen = SCO_output * frac_electricity_self_gene * electricity_yield
        elect_import = SCO_output * electricity_yield * (1 - frac_electricity_self_gene)

        # NG calculation
        NG_dict = d["Natural gas intensity (W/O cogen)"] * SCO_output
        NG_to_cogen_yield = \
            frac_electricity_self_gene * electricity_yield / heavy_oil_upgrading_table[
                "Cogen turbine efficiency"] / self.NG_heating_value
        NG_to_H2 = NG_dict["Fraction NG - H2"]
        NG_to_H2_mass_rate = calculate_mass_rate_from_volume_rate(NG_to_H2, self.NG_comp)
        NG_to_cogen = NG_to_cogen_yield * SCO_output
        heat_from_cogen = \
            NG_to_cogen * self.NG_heating_value * heavy_oil_upgrading_table["Cogeneration steam efficiency"]
        NG_to_heat = max(
            NG_dict["Fraction NG - Heating (W/O cogen)"] - heat_from_cogen / upgrader_process_gas_heating_value, 0)

        proc_gas_flaring_mass_rate = calculate_mass_rate_from_volume_rate(proc_gas_flared, self.upgrader_gas_comp)
        flaring_gas = self.find_output_stream("gas for flaring")
        flaring_gas.set_rates_from_series(proc_gas_flaring_mass_rate, PHASE_GAS)
        flaring_gas.set_tp(STP)

        # Petrocoke calculation
        coke_dict = d["Coke yield per bbl SCO output"] * SCO_output
        coke_to_stockpile_and_transport = \
            ureg.Quantity(max(0, (
                    input_liquid_mass_rate -
                    SCO_output_mass_rate -
                    proc_gas_exported_mass_rate.sum() -
                    proc_gas_flaring_mass_rate.sum()).to("tonne/day").m), "tonne/day")
        coke_to_heat = \
            ureg.Quantity(max(0, (coke_dict.sum() - coke_to_stockpile_and_transport).to("tonne/day").m), "tonne/day")

        coke_to_transport = self.find_output_stream("petrocoke")
        coke_to_transport.set_solid_flow_rate("PC", coke_to_stockpile_and_transport)
        coke_to_transport.set_tp(STP)

        self.set_iteration_value(SCO_to_storage.total_flow_rate() +
                                 coke_to_transport.total_flow_rate() +
                                 flaring_gas.total_flow_rate() +
                                 output_proc_gas.total_flow_rate())

        # energy use
        energy_use = self.energy

        NG_stream = Stream("NG_stream", tp=STP)
        upgrader_gas_stream = Stream("upgrader_gas_stream", tp=STP)
        NG_mass_rate = calculate_mass_rate_from_volume_rate(NG_to_cogen + NG_to_heat + NG_to_H2, self.NG_comp)
        upgrader_mass_rate = \
            calculate_mass_rate_from_volume_rate(proc_gas_to_heat + proc_gas_to_H2 + proc_gas_flared,
                                                 self.upgrader_gas_comp)
        NG_stream.set_rates_from_series(NG_mass_rate, PHASE_GAS)
        upgrader_gas_stream.set_rates_from_series(upgrader_mass_rate, PHASE_GAS)

        NG_consumption = self.gas.energy_flow_rate(NG_stream)
        upgrader_process_gas_consumption = self.gas.energy_flow_rate(upgrader_gas_stream)
        petro_coke_consumption = coke_to_heat * self.petro_coke_heating_value

        energy_use.set_rate(EN_NATURAL_GAS, NG_consumption.to("mmBtu/day"))
        energy_use.set_rate(EN_UPG_PROC_GAS, upgrader_process_gas_consumption.to("mmBtu/day"))
        energy_use.set_rate(EN_PETCOKE, petro_coke_consumption.to("mmBtu/day"))
        energy_use.set_rate(EN_ELECTRICITY, elect_import.to("mmBtu/day"))

        # import/export
        self.set_import_from_energy(energy_use)
        self.import_export.set_export(self.name, ELECTRICITY, elect_cogen)
        self.import_export.set_export(self.name, H2, proc_gas_to_H2_mass_rate.sum() + NG_to_H2_mass_rate.sum())

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_series(EM_FLARING, proc_gas_flaring_mass_rate.pint.to("tonne/day"))
