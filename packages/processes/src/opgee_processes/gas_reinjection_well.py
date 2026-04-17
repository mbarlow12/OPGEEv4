#
# GasReinjectionWell class
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


class GasReinjectionWell(Process):
    gas_flooding: bool
    natural_gas_reinjection: bool
    loss_rate: Quantity

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas_flooding: bool,
        natural_gas_reinjection: bool,
        loss_rate: Quantity,
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas"
        ]

        self._required_outputs = [
            "gas",
        ]

        self.gas_flooding = gas_flooding
        self.natural_gas_reinjection = natural_gas_reinjection
        self.loss_rate = loss_rate

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("gas")

        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        gas_to_reservoir = self.find_output_stream("gas")
        gas_to_reservoir.copy_flow_rates_from(input)
        gas_to_reservoir.subtract_rates_from(gas_fugitives)

        self.set_iteration_value(gas_to_reservoir.total_flow_rate())

        # emissions
        emissions = self.emissions
        emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
