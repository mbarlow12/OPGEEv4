#
# CrudeOilTransport class
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
from ..thermodynamics import Oil

_logger = logging.getLogger(__name__)


class CrudeOilTransport(Process):
    """
    Crude oil transport calculate emissions from crude oil to the market
    """

    transport_energy: Any
    transport_share_fuel: Any
    transport_parameter: Any
    transport_by_mode: Any

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        transport_energy: Any,
        transport_share_fuel: Any,
        transport_parameter: Any,
        transport_by_mode: Any,
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "oil"
        ]

        self._required_outputs = [
            "oil"
        ]

        self.oil = oil
        self.transport_energy = transport_energy
        self.transport_share_fuel = transport_share_fuel
        self.transport_parameter = transport_parameter
        self.transport_by_mode = transport_by_mode

    def run(self):
        self.print_running_msg()

        input_oil = self.find_input_stream("oil")

        if input_oil.is_uninitialized():
            return

        oil_mass_energy_density = self.oil.mass_energy_density()

        if self.ctx.process_data.get("crude_LHV") is None:
            self.ctx.process_data["crude_LHV"] = oil_mass_energy_density

        output = self.find_output_stream("oil")
        output.copy_flow_rates_from(input_oil)

        # TODO(phase 5 batch C): TransportEnergy still uses legacy API expecting `field`.
        # Wire properly when transport_energy.py is migrated. The pre-refactor flow was:
        # oil_LHV_rate = input_oil.liquid_flow_rate("oil") * oil_mass_energy_density
        # fuel_consumption = field.transport_energy.get_transport_energy_dict(
        #     self.field, self.transport_parameter, self.transport_share_fuel,
        #     self.transport_by_mode, oil_LHV_rate, "Crude")
        # then: for name, value in fuel_consumption.items():
        #     energy_use.set_rate(get_energy_carrier(name), value.to("mmBtu/day"))
        # then: self.set_import_from_energy(energy_use)
        #       self.import_export.set_export(self.name, CRUDE_OIL, oil_LHV_rate)
        #       self.set_combustion_emissions()
        raise NotImplementedError(
            "CrudeOilTransport.run: blocked on TransportEnergy migration (Tier 2 Batch C)"
        )
