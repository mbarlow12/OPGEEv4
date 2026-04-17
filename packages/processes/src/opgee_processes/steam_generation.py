#
# SteamGeneration class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging
from typing import TYPE_CHECKING

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import TemperaturePressure
from ..energy import EN_NATURAL_GAS, EN_ELECTRICITY
from ..error import BalanceError
from ..import_export import WATER
from ..process import Process
from ..thermodynamics import Water
from ..units import ureg
from .shared import get_energy_consumption

if TYPE_CHECKING:
    from .steam_generator import SteamGenerator

_logger = logging.getLogger(__name__)

# the tolerance is used for checking mass and energy balance
# (input - output) / input < tolerance
tolerance = 0.01


class SteamGeneration(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        water: Water,
        steam_generator: "SteamGenerator",
        steam_flooding: bool,
        SOR: Quantity[float],
        oil_volume_rate: Quantity[float],
        res_press: Quantity[float],
        friction_loss_steam_distr: Quantity[float],
        fraction_steam_cogen: Quantity[float],
        fraction_steam_solar: Quantity[float],
        steam_quality_outlet: Quantity[float],
        steam_quality_after_blowdown: Quantity[float],
        fraction_blowdown_recycled: Quantity[float],
        waste_water_reinjection_temp: Quantity[float],
        waste_water_reinjection_press: Quantity[float],
        pressure_loss_choke_wellhead: Quantity[float],
        steam_injection_delta_press: Quantity[float],
        prod_water_inlet_press: Quantity[float],
        makeup_water_inlet_press: Quantity[float],
        eta_displacement_pump: Quantity[float],
        eta_air_blower_OTSG: Quantity[float],
        eta_air_blower_HRSG: Quantity[float],
        eta_air_blower_solar: Quantity[float],
    ):
        super().__init__(name, ctx)

        if steam_flooding == 1 and SOR != 0:
            self._required_inputs = [
                "produced water",
                "makeup water"
            ]
            self._required_outputs = [
                "water",
            ]
        else:
            self._required_inputs = []
            self._required_outputs = []

        self.water = water
        self.water_density = water.density()
        self.steam_generator = steam_generator
        self.steam_flooding_check = steam_flooding
        self.SOR = SOR
        self.oil_volume_rate = oil_volume_rate
        self.res_press = res_press
        self.friction_loss_steam_distr = friction_loss_steam_distr
        self.fraction_steam_cogen = fraction_steam_cogen
        self.fraction_steam_solar = fraction_steam_solar
        self.steam_quality_outlet = steam_quality_outlet
        self.steam_quality_after_blowdown = steam_quality_after_blowdown
        self.fraction_blowdown_recycled = fraction_blowdown_recycled
        self.waste_water_reinjection_tp = TemperaturePressure(
            waste_water_reinjection_temp, waste_water_reinjection_press
        )
        self.pressure_loss_choke_wellhead = pressure_loss_choke_wellhead
        self.steam_injection_delta_press = steam_injection_delta_press
        self.prod_water_inlet_press = prod_water_inlet_press
        self.makeup_water_inlet_press = makeup_water_inlet_press
        self.eta_displacement_pump = eta_displacement_pump
        self.eta_air_blower_OTSG = eta_air_blower_OTSG
        self.eta_air_blower_HRSG = eta_air_blower_HRSG
        self.eta_air_blower_solar = eta_air_blower_solar

        self.fraction_OTSG = 1 - fraction_steam_cogen - fraction_steam_solar
        self.steam_generator_press_outlet = (
            (self.res_press + self.steam_injection_delta_press)
            * self.friction_loss_steam_distr
            * self.pressure_loss_choke_wellhead
        )

    def run(self):
        self.print_running_msg()
        self.set_iteration_value(0)

        # mass rate
        input_prod_water = self.find_input_stream("produced water")
        input_makeup_water = self.find_input_stream("makeup water")
        if input_prod_water.is_uninitialized() and input_makeup_water.is_uninitialized():
            return

        prod_water_mass_rate = input_prod_water.liquid_flow_rate("H2O")
        makeup_water_mass_rate = input_makeup_water.liquid_flow_rate("H2O")
        water_mass_rate_for_injection = prod_water_mass_rate + makeup_water_mass_rate

        steam_quality_diff_between_blowndown_and_outlet = self.steam_quality_after_blowdown - self.steam_quality_outlet
        steam_quality_diff_between_blowndown_and_outlet = \
            ureg.Quantity(max(steam_quality_diff_between_blowndown_and_outlet.to("frac").m, 0.0), "frac")

        if steam_quality_diff_between_blowndown_and_outlet.m < 0:
            _logger.warning("steam quality after blowdown is smaller than steam quality at outlet")

        blowdown_water_mass_rate = \
            water_mass_rate_for_injection * steam_quality_diff_between_blowndown_and_outlet / self.steam_quality_outlet
        waste_water_from_blowdown = blowdown_water_mass_rate * (1 - self.fraction_blowdown_recycled)
        self.import_export.set_export(self.name, WATER, waste_water_from_blowdown)

        recycled_blowdown_water = blowdown_water_mass_rate * self.fraction_blowdown_recycled

        recycled_water_stream = self.find_output_stream("water")
        recycled_water_stream.set_liquid_flow_rate("H2O",
                                                   recycled_blowdown_water.to("tonne/day"),
                                                   tp=self.waste_water_reinjection_tp)

        fuel_consumption_OTSG = fuel_consumption_HRSG = fuel_consumption_solar = \
            electricity_HRSG = ureg.Quantity(0, "MJ/day")

        fraction_OTSG = self.fraction_OTSG
        if fraction_OTSG.m != 0:
            fuel_consumption_OTSG, mass_in_OTSG, mass_out_OTSG, energy_in_OTSG, energy_out_OTSG = \
                self.steam_generator.once_through_SG(prod_water_mass_rate * fraction_OTSG,
                                                     makeup_water_mass_rate * fraction_OTSG,
                                                     water_mass_rate_for_injection * fraction_OTSG,
                                                     blowdown_water_mass_rate * fraction_OTSG)
            self.check_balance(mass_in_OTSG, mass_out_OTSG, "OTSG_mass")
            self.check_balance(energy_in_OTSG, energy_out_OTSG, "OTSG_energy")

        fraction_steam_cogen = self.fraction_steam_cogen
        if self.fraction_steam_cogen != 0:
            fuel_consumption_HRSG, electricity_HRSG, mass_in_HRSG, mass_out_HRSG, energy_in_HRSG, energy_out_HRSG = \
                self.steam_generator.heat_recovery_SG(prod_water_mass_rate * fraction_steam_cogen,
                                                      makeup_water_mass_rate * fraction_steam_cogen,
                                                      water_mass_rate_for_injection * fraction_steam_cogen,
                                                      blowdown_water_mass_rate * fraction_steam_cogen)
            self.check_balance(mass_in_HRSG, mass_out_HRSG, "HRSG_mass")
            self.check_balance(energy_in_HRSG, energy_out_HRSG, "HRSG_energy")

        if self.fraction_steam_solar != 0:
            fuel_consumption_solar = \
                self.steam_generator.solar_SG(prod_water_mass_rate * self.fraction_steam_solar,
                                              makeup_water_mass_rate * self.fraction_steam_solar)

        # energy use
        energy_use = self.energy
        NG_consumption = fuel_consumption_OTSG + fuel_consumption_HRSG
        energy_use.set_rate(EN_NATURAL_GAS, NG_consumption.to("mmBtu/day"))

        water_pump_hp = self.get_feedwater_horsepower(prod_water_mass_rate, makeup_water_mass_rate)
        water_pump_power = get_energy_consumption("Electric_motor", water_pump_hp)
        OTSG_air_blower = get_energy_consumption("Electric_motor",
                                                 fuel_consumption_OTSG * self.eta_air_blower_OTSG)
        HRSG_air_blower = get_energy_consumption("Electric_motor",
                                                 fuel_consumption_HRSG * self.eta_air_blower_HRSG)
        solar_thermal_pumping = get_energy_consumption("Electric_motor",
                                                       fuel_consumption_solar * self.eta_air_blower_solar)
        total_power_required = water_pump_power + OTSG_air_blower + HRSG_air_blower + solar_thermal_pumping
        energy_use.set_rate(EN_ELECTRICITY, total_power_required)

        # import/export
        self.set_import_from_energy(energy_use)
        self.import_export.set_export(self.name, EN_ELECTRICITY, electricity_HRSG)

        # emissions
        self.set_combustion_emissions()

    def get_feedwater_horsepower(self, prod_water_mass_rate, makeup_water_mass_rate):
        prod_water_volume_rate = prod_water_mass_rate / self.water_density
        makeup_water_mass_rate = makeup_water_mass_rate / self.water_density

        result = makeup_water_mass_rate * (self.steam_generator_press_outlet - self.makeup_water_inlet_press) + \
                 prod_water_volume_rate * (self.steam_generator_press_outlet - self.prod_water_inlet_press)
        result /= self.eta_displacement_pump

        return result

    def check_balance(self, input, output, label):
        """

        :param input:
        :param output:
        :param label:
        :return:
        """

        unit = input.units
        if abs(input.m - output.to(unit).m) > tolerance * input.m:
            raise BalanceError(self.name, label)
