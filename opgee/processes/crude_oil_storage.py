#
# CrudeOilStorage class
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
from ..emissions import EM_FUGITIVES
from ..process import Process
from ..stream import PHASE_GAS, Stream
from ..thermodynamics import Oil, Water
from ..units import ureg

_logger = logging.getLogger(__name__)


class CrudeOilStorage(Process):
    """
        A process that represents the storage of crude oil in a field.

        This process takes crude oil as an input and produces three output streams:
        - gas for partition: gas that is flared
        - gas for VRU: gas that is sent to a vapor recovery unit
        - oil: crude oil that is transported out of the storage facility

        The process calculates the mass rate of crude oil input, as well as the amount of gas that is exsolved upon flashing.
        It then calculates the rates of gas that are sent to the flare, vapor recovery unit, and fugitives, based on the
        exsolved gas and user-defined factors. Finally, it calculates the mass rate of crude oil that is transported out of
        the storage facility, and sets the output streams accordingly.

        This process does not use any energy, and only produces emissions from the gas fugitives stream.

        Attributes:
            oil: The ``Oil`` object representing the type of crude oil being stored.
            oil_sands_mine: A string representing the name of the oil sands mine, or "None" if there is no mine.
            storage_gas_comp: The composition of the storage gas (pre-sliced Series for "Storage Gas").
            CH4_comp: The methane component of the storage gas composition.
            f_FG_CS_VRU: The fraction of exsolved gas that is sent to the vapor recovery unit.
            f_FG_CS_FL: The fraction of exsolved gas that is flared.
            loss_rate: Fugitive loss rate in kg/bbl_oil (pre-computed by the caller).
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        water: Water,
        storage_gas_comp: pd.Series,
        oil_sands_mine: str,
        f_FG_CS_VRU: Quantity[float],
        f_FG_CS_FL: Quantity[float],
        loss_rate: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "oil for storage",
        ]

        self._required_outputs = [
            "gas for partition",
            "gas for VRU",
            "oil",
        ]

        self.oil = oil
        self.water = water
        self.storage_gas_comp = storage_gas_comp
        self.CH4_comp = storage_gas_comp["C1"]
        self.oil_sands_mine = oil_sands_mine
        self.f_FG_CS_VRU = f_FG_CS_VRU
        self.f_FG_CS_FL = f_FG_CS_FL
        self.loss_rate = loss_rate

    def run(self):
        self.print_running_msg()

        # TODO: LPG to blend with crude oil need to be implement after gas branch
        # mass rate
        input_stream = self.find_input_streams("oil for storage", combine=True)
        if input_stream.is_uninitialized():
            return

        oil_mass_rate = input_stream.liquid_flow_rate("oil")

        # Calculate gas exsolved upon flashing
        oil_volume_rate = oil_mass_rate / (self.oil.specific_gravity(input_stream.API) * self.water.density())
        gas_exsolved_upon_flashing = oil_volume_rate * self.loss_rate / self.CH4_comp \
            if self.oil_sands_mine == "None" else ureg.Quantity(0, "tonne/day")

        # Calculate vapor to flare, VRU, and gas fugitives
        temp = gas_exsolved_upon_flashing * self.storage_gas_comp
        vapor_to_flare = self.f_FG_CS_FL * temp
        vapor_to_VRU = self.f_FG_CS_VRU * temp
        gas_fugitives = (1 - self.f_FG_CS_VRU - self.f_FG_CS_FL) * gas_exsolved_upon_flashing * self.storage_gas_comp

        # Set output streams
        stp = self.ctx.stp
        output_flare = self.find_output_stream("gas for partition")
        output_flare.set_rates_from_series(vapor_to_flare, PHASE_GAS)
        output_flare.set_tp(stp)

        output_VRU = self.find_output_stream("gas for VRU")
        output_VRU.set_rates_from_series(vapor_to_VRU, PHASE_GAS)
        output_VRU.set_tp(stp)

        gas_fugitive_stream = Stream("gas_fugitives", tp=stp)
        gas_fugitive_stream.set_rates_from_series(gas_fugitives, PHASE_GAS)

        output_transport = self.find_output_stream("oil")
        oil_to_transport_mass_rate = (oil_mass_rate -
                                      output_VRU.total_gas_rate() -
                                      output_flare.total_gas_rate() -
                                      gas_fugitive_stream.total_gas_rate())
        output_transport.set_liquid_flow_rate("oil", oil_to_transport_mass_rate, tp=stp)
        output_transport.set_API(input_stream.API)

        iteration_value =\
            output_flare.total_flow_rate() +\
            output_VRU.total_flow_rate() +\
            gas_fugitive_stream.total_flow_rate() +\
            output_transport.total_flow_rate()
        self.set_iteration_value(iteration_value)

        # No energy-use for storage

        # emissions
        emissions = self.emissions
        emissions.set_from_stream(EM_FUGITIVES, gas_fugitive_stream)
