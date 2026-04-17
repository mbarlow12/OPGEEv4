#
# DownholePump class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import numpy as np
from pint.facets.plain import PlainQuantity as Quantity

from ..combine_streams import combine_streams
from ..context import FieldContext
from ..core import TemperaturePressure
from ..emissions import EM_FUGITIVES
from ..process import Process
from ..stream import PHASE_GAS, Stream
from ..thermodynamics import Gas, Oil, Water
from ..units import ureg
from .shared import get_energy_carrier, get_energy_consumption_stages

_logger = logging.getLogger(__name__)


class DownholePump(Process):
    """
    A class to represent the DownholePump process, which is responsible for lifting
    crude oil from a reservoir to the surface using a downhole pump.

    Attributes
        gas_lifting : bool
            Whether gas lifting is enabled in the field.
        res_temp : Quantity[float]
            The reservoir temperature.
        oil_volume_rate : Quantity[float]
            The oil volume rate in the field.
        eta_pump_well : Quantity[float]
            The efficiency of the downhole pump in the well.
        prod_tubing_diam : Quantity[float]
            The diameter of the production tubing.
        prod_tubing_xsection_area : float
            The cross-sectional area of the production tubing.
        depth : Quantity[float]
            The depth of the reservoir.
        friction_factor : float
            The friction factor for the production tubing.
        num_prod_wells : int
            The number of production wells in the field.
        gravitational_acceleration : Quantity[float]
            The gravitational acceleration constant.
        prime_mover_type : str
            The type of prime mover used in the process.
        wellhead_t : Quantity[float]
            The wellhead temperature.
        wellhead_tp : TemperaturePressure
            The wellhead temperature and pressure.
        oil_sand_mine : str
            Whether the field is an oil sands mine.

    Methods
        run()
            Simulates the DownholePump process to lift crude oil from the reservoir
            to the surface and calculates the energy consumption and emissions.
        impute()
            Estimates the completion and workover fugitive stream and adjusts the input stream.
    """
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        gas: Gas,
        water: Water,
        downhole_pump: bool,
        gas_lifting: bool,
        res_temp: Quantity[float],
        oil_volume_rate: Quantity[float],
        eta_pump_well: Quantity[float],
        prod_tubing_diam: Quantity[float],
        depth: Quantity[float],
        friction_factor: Quantity[float],
        num_prod_wells: int,
        prime_mover_type: str,
        wellhead_t: Quantity[float],
        wellhead_pressure: Quantity[float],
        oil_sands_mine: str,
        gravitational_acceleration: Quantity[float],
        loss_rate: Quantity[float],
        completion_and_workover_C1_rate: Quantity[float],
    ):
        super().__init__(name, ctx)

        self._required_inputs = [
            "oil",
            # "lifting gas", # optional input stream
        ]

        self._required_outputs = [
            "oil",
        ]

        self.oil = oil
        self.gas = gas
        self.water = water
        self.downhole_pump = downhole_pump
        self.gas_lifting = gas_lifting
        self.res_temp = res_temp
        self.oil_volume_rate = oil_volume_rate
        self.eta_pump_well = eta_pump_well
        self.prod_tubing_diam = prod_tubing_diam
        self.prod_tubing_xsection_area = np.pi * (prod_tubing_diam / 2) ** 2
        self.depth = depth
        self.friction_factor = friction_factor
        self.num_prod_wells = num_prod_wells
        self.prime_mover_type = prime_mover_type
        self.wellhead_tp = TemperaturePressure(wellhead_t, wellhead_pressure)
        self.oil_sand_mine = oil_sands_mine
        self.gravitational_acceleration = gravitational_acceleration
        self.loss_rate = loss_rate
        self.completion_and_workover_C1_rate = completion_and_workover_C1_rate

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("oil")
        if input.is_uninitialized():
            return

        lift_gas = self.find_input_stream('lifting gas', raiseError=None)
        if lift_gas is not None and lift_gas.is_initialized():
            input = combine_streams([input, lift_gas])

        loss_rate = self.loss_rate
        gas_fugitives = self.set_gas_fugitives(input, loss_rate)

        output = self.find_output_stream("oil")
        output.copy_flow_rates_from(input, tp=self.wellhead_tp)
        output.subtract_rates_from(gas_fugitives)

        completion_workover_fugitive_stream = self.ctx.process_data.get("completion_workover_fugitive_stream")
        if completion_workover_fugitive_stream is not None:
            gas_fugitives.add_flow_rates_from(completion_workover_fugitive_stream)
            output.subtract_rates_from(completion_workover_fugitive_stream)

        self.set_iteration_value(output.total_flow_rate())

        # energy use
        oil = self.oil
        water = self.water
        gas = self.gas
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        if not self.gas_lifting:
            oil_SG = oil.specific_gravity(input.API)
            solution_gas_oil_ratio_input = oil.solution_gas_oil_ratio(input,
                                                                      oil_SG,
                                                                      oil.gas_specific_gravity,
                                                                      oil.gas_oil_ratio)
            solution_gas_oil_ratio_output = oil.solution_gas_oil_ratio(output,
                                                                       oil_SG,
                                                                       oil.gas_specific_gravity,
                                                                       oil.gas_oil_ratio)
            oil_density_input = oil.density(input,
                                            oil_SG,
                                            oil.gas_specific_gravity,
                                            oil.gas_oil_ratio)
            oil_density_output = oil.density(output,
                                             oil_SG,
                                             oil.gas_specific_gravity,
                                             oil.gas_oil_ratio)
            volume_oil_lifted_input = oil.volume_flow_rate(input,
                                                           oil_SG,
                                                           oil.gas_specific_gravity,
                                                           oil.gas_oil_ratio)
            volume_oil_lifted_output = oil.volume_flow_rate(output,
                                                            oil_SG,
                                                            oil.gas_specific_gravity,
                                                            oil.gas_oil_ratio)

            # properties of crude oil (all at average conditions along wellbore, in production tubing)
            average_solution_GOR = (solution_gas_oil_ratio_input + solution_gas_oil_ratio_output) / 2
            average_oil_density = (oil_density_input + oil_density_output) / 2
            average_volume_oil_lifted = (volume_oil_lifted_input + volume_oil_lifted_output).to("ft**3/day") / 2

            # properties of water (all at average conditions along wellbore, in production tubing)
            water_density = water.density(temperature=input.tp.T, pressure=input.tp.P)
            volume_water_lifted = water.volume_flow_rate(output)

            wellhead_T, wellhead_P = self.wellhead_tp.get()

            # properties of free gas (all at average conditions along wellbore, in production tubing)
            free_gas = max(ureg.Quantity(0, "scf/bbl"), (solution_gas_oil_ratio_input - average_solution_GOR))
            wellbore_average_press = (wellhead_P + input.tp.P) / 2
            wellbore_average_temp = ureg.Quantity((wellhead_T.m + self.res_temp.m) / 2, "degF")
            wellbore_average_tp = TemperaturePressure(wellbore_average_temp, wellbore_average_press)
            stream = Stream("average", wellbore_average_tp)
            stream.copy_flow_rates_from(input, tp=wellbore_average_tp)
            gas_FVF = gas.volume_factor(stream)
            gas_density = gas.density(stream)
            volume_free_gas = free_gas * gas_FVF
            volume_free_gas_lifted = (volume_free_gas * self.oil_volume_rate)

            total_volume_fluid_lifted = (average_volume_oil_lifted +
                                         volume_water_lifted +
                                         volume_free_gas_lifted)
            fluid_velocity = (total_volume_fluid_lifted / (self.prod_tubing_xsection_area * self.num_prod_wells))

            total_mass_fluid_lifted = (average_oil_density * average_volume_oil_lifted +
                                       water_density * volume_water_lifted +
                                       gas_density * volume_free_gas_lifted)
            fluid_lifted_density = (total_mass_fluid_lifted / total_volume_fluid_lifted)

            # downhole pump
            pressure_drop_elev = fluid_lifted_density * self.gravitational_acceleration * self.depth
            pressure_drop_fric = (fluid_lifted_density * self.friction_factor * self.depth * fluid_velocity ** 2 /
                                  (2 * self.prod_tubing_diam))
            pressure_drop_total = pressure_drop_fric + pressure_drop_elev
            pressure_for_lifting = max(ureg.Quantity(0.0, "psia"), wellhead_P + pressure_drop_total - input.tp.P)
            liquid_flow_rate_per_well = (average_volume_oil_lifted + volume_water_lifted) / self.num_prod_wells
            brake_horse_power = 1.05 * (liquid_flow_rate_per_well * pressure_for_lifting) / self.eta_pump_well
            energy_consumption_of_stages = get_energy_consumption_stages(self.prime_mover_type, [brake_horse_power])
            energy_consumption_sum = sum(energy_consumption_of_stages) * self.num_prod_wells
            energy_use.set_rate(energy_carrier, energy_consumption_sum)

            # import and export
            self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)

    def impute(self):
        output = self.find_output_stream("oil")

        loss_rate = self.loss_rate
        loss_rate = (1 / (1 - loss_rate)).to("frac")

        well_completion_and_workover_C1_rate = self.completion_and_workover_C1_rate
        output_mol_fracs = self.gas.component_molar_fractions(output)
        output_mass_fracs = self.gas.component_mass_fractions(output_mol_fracs)
        total_mass_rate_from_completion_workover = well_completion_and_workover_C1_rate / output_mass_fracs["C1"]
        completion_workover_fugitive_series = total_mass_rate_from_completion_workover * output_mass_fracs

        completion_workover_fugitive_stream = Stream("completion_workover_fugitive", tp=output.tp)
        completion_workover_fugitive_stream.set_rates_from_series(completion_workover_fugitive_series, phase=PHASE_GAS)
        self.ctx.process_data["completion_workover_fugitive_stream"] = completion_workover_fugitive_stream

        input = self.find_input_stream("oil")
        input.copy_flow_rates_from(output)
        input.add_flow_rates_from(completion_workover_fugitive_stream)
        input.multiply_flow_rates(loss_rate)
