#
# LNGRegasification class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..process import Process
from ..thermodynamics import Gas
from .shared import get_energy_carrier, get_energy_consumption

_logger = logging.getLogger(__name__)


class LNGRegasification(Process):
    """
    LNG liquefaction calculate emission of transported gas to regasification
    """

    efficiency: Quantity
    energy_intensity_regas: Quantity
    prime_mover_type: str

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        efficiency: Quantity,
        energy_intensity_regas: Quantity,
        prime_mover_type: str,
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "gas",
        ]

        # TODO: avoid process names in contents.
        self._required_outputs = [
            "gas for distribution",
        ]

        self.gas = gas
        self.efficiency = efficiency
        self.energy_intensity_regas = energy_intensity_regas
        self.prime_mover_type = prime_mover_type

    def run(self):
        self.print_running_msg()

        input = self.find_input_stream("gas")

        if input.is_uninitialized():
            return

        gas_mass_rate = input.total_gas_rate()
        gas_mass_energy_density = self.gas.mass_energy_density(input)
        gas_LHV_rate = gas_mass_rate * gas_mass_energy_density
        total_regasification_requirement = self.energy_intensity_regas * gas_LHV_rate

        energy_consumption = get_energy_consumption(self.prime_mover_type, total_regasification_requirement)
        gas_to_distribution = self.find_output_stream("gas for distribution")
        gas_to_distribution.copy_flow_rates_from(input)

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
