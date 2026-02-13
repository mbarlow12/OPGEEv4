"""
Unit registry setup for opgee_thermo.

Initializes a pint ApplicationRegistry with custom OPGEE unit definitions
and exports the shared ``ureg`` and ``Quantity`` objects used throughout
the package.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import pint
import pint_pandas  # noqa: F401 — registers PintArray dtype with pandas
from pint import UnitRegistry

# ---------------------------------------------------------------------------
# Registry bootstrap
# ---------------------------------------------------------------------------
_ureg = pint.get_application_registry()

# Remove pint's default "bbl" so we can define barrel_oil with our aliases.
if "bbl" in _ureg:
    del _ureg._units["bbl"]

_units_path = Path(__file__).resolve().parent / "etc" / "units.txt"
_lines = _units_path.read_text().splitlines()
_ureg.load_definitions(_lines)

ureg: Final[UnitRegistry] = _ureg
"""Application-wide pint unit registry with OPGEE custom definitions."""

Q_ = ureg.Quantity
"""Shorthand for creating :class:`pint.Quantity` instances."""
