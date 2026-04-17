#
# Separation class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..combine_streams import combine_streams
from ..context import FieldContext
from ..core import TemperaturePressure
from ..emissions import EM_FUGITIVES
from ..process import Process
from ..processes.compressor import Compressor
from ..stream import Stream, PHASE_GAS
from ..thermodynamics import Gas, Oil, Water
from .shared import get_energy_carrier, get_energy_consumption_stages

_logger = logging.getLogger(__name__)


class Separation(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil: Oil,
        gas: Gas,
        water: Water,
        oil_volume_rate: Quantity[float],
        wellhead_t: Quantity[float],
        wellhead_p: Quantity[float],
        gas_oil_ratio: Quantity[float],
        gas_comp: pd.Series,
        stab_gas_press: Quantity[float],
        WOR: Quantity[float],
        API: Quantity[float],
        prime_mover_type: str,
        temperature_outlet: Quantity[float],
        pressure_outlet: Quantity[float],
        pressure_first_stage: Quantity[float],
        pressure_second_stage: Quantity[float],
        pressure_third_stage: Quantity[float],
        number_stages: int,
        water_content_oil_emulsion: Quantity[float],
        eta_compressor: Quantity[float],
        loss_rate: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "oil",
        ]

        self._required_outputs = [
            "gas for partition",    # TODO: this is called "gas for gas partition" elsewhere
        ]

        self.oil = oil
        self.gas = gas
        self.water = water
        self.water_density_STP = water.density()

        self.oil_volume_rate = oil_volume_rate
        self.API = API
        self.WOR = WOR
        self.prime_mover_type = prime_mover_type
        self.compressor_eff = eta_compressor
        self.num_of_stages = number_stages
        self.water_content = water_content_oil_emulsion
        self.pressure_after_boosting = stab_gas_press

        self.outlet_tp = TemperaturePressure(temperature_outlet, pressure_outlet)
        self.wellhead_tp = TemperaturePressure(wellhead_t, wellhead_p)

        self.temperature_stage1 = wellhead_t
        self.temperature_stage2 = (wellhead_t.to("kelvin") + self.outlet_tp.T.to("kelvin")) / 2

        #TODO: move it to smart default
        self.pressure_stage1 = min(wellhead_p, pressure_first_stage)
        self.pressure_stage2 = pressure_second_stage
        self.pressure_stage3 = pressure_third_stage

        self.gas_oil_ratio = gas_oil_ratio
        self.gas_comp = gas_comp

        #TODO: move it to smart default
        if wellhead_p.m < 500:
            self.num_of_stages = 1

        self.loss_rate = loss_rate

    def run(self):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("oil")

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        gas_after = self.find_output_stream("gas for partition")
        gas_after.copy_gas_rates_from(input)
        gas_after.subtract_rates_from(gas_fugitives)
        self.ctx.process_data["gas_tp_after_separation"] = gas_after.tp

        self.set_iteration_value(gas_after.total_flow_rate())

        # energy rate

        free_gas_stages, final_GOR = self.get_free_gas_stages(input)  # (float, list) scf/bbl
        gas_compression_volume_stages = [(self.oil_volume_rate * free_gas).to("mmscf/day") for free_gas in
                                         free_gas_stages]
        compressor_brake_horsepower_of_stages = self.compressor_brake_horsepower_of_stages(gas_after,
                                                                                           gas_compression_volume_stages)
        energy_consumption_of_stages = get_energy_consumption_stages(self.prime_mover_type,
                                                                     compressor_brake_horsepower_of_stages)
        energy_consumption_sum = sum(energy_consumption_of_stages)

        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption_sum)

        # import/export
        self.set_import_from_energy(energy_use)

        # emission rate
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)

    def impute(self):
        oil = self.oil

        gas_after, oil_after, water_after = self.get_output_streams()
        output = combine_streams([oil_after, gas_after, water_after])

        output.multiply_flow_rates(self.loss_rate)

        input = self.find_input_stream("oil")
        input.copy_flow_rates_from(output, tp=self.wellhead_tp)
        oil_LHV_rate = oil.energy_flow_rate(input)
        gas_LHV_rate = self.gas.energy_flow_rate(input)
        self.ctx.process_data["wellhead_LHV_rate"] = gas_LHV_rate + oil_LHV_rate

    def get_stages_temperature_and_pressure(self):

        temperature_of_stages = [self.temperature_stage1, self.temperature_stage2.to("degF"), self.outlet_tp.T]

        pressure_of_stages = [self.pressure_stage1, self.pressure_stage2, self.pressure_stage3]

        return temperature_of_stages, pressure_of_stages

    def get_output_streams(self):
        temperature_of_stages, pressure_of_stages = self.get_stages_temperature_and_pressure()

        oil = self.oil
        gas = self.gas

        gas_after = self.find_output_stream("gas for partition")

        last = self.num_of_stages - 1
        stream = Stream("stage_stream", TemperaturePressure(temperature_of_stages[last],
                                                            pressure_of_stages[last]))

        density = oil.density(stream,  # lb/ft3
                              oil.oil_specific_gravity,
                              oil.gas_specific_gravity,
                              oil.gas_oil_ratio)

        gas_volume_rate = self.oil_volume_rate * self.gas_oil_ratio * self.gas_comp
        gas_density = gas.component_gas_rho_STP[self.gas_comp.index]
        gas_mass_rate = gas_volume_rate * gas_density
        gas_after.set_rates_from_series(gas_mass_rate, PHASE_GAS)
        gas_after.tp.set(T=self.outlet_tp.T, P=self.pressure_after_boosting)

        oil_after = self.find_output_stream("oil")
        oil_mass_rate = (self.oil_volume_rate * density).to("tonne/day")
        water_in_oil_mass_rate = self.water_in_oil_mass_rate(oil_mass_rate)
        oil_after.set_liquid_flow_rate("oil", oil_mass_rate)
        oil_after.set_liquid_flow_rate("H2O", water_in_oil_mass_rate)
        oil_after.set_tp(self.outlet_tp)
        oil_after.set_API(self.API)

        water_mass_rate = max(0, self.oil_volume_rate * self.WOR * self.water_density_STP - water_in_oil_mass_rate)
        water_after = self.find_output_stream("water")
        water_after.set_liquid_flow_rate("H2O", water_mass_rate, tp=self.outlet_tp)

        return gas_after, oil_after, water_after

    def water_in_oil_mass_rate(self, oil_mass_rate):
        """

        :param oil_mass_rate: (float) oil mass rate
        :return: (float) water mass rate in the oil stream after separation (unit = tonne/day)
        """
        water_in_oil_mass_rate = (oil_mass_rate * self.water_content).to("tonne/day")
        return water_in_oil_mass_rate

    def get_free_gas_stages(self, input_stream):
        oil = self.oil

        temperature_of_stages, pressure_of_stages = self.get_stages_temperature_and_pressure()

        solution_gas_oil_ratio_of_stages = [oil.gas_oil_ratio]
        oil_SG = oil.specific_gravity(input_stream.API)
        for stage in range(self.num_of_stages):
            stream_stages = Stream("stage_stream", TemperaturePressure(temperature_of_stages[stage],
                                                                       pressure_of_stages[stage]))
            solution_gas_oil_ratio = oil.solution_gas_oil_ratio(stream_stages,
                                                                oil_SG,
                                                                oil.gas_specific_gravity,
                                                                oil.gas_oil_ratio)
            solution_gas_oil_ratio_of_stages.append(solution_gas_oil_ratio)

        free_gas_of_stages = []
        for i in range(1, len(solution_gas_oil_ratio_of_stages)):
            free_gas_of_stages.append(solution_gas_oil_ratio_of_stages[i - 1] -
                                      solution_gas_oil_ratio_of_stages[i])

        return free_gas_of_stages, solution_gas_oil_ratio_of_stages[-1]

    def compressor_brake_horsepower_of_stages(self, gas_stream, gas_compression_volume_stages):
        """
        Get the compressor horsepower of all stages in the separator

        :param gas_stream:
        :param gas_compression_volume_stages: (float) a list contains gas compression volume for each stages
        :return: (float) compresssor brake horsepower for each stages
        """

        temperature_of_stages, pressure_of_stages = self.get_stages_temperature_and_pressure()

        overall_compression_ratio_stages = [self.pressure_after_boosting /
                                            pressure_of_stages[stage] for stage in range(self.num_of_stages)]
        compression_ratio_per_stages = Compressor.get_compression_ratio_stages(overall_compression_ratio_stages)

        brake_horsepower_of_stages = []
        for (inlet_temp, inlet_press, (compression_ratio, num_of_compression),
             gas_compression_volume) \
                in zip(temperature_of_stages,
                       pressure_of_stages,
                       compression_ratio_per_stages,
                       gas_compression_volume_stages):
            work_sum, _, _ = Compressor.get_compressor_work_temp(self.gas, inlet_temp, inlet_press,
                                                                 gas_stream, compression_ratio, num_of_compression)
            horsepower = work_sum * gas_compression_volume
            brake_horsepower = horsepower / self.compressor_eff
            brake_horsepower_of_stages.append(brake_horsepower)

        return brake_horsepower_of_stages
