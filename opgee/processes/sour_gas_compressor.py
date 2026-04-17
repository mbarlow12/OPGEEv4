#
# SourGasCompressor class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..emissions import EM_FUGITIVES
from ..process import Process
from ..processes.compressor import Compressor
from ..thermodynamics import Gas
from ..units import ureg
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class SourGasCompressor(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        res_press: Quantity[float],
        eta_compressor: Quantity[float],
        prime_mover_type: str,
        loss_rate: Quantity[float],
        gas: Gas,
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for sour gas compressor",
        ]

        self._required_outputs = [
            "gas",
        ]

        self.res_press = res_press
        self.eta_compressor = eta_compressor
        self.prime_mover_type = prime_mover_type
        self.loss_rate = loss_rate
        self.gas = gas

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("gas for sour gas compressor")
        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        gas_to_injection = self.find_output_stream("gas")
        gas_to_injection.copy_flow_rates_from(input)
        gas_to_injection.subtract_rates_from(gas_fugitives)

        discharge_press = self.res_press + ureg.Quantity(500.0, "psia")
        overall_compression_ratio = discharge_press / input.tp.P
        energy_consumption, output_temp, _ = \
            Compressor.get_compressor_energy_consumption(
                self.gas,
                self.prime_mover_type,
                self.eta_compressor,
                overall_compression_ratio,
                input)

        gas_to_injection.tp.set(T=output_temp, P=discharge_press)
        self.ctx.process_data["sour_gas_reinjection_mass_rate"] = gas_to_injection.gas_flow_rate("CO2")

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
