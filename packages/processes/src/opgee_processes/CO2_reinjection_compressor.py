#
# CO2ReinjectionCompressor class
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
from ..process import Process
from ..processes.compressor import Compressor
from ..thermodynamics import Gas
from ..units import ureg
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class CO2ReinjectionCompressor(Process):
    """
        A process that compresses CO2 gas for reinjection into the reservoir.

        Inputs:
        - gas for CO2 compressor: The inlet stream of CO2 gas to the compressor.

        Outputs:
        - gas: The outlet stream of CO2 gas that is reinjected into the reservoir.

        Attributes:
        - res_press: The reservoir pressure in psia.
        - eta_compressor: The compressor efficiency.
        - prime_mover_type: The type of prime mover used to power the compressor.

    """

    res_press: Quantity[float]
    eta_compressor: Quantity[float]
    prime_mover_type: str
    loss_rate: Quantity[float]

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        res_press: Quantity[float],
        eta_compressor: Quantity[float],
        prime_mover_type: str,
        loss_rate: Quantity[float],
    ):
        super().__init__(name, ctx)

        self.gas = gas
        self.res_press = res_press
        self.eta_compressor = eta_compressor
        self.prime_mover_type = prime_mover_type
        self.loss_rate = loss_rate

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for CO2 compressor",   # might be multiple
        ]

        self._required_outputs = [
            "gas",
        ]

    def run(self):
        self.print_running_msg()

        # Check if input stream is ready
        if not self.all_streams_ready("gas for CO2 compressor"):
            return

        # Get input stream and fugitive gas
        input = self.find_input_streams("gas for CO2 compressor", combine=True)
        if input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        # Calculate discharge pressure and iterate over input streams
        discharge_press = self.res_press + ureg.Quantity(500.0, "psia")
        total_energy_consumption = ureg.Quantity(0, "mmbtu/day")
        input_streams = self.find_input_streams("gas for CO2 compressor")
        for _, input_stream in input_streams.items():
            overall_compression_ratio = discharge_press / input_stream.tp.P
            energy_consumption, out_temp, _ = \
                Compressor.get_compressor_energy_consumption(self.gas,
                                                             self.prime_mover_type,
                                                             self.eta_compressor,
                                                             overall_compression_ratio,
                                                             input_stream)
            total_energy_consumption += energy_consumption

        # Set output stream and iteration value
        gas_to_well = self.find_output_stream("gas")
        gas_to_well.copy_flow_rates_from(input)
        gas_to_well.subtract_rates_from(gas_fugitives)
        gas_to_well.tp.set(T=out_temp, P=discharge_press)

        self.set_iteration_value(gas_to_well.total_flow_rate())

        self.ctx.process_data["CO2_reinjection_mass_rate"] = gas_to_well.gas_flow_rate("CO2")

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, total_energy_consumption)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
