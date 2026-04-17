#
# GasDistribution class
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
from ..import_export import NATURAL_GAS
from ..process import Process
from ..thermodynamics import Gas

_logger = logging.getLogger(__name__)


class GasDistribution(Process):
    """
    Gas distribution calculates emission of gas to distribution
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        frac_loss_distribution: Quantity[float],
        frac_loss_meter: Quantity[float],
        frac_loss_enduse: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for distribution"
        ]

        self._required_outputs = [
            "gas",
        ]

        self.gas = gas
        self.frac_loss = frac_loss_distribution + frac_loss_meter + frac_loss_enduse

    def run(self):
        self.print_running_msg()

        input = self.find_input_streams("gas for distribution", combine=True)

        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.frac_loss.m)

        gas_to_customer = self.find_output_stream("gas")
        gas_to_customer.copy_flow_rates_from(input)
        gas_to_customer.subtract_rates_from(gas_fugitives)

        gas_mass_rate = gas_to_customer.total_gas_rate()
        gas_mass_energy_density = self.gas.mass_energy_density(gas_to_customer)
        gas_LHV_rate = gas_mass_rate * gas_mass_energy_density
        self.import_export.set_export(self.name, NATURAL_GAS, gas_LHV_rate)

        # emissions
        emissions = self.emissions
        emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
