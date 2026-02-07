"""Smart default functions extracted from Field class (field.py:1554–1752).

All functions are standalone (no self parameter) and registered with the
simplified SmartDefault_ registry.
"""

from math import exp

import pint

from opgee.units import ureg
from opgee.utils import roundup

from .smart_defaults import register


@register("WOR", ["steam_flooding", "age", "SOR"])
def WOR_default(steam_flooding: int, age: pint.Quantity, SOR: float) -> float:
    if steam_flooding:
        return SOR

    tmp = 4.021 * exp(0.024 * age.to("yr").m) - 4.021
    return tmp if tmp <= 100 else 100


@register("SOR", ["steam_flooding"])
def SOR_default(steam_flooding: int) -> float:
    return 3.0 if steam_flooding else 1.0


@register("GOR", ["API"])
def GOR_default(API: pint.Quantity) -> float:
    api = API.to("degAPI").m

    if api < 20:
        return 1122.4
    elif 20 <= api <= 30:
        return 1205.4
    else:
        return 2429.3


@register("WIR", ["WOR"])
def WIR_default(wor: float) -> float:
    return wor + 1


@register("stabilizer_column", ["GOR", "gas_lifting", "oil_sands_mine"])
def stabilizer_default(GOR: float, gas_lifting: int, oil_sands_mine: str) -> int:
    return (
        0 if (oil_sands_mine != "None") or (not gas_lifting and GOR <= 500) else 1
    )


@register("GFIR", ["flood_gas_type", "GOR"])
def GFIR_default(flood_gas_type: int, GOR: float) -> float:
    if flood_gas_type == 1:
        return 1.5 * GOR
    elif flood_gas_type == 2:
        return 1200
    elif flood_gas_type == 3:
        return 10000
    else:
        return 1.5 * GOR


@register("depth", ["GOR"])
def depth_default(GOR: pint.Quantity) -> float:
    gas_field_default_depth = 8285.0
    return gas_field_default_depth if GOR.m > 10000 else 7122.0


@register("res_press", ["country", "depth", "steam_flooding"])
def res_press_default(country: str, depth: pint.Quantity, steam_flooding: int) -> float:
    return (
        100.0
        if (country == "California" and steam_flooding)
        else 0.5 * depth.to("ft").m * 0.43
    )


@register("res_temp", ["depth"])
def res_temp_default(depth: pint.Quantity) -> float:
    return 70 + 1.8 * depth.to("ft").m / 100.0


@register("CrudeOilDewatering.heater_treater", ["API"])
def heater_treater_default(API: pint.Quantity) -> bool:
    return API.to("degAPI").m < 18


@register("num_prod_wells", ["oil_sands_mine", "oil_prod"])
def num_producing_wells_default(oil_sands_mine: str, oil_prod: pint.Quantity) -> float:
    return (
        1
        if oil_sands_mine != "None"
        else max(1.0, round(oil_prod.to("bbl_oil/d").m / 87.5, 0))
    )


@register("num_water_inj_wells", ["oil_sands_mine", "oil_prod", "num_prod_wells"])
def num_water_inj_wells_default(oil_sands_mine: str, oil_prod: pint.Quantity, num_prod_wells: float) -> float:
    if oil_sands_mine != "None":
        return 0

    oil_prod_m = oil_prod.m

    if oil_prod_m <= 10:
        fraction = 0.143
    elif 10 < oil_prod_m <= 100:
        fraction = 0.267
    elif 100 < oil_prod_m <= 1000:
        fraction = 0.512
    else:
        fraction = 0.829

    return roundup(num_prod_wells * fraction, 0)


@register("HeavyOilDilution.fraction_diluent", ["oil_sands_mine", "upgrader_type"])
def fraction_diluent_default(oil_sands_mine: str, upgrader_type: str) -> float:
    return (
        0.3
        if (oil_sands_mine == "Integrated with diluent" and upgrader_type == "None")
        else 0.0
    )


@register("fraction_elec_onsite", ["offshore"])
def fraction_elec_onsite_default(offshore: int) -> float:
    return 1.0 if offshore else 0.0


@register("fraction_remaining_gas_inj", ["natural_gas_reinjection", "gas_flooding"])
def fraction_remaining_gas_inj_default(natural_gas_reinjection: int, gas_flooding: int) -> float:
    return 1.0 if gas_flooding else (0.5 if natural_gas_reinjection else 0.0)


@register("ecosystem_richness", ["offshore"])
def ecosystem_richness_default(offshore: int) -> str:
    return "Low carbon" if offshore else "Med carbon"


@register("field_development_intensity", ["offshore"])
def field_development_intensity_default(offshore: int) -> str:
    return "Low" if offshore else "Med"


@register("common_gas_process_choice", ["oil_sands_mine"])
def common_gas_process_choice_default(oil_sands_mine: str) -> str:
    return "None" if oil_sands_mine != "None" else "All"


@register("prod_water_inlet_temp", ["country"])
def prod_water_inlet_temp_default(country: str) -> pint.Quantity:
    temperature = 340 if country == "Canada" else 140
    return ureg.Quantity(temperature, "degF")


@register("num_gas_inj_wells", ["num_prod_wells"])
def num_gas_inj_wells_default(num_prod_wells: float) -> float:
    return num_prod_wells * 0.25
