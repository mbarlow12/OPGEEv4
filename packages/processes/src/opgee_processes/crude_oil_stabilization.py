#
# CrudeOilStabilization class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import TemperaturePressure
from ..emissions import EM_FUGITIVES
from ..process import Process
from ..stream import Stream, PHASE_LIQUID, PHASE_GAS
from ..thermodynamics import Gas, Oil
from .compressor import Compressor
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class CrudeOilStabilization(Process):
    """
    CrudeOilStabilization is a subclass of the Process class that represents a crude oil stabilization process in an oil and gas production system.
    This class handles the stabilization of oil by removing gas, managing energy use, and calculating emissions associated
    with the stabilization process.

    Attributes:
        stab_tp (TemperaturePressure): The temperature and pressure of the stabilizer column.
        mol_per_scf (Quantity[float]): The number of moles per standard cubic feet.
        stab_gas_press (Quantity[float]): The pressure of the stabilized gas.
        eps_stab (Quantity[float]): Stabilization heat duty multiplier.
        eta_gas (Quantity[float]): Efficiency of natural gas engine.
        eta_electricity (Quantity[float]): Efficiency of electricity.
        prime_mover_type (str): Type of prime mover used for energy consumption.
        eta_compressor (Quantity[float]): Efficiency of the compressor.
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        gas: Gas,
        stabilizer_column_temp: Quantity[float],
        stabilizer_column_press: Quantity[float],
        mol_per_scf: Quantity[float],
        stab_gas_press: Quantity[float],
        eps_stab: Quantity[float],
        eta_gas: Quantity[float],
        eta_electricity: Quantity[float],
        prime_mover_type: str,
        eta_compressor: Quantity[float],
        loss_rate: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "oil for stabilization",
        ]

        self._required_outputs = [
            "gas",
            "oil for storage",
        ]

        self.oil = oil
        self.gas = gas
        self.stab_tp = TemperaturePressure(stabilizer_column_temp, stabilizer_column_press)
        self.mol_per_scf = mol_per_scf
        self.stab_gas_press = stab_gas_press
        self.eps_stab = eps_stab
        self.eta_gas = eta_gas
        self.eta_electricity = eta_electricity
        self.prime_mover_type = prime_mover_type
        self.eta_compressor = eta_compressor
        self.loss_rate = loss_rate

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("oil for stabilization")
        if input.is_uninitialized():
            return

        input_T, input_P = input.tp.get()
        average_temp = (self.stab_tp.T.to("kelvin") + input_T.to("kelvin")) / 2
        oil = self.oil
        oil_specific_heat = oil.specific_heat(input.API, average_temp)
        stream = Stream("out_stream", self.stab_tp)
        oil_SG = oil.specific_gravity(input.API)
        solution_GOR_inlet = oil.solution_gas_oil_ratio(input,
                                                        oil_SG,
                                                        oil.gas_specific_gravity,
                                                        oil.gas_oil_ratio)
        solution_GOR_outlet = oil.solution_gas_oil_ratio(stream,
                                                         oil_SG,
                                                         oil.gas_specific_gravity,
                                                         oil.gas_oil_ratio)
        oil_mass_rate = input.flow_rate("oil", PHASE_LIQUID)
        oil_density = oil.density(input,
                                  oil_SG,
                                  oil.gas_specific_gravity,
                                  oil.gas_oil_ratio)
        gas_removed_by_stabilizer = oil_mass_rate * (solution_GOR_inlet - solution_GOR_outlet) / oil_density
        gas_removed_molar_rate = gas_removed_by_stabilizer * self.mol_per_scf * oil.gas_comp  # Pandas Series
        gas_removed_mass_rate = oil.component_MW[gas_removed_molar_rate.index] * gas_removed_molar_rate

        output_stab_gas = self.find_output_stream("gas")
        gas_tp_after_separation = self.ctx.process_data.get("gas_tp_after_separation")
        if gas_tp_after_separation is None:
            gas_tp_after_separation = input.tp
        output_stab_gas.set_tp(gas_tp_after_separation)
        output_stab_gas.set_rates_from_series(gas_removed_mass_rate, PHASE_GAS)

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        output_oil = self.find_output_stream("oil for storage")
        oil_for_storage = oil_mass_rate - output_stab_gas.total_gas_rate() - gas_fugitives.total_gas_rate()
        output_oil.set_liquid_flow_rate("oil", oil_for_storage, tp=self.stab_tp)
        output_oil.set_API(input.API)

        self.set_iteration_value(output_stab_gas.total_flow_rate() + output_oil.total_flow_rate())

        # energy use
        heat_duty = oil_mass_rate * oil_specific_heat * (self.stab_tp.T - input_T) * (1 + self.eps_stab)
        energy_use = self.energy

        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_consumption = heat_duty / self.eta_gas if self.prime_mover_type == "NG_engine" else heat_duty / self.eta_electricity

        # boosting compressor for stabilizer
        overall_compression_ratio = self.stab_gas_press / input.tp.P
        compressor_energy, _, _ = Compressor.get_compressor_energy_consumption(self.gas,
                                                                               self.prime_mover_type,
                                                                               self.eta_compressor,
                                                                               overall_compression_ratio,
                                                                               output_stab_gas,
                                                                               inlet_tp=input.tp)

        energy_consumption += compressor_energy
        energy_use.set_rate(energy_carrier, energy_consumption.to("mmBtu/day"))

        # import and export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
