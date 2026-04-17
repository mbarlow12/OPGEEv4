#
# Venting class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..emissions import EM_VENTING, EM_FUGITIVES
from ..process import Process
from ..stream import Stream
from ..thermodynamics import Gas
from ..units import ureg

_logger = logging.getLogger(__name__)


class Venting(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        imported_fuel_gas_comp: pd.Series,
        frac_venting: Quantity[float],
        pipe_leakage: Quantity[float],
        gas_lifting: bool,
        GOR: Quantity[float],
        FOR: Quantity[float],
        GLIR: Quantity[float],
        oil_volume_rate: Quantity[float],
        res_press: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for venting",
        ]

        self._required_outputs = [
            "gas",
        ]

        self.gas = gas
        self.imported_fuel_gas_comp = imported_fuel_gas_comp
        self.imported_fuel_gas_mass_fracs = gas.component_mass_fractions(imported_fuel_gas_comp)

        #TODO: give warning when frac_venting is not within [0, 1]
        self.frac_venting = min(ureg.Quantity(1., "frac"),
                                max(frac_venting, ureg.Quantity(0., "frac")))

        self.pipe_leakage = pipe_leakage
        self.gas_lifting = gas_lifting
        self.GOR = GOR
        self.FOR = FOR
        self.GLIR = GLIR
        self.oil_volume_rate = oil_volume_rate
        self.res_press = res_press

        self.is_first_loop = True

    def run(self):
        self.print_running_msg()
        # mass rate

        # # TODO: fix this after data pipeline is done
        # WOR = field.attr("WOR")
        # water_prod = self.oil_volume_rate * WOR

        input = self.find_input_stream("gas for venting")  # type: Stream
        if input.is_uninitialized():
            return

        methane_to_venting = input.gas_flow_rate("C1") * self.frac_venting
        venting_frac = \
            methane_to_venting / input.gas_flow_rate("C1") \
                if input.gas_flow_rate("C1").m != 0 else ureg.Quantity(0, "frac")
        fugitive_frac = \
            self.pipe_leakage / input.gas_flow_rate("C1") \
                if input.gas_flow_rate("C1").m != 0 else ureg.Quantity(0, "frac")

        gas_to_vent = Stream("venting_gas", tp=self.ctx.stp)
        gas_to_vent.copy_flow_rates_from(input, tp=self.ctx.stp)
        gas_to_vent.multiply_flow_rates(venting_frac.to("frac").m)

        if self.is_first_loop:
            self.ctx.process_data["gas_to_vent_init"] = gas_to_vent
            self.is_first_loop = False

        if self.gas_lifting and self.ctx.process_data.get("gas_to_vent_init"):
            gas_to_vent = self.ctx.process_data.get("gas_to_vent_init")

        gas_fugitives = self.set_gas_fugitives(input, fugitive_frac.to("frac").m)

        gas_to_gathering = self.find_output_stream("gas")
        gas_tp_after_separation = self.ctx.process_data.get("gas_tp_after_separation")
        gas_to_gathering.copy_flow_rates_from(input, tp=gas_tp_after_separation)
        gas_to_gathering.subtract_rates_from(gas_to_vent)
        gas_to_gathering.subtract_rates_from(gas_fugitives)

        self.set_iteration_value(gas_to_gathering.total_flow_rate())

        # emissions
        emissions = self.emissions
        emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
        emissions.set_from_stream(EM_VENTING, gas_to_vent)
