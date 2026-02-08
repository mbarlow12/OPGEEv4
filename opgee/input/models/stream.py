"""Stream model for XML deserialization."""
from __future__ import annotations

from pydantic_xml import attr, element

from .base import OPGEEBaseModel


class ContainsElement(OPGEEBaseModel, tag="Contains"):
    """Declares what a stream contains."""
    value: str | None = None
    delete: bool | None = attr(default=None)


class StreamModel(OPGEEBaseModel, tag="Stream", search_mode="unordered"):
    """A material/energy flow connection between processes."""
    src: str = attr()
    dst: str = attr()
    name: str | None = attr(default=None)
    impute: bool | None = attr(default=None)
    boundary: str | None = attr(default=None)
    delete: bool | None = attr(default=None)
    contains: list[ContainsElement] = element(tag="Contains", default=[])
