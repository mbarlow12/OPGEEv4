#
# PreMembraneChiller class
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
from ..energy import EN_ELECTRICITY
from ..process import Process
from ..units import ureg

_logger = logging.getLogger(__name__)


class PreMembraneChiller(Process):
    outlet_temp: "Quantity[float]"
    loss_rate: "Quantity[float]"

    def __init__(self, name: str, ctx: FieldContext, outlet_temp: "Quantity[float]", loss_rate: "Quantity[float]"):
        super().__init__(name, ctx)

        self.outlet_temp = outlet_temp
        self.loss_rate = loss_rate

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for chiller",
        ]

        self._required_outputs = [
            "gas",
        ]

        self.compressor_load = ureg.Quantity(3.44, "kW")
        self.feed_stream_mass_rate = ureg.Quantity(6.111072, "tonne/day")
        self.pressure_drop = ureg.Quantity(56.0, "delta_degC")

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("gas for chiller")
        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        gas_to_compressor = self.find_output_stream("gas")
        gas_to_compressor.copy_flow_rates_from(input)
        gas_to_compressor.subtract_rates_from(gas_fugitives)
        gas_to_compressor.tp.set(T=self.outlet_temp, P=input.tp.P)
        self.set_iteration_value(gas_to_compressor.total_flow_rate())

        delta_temp = input.tp.T - self.outlet_temp
        energy_consumption = (self.compressor_load * input.total_gas_rate() /
                              self.feed_stream_mass_rate * delta_temp / self.pressure_drop)

        # energy-use
        energy_use = self.energy
        energy_use.set_rate(EN_ELECTRICITY, energy_consumption)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        emissions = self.emissions
        emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
