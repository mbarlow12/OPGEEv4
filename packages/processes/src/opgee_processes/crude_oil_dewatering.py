#
# CrudeOilDewatering class
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
from ..error import OpgeeException
from ..process import Process
from ..stream import PHASE_LIQUID
from ..thermodynamics import Oil, Water
from ..units import ureg
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class CrudeOilDewatering(Process):
    """
    A subclass of the Process class that represents a crude oil dewatering process
    in an oil and gas production system.

    Attributes:
        heater_treater (bool): Whether a heater treater is used in the process.
        temperature_heater_treater (Quantity[float]): Temperature of the heater treater.
        heat_loss (Quantity[float]): Heat loss in the process.
        prime_mover_type (str): Type of prime mover used for energy consumption.
        eta_gas (Quantity[float]): Efficiency of natural gas engine.
        eta_electricity (Quantity[float]): Efficiency of electricity.
        oil_path (str): The oil path in the process.
        oil_path_dict (dict): Dictionary mapping oil paths to their descriptions.
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        water: Water,
        oil_path: str,
        heater_treater: bool,
        temperature_heater_treater: Quantity[float],
        heat_loss: Quantity[float],
        prime_mover_type: str,
        eta_gas: Quantity[float],
        eta_electricity: Quantity[float],
    ):
        super().__init__(name, ctx)

        self.oil = oil
        self.water = water
        self.oil_path = oil_path
        self.heater_treater = heater_treater
        self.temperature_heater_treater = temperature_heater_treater
        self.heat_loss = heat_loss
        self.prime_mover_type = prime_mover_type
        self.eta_gas = eta_gas
        self.eta_electricity = eta_electricity

        # TODO: avoid process names in contents. Can all the subsequent processes just
        #  look for "oil"? Then we'd have a single output stream.
        self.oil_path_dict = {
            "Stabilization": "oil for stabilization",
            "Storage": "oil for storage",
            "Upgrading": "oil for upgrading",
            "Dilution": "oil for dilution",
            "Dilution and Upgrading": "oil for dilution",
        }

        self._required_inputs = [
            "oil",
        ]

        self._required_outputs = [
            "water",
            self.oil_path_dict[self.oil_path],
        ]

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("oil")
        if input.is_uninitialized():
            return

        input_T, input_P = input.tp.get()
        oil_rate = input.flow_rate("oil", PHASE_LIQUID)
        water_rate = input.flow_rate("H2O", PHASE_LIQUID)
        temp = self.temperature_heater_treater if self.heater_treater else input_T

        try:
            output = self.oil_path_dict[self.oil_path]
        except KeyError:
            raise OpgeeException(f"{self.name} oil path is not recognized:{self.oil_path}."
                                 f"Must be one of {list(self.oil_path_dict.keys())}")
        output_oil = self.find_output_stream(output)

        output_tp = TemperaturePressure(temp, input_P)
        output_oil.set_liquid_flow_rate("oil", oil_rate, tp=output_tp)
        output_oil.set_API(input.API)
        self.set_iteration_value(output_oil.total_flow_rate())

        water_to_treatment = self.find_output_stream("water", raiseError=None)
        if water_to_treatment is not None:
            water_to_treatment.set_liquid_flow_rate("H2O", water_rate, tp=output_tp)

        heat_duty = ureg.Quantity(0.0, "mmBtu/day")
        if self.heater_treater:
            average_oil_temp = (input_T.to("kelvin") + temp.to("kelvin")) / 2
            oil_heat_capacity = self.oil.specific_heat(input.API, average_oil_temp)
            water_heat_capacity = self.water.specific_heat(average_oil_temp)
            delta_temp = abs(input_T - temp)
            eff = (1 + self.heat_loss.to("frac")).to("frac")
            heat_duty = ((oil_rate * oil_heat_capacity + water_rate * water_heat_capacity) *
                         delta_temp * eff).to("mmBtu/day")

        # energy_use
        energy_use = self.energy
        energy_consumption = \
            heat_duty / self.eta_gas if self.prime_mover_type == "NG_engine" else heat_duty / self.eta_electricity
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        # import and export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
