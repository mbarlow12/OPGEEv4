#
# LNGTransport class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from ..context import FieldContext
from ..import_export import NGL_LPG
from ..process import Process
from ..thermodynamics import Gas
from .shared import get_energy_carrier
from .transport_energy import TransportEnergy

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
        transport_energy: TransportEnergy,
        transport_share_fuel,
        transport_parameter,
        transport_by_mode,
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

        gas_mass_rate = input.total_gas_rate()
        gas_mass_energy_density = self.gas.mass_energy_density(input)
        gas_LHV_rate = gas_mass_rate * gas_mass_energy_density

        # LNG denominator: LHV per unit mass for C1 (methane), the dominant LNG component
        denominator = self.gas.component_LHV_mass["C1"]

        fuel_consumption = self.transport_energy.get_transport_energy_dict(
            self.transport_parameter,
            self.transport_share_fuel,
            self.transport_by_mode,
            gas_LHV_rate,
            "LNG",
            denominator,
        )

        for name, value in fuel_consumption.items():
            self.energy.set_rate(get_energy_carrier(name), value.to("mmBtu/day"))

        self.set_import_from_energy(self.energy)
        self.import_export.set_export(self.name, NGL_LPG, gas_LHV_rate)
        self.set_combustion_emissions()
