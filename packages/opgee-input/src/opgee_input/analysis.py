"""Analysis input dataclass."""
from __future__ import annotations

from typing import Literal

from .base import OPGEEInput, opgee_dataclass


@opgee_dataclass
class AnalysisInput(OPGEEInput):
    """Input specification for an Analysis element."""

    name: str
    GWP_horizon: Literal["20", "100"] | None = None
    GWP_version: Literal["AR4", "AR5", "AR5_CCF", "AR6"] | None = None
    functional_unit: Literal["oil", "gas"] | None = None
    boundary: Literal["Production", "Transportation", "Distribution", "Refinery"] | None = None
