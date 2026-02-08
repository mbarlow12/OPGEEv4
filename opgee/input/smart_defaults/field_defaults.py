"""Smart default functions for Field attributes.

These are the 18 Field-scoped defaults, adapted from opgee/input/xml/defaults.py
to operate on pydantic model values instead of lxml elements.

Note: dependency values are plain Python types (float, int, str),
not pint.Quantity. The smart default registry resolves values directly
from model attributes. Functions that previously used pint.Quantity
now take plain floats and handle unit conversion internally.
"""
from __future__ import annotations

from math import exp

from opgee.input.smart_defaults import register
from opgee.utils import roundup


@register("SOR", ["steam_flooding"])
def SOR_default(steam_flooding: int) -> float:
    return 3.0 if steam_flooding else 1.0


@register("WOR", ["steam_flooding", "age", "SOR"])
def WOR_default(steam_flooding: int, age: float, SOR: float) -> float:
    if steam_flooding:
        return SOR
    tmp = 4.021 * exp(0.024 * age) - 4.021
    return min(tmp, 100.0)


@register("GOR", ["API"])
def GOR_default(API: float) -> float:
    if API < 20:
        return 1122.4
    elif 20 <= API <= 30:
        return 1205.4
    else:
        return 2429.3


@register("WIR", ["WOR"])
def WIR_default(WOR: float) -> float:
    return WOR + 1


@register("stabilizer_column", ["GOR", "gas_lifting", "oil_sands_mine"])
def stabilizer_default(GOR: float, gas_lifting: int, oil_sands_mine: str) -> int:
    return 0 if (oil_sands_mine != "None") or (not gas_lifting and GOR <= 500) else 1


@register("GFIR", ["flood_gas_type", "GOR"])
def GFIR_default(flood_gas_type: str, GOR: float) -> float:
    if flood_gas_type == "NG":
        return 1.5 * GOR
    elif flood_gas_type == "N2":
        return 1200.0
    elif flood_gas_type == "CO2":
        return 10000.0
    else:
        return 1.5 * GOR


@register("depth", ["GOR"])
def depth_default(GOR: float) -> float:
    gas_field_default_depth = 8285.0
    return gas_field_default_depth if GOR > 10000 else 7122.0


@register("res_press", ["country", "depth", "steam_flooding"])
def res_press_default(country: str, depth: float, steam_flooding: int) -> float:
    return 100.0 if (country == "California" and steam_flooding) else 0.5 * depth * 0.43


@register("res_temp", ["depth"])
def res_temp_default(depth: float) -> float:
    return 70 + 1.8 * depth / 100.0


@register("num_prod_wells", ["oil_sands_mine", "oil_prod"])
def num_producing_wells_default(oil_sands_mine: str, oil_prod: float) -> int:
    if oil_sands_mine != "None":
        return 1
    return max(1, round(oil_prod / 87.5))


@register("num_water_inj_wells", ["oil_sands_mine", "oil_prod", "num_prod_wells"])
def num_water_inj_wells_default(oil_sands_mine: str, oil_prod: float, num_prod_wells: int) -> int:
    if oil_sands_mine != "None":
        return 0

    if oil_prod <= 10:
        fraction = 0.143
    elif oil_prod <= 100:
        fraction = 0.267
    elif oil_prod <= 1000:
        fraction = 0.512
    else:
        fraction = 0.829

    return int(roundup(num_prod_wells * fraction, 0))


@register("num_gas_inj_wells", ["num_prod_wells"])
def num_gas_inj_wells_default(num_prod_wells: int) -> int:
    return int(num_prod_wells * 0.25)


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
def prod_water_inlet_temp_default(country: str) -> float:
    return 340.0 if country == "Canada" else 140.0
