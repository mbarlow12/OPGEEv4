#
# StorageSeparator class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import TemperaturePressure
from ..process import Process
from ..stream import Stream

_logger = logging.getLogger(__name__)


class StorageSeparator(Process):
    """
    Storage well calculate fugitive emission from storage wells.
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        water_production_frac: Quantity[float],
        outlet_temp: Quantity[float],
        outlet_press: Quantity[float],
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "gas",
        ]

        self._required_outputs = [
            "gas",
        ]

        self.water_production_frac = water_production_frac
        self.outlet_tp = TemperaturePressure(outlet_temp, outlet_press)

    def run(self):
        self.print_running_msg()

        input = self.find_input_stream("gas")

        if input.is_uninitialized():
            return

        # produced water stream
        prod_water = Stream("produced water stream", self.outlet_tp)
        prod_water.set_liquid_flow_rate("H2O", (input.total_gas_rate() * self.water_production_frac).m)

        gas_to_compressor = self.find_output_stream("gas")
        gas_to_compressor.copy_gas_rates_from(input, tp=self.outlet_tp)

        #TODO: Future versions of OPGEE may treat this process in more detail.
