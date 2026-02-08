"""Smart default functions for Process-scoped attributes."""
from __future__ import annotations

from opgee.input.smart_defaults import register


@register("CrudeOilDewatering.heater_treater", ["API"])
def heater_treater_default(API: float) -> int:
    return 1 if API < 18 else 0


@register("HeavyOilDilution.fraction_diluent", ["oil_sands_mine", "upgrader_type"])
def fraction_diluent_default(oil_sands_mine: str, upgrader_type: str) -> float:
    return (
        0.3
        if (oil_sands_mine == "Integrated with diluent" and upgrader_type == "None")
        else 0.0
    )
