"""Base class and decorator for all OPGEE input dataclasses."""
from __future__ import annotations

import functools

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass as _pydantic_dataclass

_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)


def opgee_dataclass(cls: type) -> type:
    """Apply pydantic dataclass with standard config and track fields_set.

    Wraps ``__init__`` so that the set of keyword arguments explicitly
    passed at construction time is stored in ``_fields_set``, accessible
    via the ``model_fields_set`` property.
    """
    cls = _pydantic_dataclass(config=_config, kw_only=True)(cls)
    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def _tracking_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        object.__setattr__(self, "_fields_set", set(kwargs.keys()))

    cls.__init__ = _tracking_init
    return cls


class OPGEEInput:
    """Base for all OPGEE input dataclasses.

    Provides a ``model_fields_set`` compatibility shim so callers can
    detect which fields were explicitly provided at construction time.
    """

    @property
    def model_fields_set(self) -> set[str]:
        """Return the set of field names explicitly passed to __init__."""
        return getattr(self, "_fields_set", set())
