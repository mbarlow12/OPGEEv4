#
# LNGTransport class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging
from typing import Any

from ..context import FieldContext
from ..process import Process
from ..thermodynamics import Gas

_logger = logging.getLogger(__name__)


class LNGTransport(Process):
    """
    LNG transport calculate emissions from LNG to the market
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        transport_energy: Any,
        transport_share_fuel: Any,
        transport_parameter: Any,
        transport_by_mode: Any,
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "gas",
        ]

        self._required_outputs = [
            "gas",
        ]

        self.gas = gas
        self.transport_energy = transport_energy
        self.transport_share_fuel = transport_share_fuel
        self.transport_parameter = transport_parameter
        self.transport_by_mode = transport_by_mode

    def run(self):
        self.print_running_msg()

        input = self.find_input_stream("gas")

        if input.is_uninitialized():
            return

        output = self.find_output_stream("gas")
        output.copy_flow_rates_from(input)

        # TODO(phase 5 tier 2): TransportEnergy still uses legacy API expecting `field`.
        # Wire properly when transport_energy.py is migrated. The pre-refactor flow
        # was: gas_LHV_rate = input.total_gas_rate() * self.gas.mass_energy_density(input);
        # then transport_energy.get_transport_energy_dict(..., gas_LHV_rate, "LNG"); then
        # set_import_from_energy + set_export(NGL_LPG, gas_LHV_rate) + set_combustion_emissions.
        raise NotImplementedError("LNGTransport.run: blocked on TransportEnergy migration (Tier 2)")
