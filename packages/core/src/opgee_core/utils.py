"""Core OPGEE base classes and physical constants."""

import datetime
import time

import pint

from .error import OpgeeException
from .units import ureg


class OpgeeObject:
    """Minimal base class — provides name and string representation."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


def dict_from_list(objs):
    """
    Build a name-keyed dict from named objects; raises on duplicate names.

    :param objs: (list of named objects) the objects to create dict from.
    :return: (dict) objects keyed by name
    :raises: OpgeeException if any name is repeated
    """
    d = {}
    for obj in objs:
        name = obj.name
        if name in d:
            raise OpgeeException(f"Duplicate name '{name}'")
        d[name] = obj
    return d


class Timer:
    def __init__(self, feature_name, start=True):
        self.feature_name = feature_name
        self.start_time = None
        self.stop_time = None

        if start:
            self.start()

    def start(self):
        self.start_time = time.time()
        return self

    def stop(self):
        self.stop_time = time.time()
        return self

    def duration(self):
        seconds = self.stop_time - self.start_time
        return datetime.timedelta(seconds=int(seconds))

    def __str__(self):
        if self.start_time is None:
            status = "is uninitialized"
        elif self.stop_time is None:
            status = "is running"
        else:
            status = f"completed in {self.duration()}"
        return f"<Timer '{self.feature_name}' {status}>"


from .error import OpgeeException


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
    if s in ("1", "true", "yes"):
        return True
    if s in ("0", "false", "no"):
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
    return df.apply(lambda col: col.pint.magnitude if hasattr(col, "pint") else col)


# Deprecated alias (removed in a later phase; retained here while callers are migrated)
getBooleanXML = parse_boolean
