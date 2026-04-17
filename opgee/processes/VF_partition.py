#
# GasPartition class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import STP
from ..process import Process
from ..stream import PHASE_GAS, Stream
from ..thermodynamics import Gas

_logger = logging.getLogger(__name__)


class VFPartition(Process):
    """
    VF (Venting and Flaring) partition is to check the reasonable amount of gas goes to venting, flaring and further process
    """
    def __init__(self, name: str, ctx: FieldContext, gas: Gas, FOR: Quantity[float], oil_volume_rate: Quantity[float], combusted_gas_frac: Quantity[float]):
        super().__init__(name, ctx)

        self.gas = gas
        self.FOR = FOR
        self.oil_volume_rate = oil_volume_rate
        self.combusted_gas_frac = combusted_gas_frac

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for partition",
        ]

        self._required_outputs = [
            "gas for flaring",
            "methane slip",
            "gas for venting",
        ]

    def run(self):
        self.print_running_msg()

        if not self.all_streams_ready("gas for partition"):
            return

        input = self.find_input_streams("gas for partition", combine=True)
        if input.is_uninitialized():
            return

        input_stream_mol_fracs = self.gas.component_molar_fractions(input)
        SCO_bitumen_ratio = self.ctx.process_data.get("SCO_bitumen_ratio")
        temp = self.oil_volume_rate * self.FOR
        if SCO_bitumen_ratio:
            volume_of_gas_flared = temp / SCO_bitumen_ratio
        else:
            volume_of_gas_flared = temp

        temp = volume_of_gas_flared * input_stream_mol_fracs
        volume_rate_gas_combusted = temp * self.combusted_gas_frac
        volume_rate_gas_slip = temp * (1 - self.combusted_gas_frac)

        temp = self.gas.component_gas_rho_STP[volume_rate_gas_combusted.index]
        mass_rate_gas_combusted =\
            volume_rate_gas_combusted * temp
        mass_rate_gas_slip = volume_rate_gas_slip * temp

        gas_to_flare = self.find_output_stream("gas for flaring")
        gas_to_flare.set_rates_from_series(mass_rate_gas_combusted, PHASE_GAS, input)
        gas_to_flare.set_tp(tp=STP)

        methane_slip = self.find_output_stream("methane slip")
        temp = Stream("temp", tp=input.tp)
        temp.copy_flow_rates_from(input)
        methane_slip.set_rates_from_series(mass_rate_gas_slip, PHASE_GAS, temp.subtract_rates_from(gas_to_flare, PHASE_GAS))
        methane_slip.set_tp(tp=STP)

        output_gas = self.find_output_stream("gas for venting")
        output_gas.copy_flow_rates_from(input)
        output_gas.subtract_rates_from(gas_to_flare)
        output_gas.subtract_rates_from(methane_slip)

        self.set_iteration_value(output_gas.total_flow_rate())
