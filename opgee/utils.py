"""General-purpose utility functions."""
import logging

from .error import OpgeeException

_logger = logging.getLogger(__name__)


def coercible(value, type_fn, default=None):
    """Attempt to coerce `value` using `type_fn`, return `default` on failure."""
    try:
        return type_fn(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    return coercible(value, int, default=default)


def binary(value, default=None):
    return coercible(value, lambda v: int(float(v)), default=default)


def parse_boolean(value):
    """Parse string to boolean. Replaces getBooleanXML."""
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ('1', 'true', 'yes'):
        return True
    if s in ('0', 'false', 'no'):
        return False
    raise OpgeeException(f"Cannot convert '{value}' to boolean")


def getFuncName(level=1):
    """Return the name of the calling function."""
    import inspect
    return inspect.stack()[level][3]


def roundup(value, nearest):
    """Round `value` up to the nearest multiple of `nearest`."""
    return int(nearest * ((value + nearest - 1) // nearest))


def flatten(lst):
    """Flatten a list of lists into a single list."""
    return [item for sublist in lst for item in sublist]


def dequantify_dataframe(df):
    """Remove pint units from a DataFrame's values."""
    return df.apply(lambda col: col.pint.magnitude if hasattr(col, 'pint') else col)


# Deprecated alias (removed in a later phase; retained here while callers are migrated)
getBooleanXML = parse_boolean
