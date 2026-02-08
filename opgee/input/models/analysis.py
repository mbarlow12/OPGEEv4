"""Analysis model for XML deserialization."""
from __future__ import annotations

from typing import Literal

from pydantic_xml import attr, element

from .base import OPGEEBaseModel


class FieldRefElement(OPGEEBaseModel, tag="FieldRef"):
    """A reference to a field by name within an analysis."""
    name: str = attr()


class AnalysisModel(OPGEEBaseModel, tag="Analysis", search_mode="unordered"):
    """Pydantic-xml model for an Analysis element."""
    name: str = attr()

    GWP_horizon: Literal["20", "100"] | None = element(tag="GWP_horizon", default=None)
    GWP_version: Literal["AR4", "AR5", "AR5_CCF", "AR6"] | None = element(tag="GWP_version", default=None)
    functional_unit: Literal["oil", "gas"] | None = element(tag="functional_unit", default=None)
    boundary: Literal["Production", "Transportation", "Distribution", "Refinery"] | None = element(tag="boundary", default=None)

    field_refs: list[FieldRefElement] = element(tag="FieldRef", default=[])
