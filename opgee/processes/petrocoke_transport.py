#
# PetrocokeTransport class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging
from typing import Any

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..process import Process

_logger = logging.getLogger(__name__)


class PetrocokeTransport(Process):
    """
    Petrocoke transport calculate emissions from petrocoke to the market
    """

    transport_energy: Any
    transport_share_fuel: Any
    transport_parameter: Any
    transport_by_mode: Any
    petro_coke_heating_value: Quantity[float]

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        transport_energy: Any,
        transport_share_fuel: Any,
        transport_parameter: Any,
        transport_by_mode: Any,
        petro_coke_heating_value: Quantity[float],
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "petrocoke"
        ]

        # TODO: avoid process names in contents.
        self._required_outputs = [
            "petrocoke",
        ]

        self.transport_energy = transport_energy
        self.transport_share_fuel = transport_share_fuel
        self.transport_parameter = transport_parameter
        self.transport_by_mode = transport_by_mode
        self.petro_coke_heating_value = petro_coke_heating_value

    def run(self):
        self.print_running_msg()

        input_coke = self.find_input_stream("petrocoke")

        if input_coke.is_uninitialized():
            return

        petrocoke_to_market = self.find_output_stream("petrocoke")
        petrocoke_to_market.copy_flow_rates_from(input_coke)

        # TODO(phase 5 tier 2): TransportEnergy still uses legacy API expecting `field`.
        # Wire properly when transport_energy.py is migrated.
        raise NotImplementedError("PetrocokeTransport.run: blocked on TransportEnergy migration (Tier 2)")
