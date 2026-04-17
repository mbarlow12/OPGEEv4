#
# Flaring class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from ..context import FieldContext
from ..emissions import EM_FLARING
from ..process import Process
from ..stream import Stream

_logger = logging.getLogger(__name__)

class Flaring(Process):

    def __init__(self, name: str, ctx: FieldContext):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for flaring",
            "methane slip"
        ]

        self._required_outputs = []

    def run(self):
        self.print_running_msg()

        # mass rate
        gas_to_flare = self.find_input_streams("gas for flaring", combine=True)  # type: Stream
        methane_slip = self.find_input_stream("methane slip")  # type: Stream
        if gas_to_flare.is_uninitialized() or methane_slip.is_uninitialized():
            return

        # emissions
        emissions = self.emissions
        sum_streams = Stream("combusted_stream", tp=gas_to_flare.tp)
        sum_streams.add_combustion_CO2_from(gas_to_flare)
        sum_streams.add_flow_rates_from(methane_slip)
        emissions.set_from_stream(EM_FLARING, sum_streams)
