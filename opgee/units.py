import logging
from importlib.resources import files
from typing import Final, Optional

import pint
from pint.registry import ApplicationRegistry

from opgee.error import OpgeeException

_logger = logging.getLogger(__name__)

_ureg: Optional[ApplicationRegistry] = None

if _ureg is None:
    _ureg = pint.get_application_registry()
    del _ureg._units["bbl"]
    units_path = files("opgee.etc").joinpath("units.txt")
    lines = [line.strip() for line in units_path.read_text().splitlines()]
    _ureg.load_definitions(lines)

ureg: Final[ApplicationRegistry] = _ureg
del _ureg

# to avoid redundantly reporting bad units
_undefined_units = {}

def validate_unit(unit):
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


def magnitude(value, units=None):
    """
    Return the magnitude of ``value``. If ``value`` is a ``pint.Quantity`` and
    ``units`` is not None, check that ``value`` has the expected units and
    return the magnitude of ``value``. If ``value`` is not a ``pint.Quantity``,
    just return it.

    :param value: (float or pint.Quantity) the value for which we return the magnitude.
    :param units: (None or pint.Unit) the expected units
    :return: the magnitude of `value`
    """
    if isinstance(value, ureg.Quantity):
        # if optional units are provided, validate them
        if units:
            if not isinstance(units, pint.Unit):
                units = ureg.Unit(units)
            if value.units != units:
                raise OpgeeException(f"magnitude: value {value} units are not {units}")

        return value.m
    else:
        return value
