#
# CO2InjectionWell class
#
# Author: Richard Plevin and Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import std_pressure
from ..process import Process
from ..processes.compressor import Compressor
from ..stream import PHASE_GAS
from ..thermodynamics import Gas
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class CO2Membrane(Process):
    """
    This process represents the separation of CO2 from natural gas using a membrane.

    input streams:
        - gas

    output streams:
        - gas for AGR
        - gas for CO2 compressor

    """

    membrane_comp: pd.Series
    press_drop: Quantity[float]
    eta_compressor: Quantity[float]
    prime_mover_type: str
    AGR_feedin_press: Quantity[float]

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        membrane_comp: pd.Series,
        press_drop: Quantity[float],
        eta_compressor: Quantity[float],
        prime_mover_type: str,
        AGR_feedin_press: Quantity[float],
    ):
        super().__init__(name, ctx)

        self.gas = gas
        self.membrane_comp = membrane_comp
        self.press_drop = press_drop
        self.eta_compressor = eta_compressor
        self.prime_mover_type = prime_mover_type
        self.AGR_feedin_press = AGR_feedin_press

        self._required_inputs = [
            "gas",
        ]

        # TODO: avoid process names in contents.
        self._required_outputs = [
            "gas for AGR",
            "gas for CO2 compressor",
        ]

    def run(self):
        self.print_running_msg()

        input = self.find_input_stream("gas")
        if input.is_uninitialized():
            return

        gas_to_AGR = self.find_output_stream("gas for AGR")
        AGR_mol_fracs = 1 - self.membrane_comp
        gas_to_AGR.copy_flow_rates_from(input)
        gas_to_AGR.tp.P = self.AGR_feedin_press
        gas_to_AGR.tp.T = self.ctx.stp.T
        gas_to_AGR.multiply_factor_from_series(AGR_mol_fracs, PHASE_GAS)

        gas_to_compressor = self.find_output_stream("gas for CO2 compressor")
        gas_to_compressor.copy_flow_rates_from(input)
        gas_to_compressor.tp.set(T=self.ctx.stp.T, P=input.tp.P * 0.33)
        gas_to_compressor.multiply_factor_from_series(self.membrane_comp, PHASE_GAS)

        inlet_pressure_after_membrane = max(std_pressure, input.tp.P - self.press_drop)
        discharge_press = input.tp.P
        overall_compression_ratio = discharge_press / inlet_pressure_after_membrane
        energy_consumption, temp, _ = Compressor.get_compressor_energy_consumption(
            self.gas,
            self.prime_mover_type,
            self.eta_compressor,
            overall_compression_ratio,
            input,
        )
        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        # import and export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
