#
# CrudeOilTransport class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from ..context import FieldContext
from ..import_export import CRUDE_OIL
from ..process import Process
from ..thermodynamics import Oil
from .shared import get_energy_carrier
from .transport_energy import TransportEnergy

_logger = logging.getLogger(__name__)


class CrudeOilTransport(Process):
    """
    Crude oil transport calculate emissions from crude oil to the market
    """

    transport_energy: TransportEnergy

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        transport_energy: TransportEnergy,
        transport_share_fuel,
        transport_parameter,
        transport_by_mode,
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

        oil_mass_rate = input_oil.liquid_flow_rate("oil")
        oil_LHV_rate = oil_mass_rate * oil_mass_energy_density

        # Denominator: crude LHV per unit mass (stored earlier in this run or by a prior process)
        denominator = self.ctx.process_data["crude_LHV"]

        fuel_consumption = self.transport_energy.get_transport_energy_dict(
            self.transport_parameter,
            self.transport_share_fuel,
            self.transport_by_mode,
            oil_LHV_rate,
            "Crude",
            denominator,
        )

        for name, value in fuel_consumption.items():
            self.energy.set_rate(get_energy_carrier(name), value.to("mmBtu/day"))

        self.set_import_from_energy(self.energy)
        self.import_export.set_export(self.name, CRUDE_OIL, oil_LHV_rate)
        self.set_combustion_emissions()
