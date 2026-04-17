#
# PetrocokeTransport class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..import_export import NGL_LPG
from ..process import Process
from .shared import get_energy_carrier
from .transport_energy import TransportEnergy

_logger = logging.getLogger(__name__)


class PetrocokeTransport(Process):
    """
    Petrocoke transport calculate emissions from petrocoke to the market
    """

    transport_energy: TransportEnergy
    petro_coke_heating_value: Quantity[float]

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        transport_energy: TransportEnergy,
        transport_share_fuel,
        transport_parameter,
        transport_by_mode,
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

        petrocoke_mass_rate = input_coke.solid_flow_rate("PC")
        petrocoke_LHV_rate = petrocoke_mass_rate * self.petro_coke_heating_value

        # Denominator: heating value per unit mass, converted to match transport_energy internals.
        # The original code divided by petrocoke-heating-value / 1.10231 (short-ton → tonne conversion).
        denominator = self.petro_coke_heating_value / 1.10231

        fuel_consumption = self.transport_energy.get_transport_energy_dict(
            self.transport_parameter,
            self.transport_share_fuel,
            self.transport_by_mode,
            petrocoke_LHV_rate,
            "Petrocoke",
            denominator,
        )

        for name, value in fuel_consumption.items():
            self.energy.set_rate(get_energy_carrier(name), value.to("mmBtu/day"))

        self.set_import_from_energy(self.energy)
        self.import_export.set_export(self.name, NGL_LPG, petrocoke_LHV_rate)
        self.set_combustion_emissions()
