"""Analysis model for XML deserialization."""
from __future__ import annotations

from typing import Literal

from pydantic_xml import attr, element

from .base import OPGEEBaseModel


class GroupElement(OPGEEBaseModel, tag="Group"):
    """A group selector within an Analysis.

    Text content is the group name (literal match) or regex pattern.
    When ``regex="1"`` or ``regex="true"``, the text is compiled as a
    regular expression and matched against a Field's ``group`` attribute.
    """
    regex: bool = attr(default=False)
    text: str | None = None


class AnalysisModel(OPGEEBaseModel, tag="Analysis", search_mode="unordered"):
    """Pydantic-xml model for an Analysis element."""
    name: str = attr()

    GWP_horizon: Literal["20", "100"] | None = element(tag="GWP_horizon", default=None)
    GWP_version: Literal["AR4", "AR5", "AR5_CCF", "AR6"] | None = element(tag="GWP_version", default=None)
    functional_unit: Literal["oil", "gas"] | None = element(tag="functional_unit", default=None)
    boundary: Literal["Production", "Transportation", "Distribution", "Refinery"] | None = element(tag="boundary", default=None)

    groups: list[GroupElement] = element(tag="Group", default=[])
