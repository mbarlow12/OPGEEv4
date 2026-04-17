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


class TemperaturePressure:
    """Stores temperature and pressure together for convenience."""
    __slots__ = ('T', 'P')

    def __init__(self, T, P):
        self.T = None
        self.P = None
        self.set(T=T, P=P)

    def __str__(self):
        return f"<T={self.T} P={self.P}>"

    def set(self, T=None, P=None):
        if T is None and P is None:
            return
        if T is not None:
            self.T = T if isinstance(T, pint.Quantity) else ureg.Quantity(float(T), "degF")
        if P is not None:
            self.P = P if isinstance(P, pint.Quantity) else ureg.Quantity(float(P), "psia")

    def get(self):
        return (self.T, self.P)

    def copy_from(self, tp):
        self.set(T=tp.T, P=tp.P)


std_temperature = ureg.Quantity(60.0, "degF")
std_pressure    = ureg.Quantity(14.676, "psia")
STP = TemperaturePressure(std_temperature, std_pressure)


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
        self.stop_time  = None

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
