#
# WaterInjection class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import numpy as np
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..error import OpgeeException
from ..process import Process
from ..thermodynamics import Water
from ..units import ureg
from .shared import get_energy_carrier, get_energy_consumption

_logger = logging.getLogger(__name__)


class WaterInjection(Process):
    """
        TBD

        input streams:
            -

        output streams:
            -
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        water: Water,
        water_reinjection: bool,
        water_flooding: bool,
        productivity_index: Quantity[float],
        res_press: Quantity[float],
        num_water_inj_wells: Quantity[float],
        depth: Quantity[float],
        prod_tubing_diam: Quantity[float],
        friction_factor: Quantity[float],
        press_pump: Quantity[float],
        eta_pump: Quantity[float],
        prime_mover_type: str,
        gravitation_acc: Quantity[float],
        gravitation_const: Quantity[float],
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "water",
        ]

        self._required_outputs = []

        self.water_reinjection = water_reinjection
        self.water_flooding = water_flooding
        self.productivity_index = productivity_index
        self.res_press = res_press
        self.num_water_inj_wells = num_water_inj_wells
        self.depth = depth
        self.prod_tubing_diam = prod_tubing_diam
        self.xsection_area = np.pi * (prod_tubing_diam / 2) ** 2
        self.friction_factor = friction_factor
        self.press_pump = press_pump
        self.eta_pump = eta_pump
        self.prime_mover_type = prime_mover_type
        self.gravitation_acc = gravitation_acc
        self.gravitation_const = gravitation_const
        self.water_density = water.density()

    def run(self):
        self.print_running_msg()

        if self.num_water_inj_wells.m == 0:
            raise OpgeeException(f"Got zero number of injector in the {self.name} process")

        input = self.find_input_stream("water")
        if input.is_uninitialized():
            return

        water_mass = input.liquid_flow_rate("H2O")
        water_volume = water_mass / self.water_density
        single_well_water_volume = water_volume / self.num_water_inj_wells

        wellbore_flowing_press = single_well_water_volume / self.productivity_index + self.res_press
        water_gravitation_head = self.water_density * self.gravitation_acc * self.depth
        water_flow_velocity = single_well_water_volume / self.xsection_area

        friction_loss = (self.friction_factor * self.depth * water_flow_velocity ** 2) / \
                        (2 * self.prod_tubing_diam * self.gravitation_const) * self.water_density
        diff_press = wellbore_flowing_press - water_gravitation_head

        pumping_press = diff_press + friction_loss - self.press_pump \
            if diff_press + friction_loss >= 0 else ureg.Quantity(0.0, "psia")
        pumping_hp_single_well = pumping_press * single_well_water_volume / self.eta_pump

        # energy-use
        water_pump_power_single_well = get_energy_consumption(self.prime_mover_type, pumping_hp_single_well)
        total_water_pump_power = water_pump_power_single_well * self.num_water_inj_wells
        energy_use = self.energy

        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, total_water_pump_power)

        # import and export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
