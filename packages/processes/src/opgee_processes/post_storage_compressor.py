#
# PostStorageCompressor class
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
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class PostStorageCompressor(Process):
    """
    Storage compressor calculate emission from compressing produced gas for long-term (i.e., seasonal) storage.
    """

    discharge_press: Quantity[float]
    eta_compressor: Quantity[float]

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        discharge_press: Quantity[float],
        eta_compressor: Quantity[float],
        prime_mover_type: str,
        loss_rate: Quantity[float],
        gas: Gas,
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "gas",
        ]

        # TODO: avoid process names in contents.
        self._required_outputs = [
            "gas for distribution",
        ]

        self.discharge_press = discharge_press
        self.eta_compressor = eta_compressor
        self.prime_mover_type = prime_mover_type
        self.loss_rate = loss_rate
        self.gas = gas

    def run(self):
        self.print_running_msg()

        input = self.find_input_stream("gas")

        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        overall_compression_ratio = self.discharge_press / input.tp.P
        energy_consumption, output_temp, output_press = \
            Compressor.get_compressor_energy_consumption(
                self.gas,
                self.prime_mover_type,
                self.eta_compressor,
                overall_compression_ratio,
                input)

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        gas_to_distribution = self.find_output_stream("gas for distribution")
        gas_to_distribution.copy_gas_rates_from(input)
        gas_to_distribution.tp.set(T=output_temp, P=self.discharge_press)
        gas_to_distribution.subtract_rates_from(gas_fugitives)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
