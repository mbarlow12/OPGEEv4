"""Stream input dataclasses."""
from __future__ import annotations

from dataclasses import field as dc_field

from .base import OPGEEInput, opgee_dataclass


@opgee_dataclass
class ContainsSpec(OPGEEInput):
    """Declares what a stream contains."""

    value: str | None = None
    delete: bool | None = None


@opgee_dataclass
class StreamInput(OPGEEInput):
    """A material/energy flow connection between processes."""

    src: str
    dst: str
    name: str | None = None
    impute: bool | None = None
    boundary: str | None = None
    delete: bool | None = None
    contains: list[ContainsSpec] = dc_field(default_factory=list)
