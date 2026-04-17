#
# GasLiftingCompressor class
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


class GasLiftingCompressor(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        loss_rate: Quantity[float],
        res_press: Quantity[float],
        prime_mover_type: str,
        eta_compressor: Quantity[float],
    ):
        super().__init__(name, ctx)

        self.gas = gas
        self.loss_rate = loss_rate
        self.res_press = res_press
        self.prime_mover_type = prime_mover_type
        self.eta_compressor = eta_compressor

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "lifting gas"
        ]

        self._required_outputs = [
            "lifting gas"
        ]

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("lifting gas", raiseError=None)

        if input is None or input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        lifting_gas = self.find_output_stream("lifting gas")
        lifting_gas.copy_flow_rates_from(input)
        lifting_gas.subtract_rates_from(gas_fugitives)

        input_tp = input.tp
        discharge_press = (self.res_press + input_tp.P) / 2 + ureg.Quantity(100.0, "psia")
        overall_compression_ratio = discharge_press / input_tp.P
        energy_consumption, output_temp, _ = \
            Compressor.get_compressor_energy_consumption(self.gas,
                                                         self.prime_mover_type,
                                                         self.eta_compressor,
                                                         overall_compression_ratio,
                                                         input)

        lifting_gas.tp.set(T=output_temp, P=discharge_press)

        self.set_iteration_value(lifting_gas.total_flow_rate())

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
