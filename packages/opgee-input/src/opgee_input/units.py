"""Pint unit infrastructure for progressive quantity annotation."""
from __future__ import annotations

from typing import Any

import pint

ureg = pint.UnitRegistry()


def _coerce_quantity(v: Any, unit: str) -> pint.Quantity:
    """Coerce a value to a pint.Quantity with the specified unit."""
    if isinstance(v, pint.Quantity):
        return v.to(unit)
    return ureg.Quantity(float(v), unit)
