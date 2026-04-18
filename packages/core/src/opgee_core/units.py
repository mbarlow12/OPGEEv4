import logging
import os
from pathlib import Path
from typing import Final

import pint
from pint.facets.plain import PlainQuantity
import pint_pandas  # noqa: F401 # pyright: ignore[reportUnusedImport] (registers pandas extension dtype for pint[unit])
from pint.registry import UnitRegistry, Unit

from .error import OpgeeException

_logger = logging.getLogger(__name__)

type ScalarValue = int | float
type OPGEEUnitRegistry = UnitRegistry[ScalarValue]

_ureg: UnitRegistry[int | float] | None = None

if _ureg is None:
    units_path = Path(os.path.dirname(__file__)) / "etc" / "units.txt"
    _ureg = UnitRegistry(filename=str(units_path))

ureg: Final[UnitRegistry[int | float]] = _ureg
del _ureg

OpgeeQ_ = ureg.Quantity[ScalarValue]


# to avoid redundantly reporting bad units
_undefined_units = {}


def validate_unit(unit: str) -> Unit | None:
    """
    Return the ``pint.Unit`` associated with the string ``unit``, or ``None``
    if ``unit`` is ``None`` or not in the unit registry.

    :param unit: (str) a string representation of a ``pint.Unit``

    :return: (pint.Unit or None)
    """
    if not unit:
        return None

    if unit in ureg:
        return ureg.Unit(unit)

    if unit not in _undefined_units:
        _logger.warning(f"Unit '{unit}' is not in the UnitRegistry")
        _undefined_units[unit] = 1

    return None


def magnitude(
    value: PlainQuantity[ScalarValue] | ScalarValue, units: Unit | None = None
) -> ScalarValue:
    """
    Return the magnitude of ``value``. If ``value`` is a ``pint.Quantity`` and
    ``units`` is not None, check that ``value`` has the expected units and
    return the magnitude of ``value``. If ``value`` is not a ``pint.Quantity``,
    just return it.

    :param value: (float or pint.Quantity) the value for which we return the magnitude.
    :param units: (None or pint.Unit) the expected units
    :return: the magnitude of `value`
    """
    if isinstance(value, PlainQuantity):
        # if optional units are provided, validate them
        if units:
            if not isinstance(units, pint.Unit):
                units = ureg.Unit(units)
            if value.units != units:
                raise OpgeeException(f"magnitude: value {value} units are not {units}")

        return value.m
    else:
        return value
