#
# Functions used by Process subclasses
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
from ..units import ureg
from ..energy import EN_NATURAL_GAS, EN_ELECTRICITY, EN_DIESEL, EN_RESID
from ..error import OpgeeException
from ..stream import Stream, PHASE_GAS

_slope = {"NG_engine": -0.6035,
          "NG_turbine": -0.1279}

_intercept = {"NG_engine": 7922.4,
              "NG_turbine": 9219.6}

_maxBHP = {"NG_engine": 2800.0,
           "Diesel_engine": 3000.0,
           "NG_turbine": 21000.0,
           "Electric_motor": 1000.0}


def get_efficiency(prime_mover_type, brake_horsepower):
    """

    :param prime_mover_type:
    :param brake_horsepower:
    :return: (pint.Quantity) efficiency in units of "btu/horsepower/hour"
    """
    brake_horsepower = brake_horsepower.to("horsepower").m
    brake_horsepower = min(_maxBHP[prime_mover_type], brake_horsepower)

    if prime_mover_type == "Electric_motor":
        efficiency = 2967 * brake_horsepower ** (-0.018) if brake_horsepower != 0.0 else 3038
    elif prime_mover_type == "Diesel_engine":
        efficiency = 0.0004 * brake_horsepower ** 2 - 1.6298 * brake_horsepower + 7955.8
    else:
        efficiency = _slope[prime_mover_type] * brake_horsepower + _intercept[prime_mover_type]

    return ureg.Quantity(efficiency, "btu/horsepower/hour")


def get_init_lifting_stream(gas,
                            lifting_gas_stream,
                            gas_lifting_vol_rate):
    """
    Generate initial gas stream for lifting

    :param gas_lifting_vol_rate: GLIR * (oil rate + water rate)
    :param lifting_gas_stream: (Stream) stream that used for gas lifting
    :param gas: (Gas) the current Field's ``Gas`` instance
    :return: (Stream) initial gas lifting stream
    """

    lifting_gas_mass_fracs = gas.component_mass_fractions(gas.component_molar_fractions(lifting_gas_stream))

    series = (lifting_gas_mass_fracs *
              gas_lifting_vol_rate *
              gas.component_gas_rho_STP[lifting_gas_stream.gas_flow_rates().index])

    stream = Stream("gas lifting stream", lifting_gas_stream.tp)
    stream.set_rates_from_series(series, PHASE_GAS)
    stream.set_tp(lifting_gas_stream.tp)
    return stream


#
# Helper function shared by acid_gas_removal, gas_dehydration, and demethanizer
#
def predict_blower_energy_use(
    thermal_load,
    air_cooler_delta_T,
    water_press,
    air_cooler_fan_eff,
    air_cooler_speed_reducer_eff,
    air_elevation_const,
    air_density_ratio,
):
    """
    Predict blower energy use per day. All parameters are explicit (no implicit
    lookup through a Process). Callers pass the values they previously read off
    their Field/Model.

    :param thermal_load: thermal load (Quantity, btu/hr)
    :param air_cooler_delta_T: air cooler delta-T (Quantity)
    :param water_press: water pressure drop (Quantity)
    :param air_cooler_fan_eff: fan efficiency (Quantity, frac)
    :param air_cooler_speed_reducer_eff: speed reducer efficiency (Quantity, frac)
    :param air_elevation_const: air elevation correction (Quantity — was model.const("air-elevation-corr"))
    :param air_density_ratio: air density ratio (Quantity — was model.const("air-density-ratio"))
    :return: (Quantity) air cooling fan energy consumption (kWh/day)
    """
    blower_air_quantity = thermal_load / air_elevation_const / air_cooler_delta_T
    blower_CFM = blower_air_quantity / air_density_ratio
    blower_delivered_hp = blower_CFM * water_press / air_cooler_fan_eff
    blower_fan_motor_hp = blower_delivered_hp / air_cooler_speed_reducer_eff
    air_cooler_energy_consumption = get_energy_consumption("Electric_motor", blower_fan_motor_hp)
    return air_cooler_energy_consumption.to("kWh/day")


def get_energy_carrier(prime_mover_type):
    if prime_mover_type.startswith("NG_") or prime_mover_type.lower() == "natural gas":
        return EN_NATURAL_GAS

    if prime_mover_type.startswith("Electric"):
        return EN_ELECTRICITY

    if prime_mover_type.startswith("Diesel"):
        return EN_DIESEL

    if prime_mover_type.startswith("Resid"):
        return EN_RESID

    raise OpgeeException(f"Unrecognized prime_mover_type: '{prime_mover_type}'")


def get_energy_consumption_stages(prime_mover_type, brake_horsepower_of_stages):
    energy_consumption_of_stages = []
    for brake_horsepower in brake_horsepower_of_stages:
        eff = get_efficiency(prime_mover_type, brake_horsepower)
        energy_consumption = (brake_horsepower * eff).to("mmBtu/day")
        energy_consumption_of_stages.append(energy_consumption)

    return energy_consumption_of_stages


def get_energy_consumption(prime_mover_type, brake_horsepower):
    eff = get_efficiency(prime_mover_type, brake_horsepower)
    energy_consumption = (brake_horsepower * eff).to("mmBtu/day")

    return energy_consumption


def get_bounded_value(value, name, variable_bound_dict):
    """

    :param value:
    :param name:
    :param variable_bound_dict: dictionary of bounded variables; key = variable name (str), value = [min, max]
    :return: bounded valued without unit
    """
    try:
        bounds = variable_bound_dict[name]
    except KeyError:
        raise OpgeeException(f"Variable bound dictionary does not have {name}")

    return min(max(value, bounds[0]), bounds[1])
