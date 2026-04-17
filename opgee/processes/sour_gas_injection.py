#
# SourGasInjection class
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

_logger = logging.getLogger(__name__)


class SourGasInjection(Process):
    loss_rate: "Quantity[float]"

    def __init__(self, name: str, ctx: FieldContext, loss_rate: "Quantity[float]"):
        super().__init__(name, ctx)
        self.loss_rate = loss_rate

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas",
        ]

        self._required_outputs = [
            "gas for gas partition",
        ]

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("gas")
        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        gas_to_partition = self.find_output_stream("gas for gas partition")
        gas_to_partition.copy_flow_rates_from(input)
        gas_to_partition.subtract_rates_from(gas_fugitives)

        self.set_iteration_value(gas_to_partition.total_flow_rate())

        self.ctx.process_data["is_input_from_well"] = True

        # emissions
        emissions = self.emissions
        emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
