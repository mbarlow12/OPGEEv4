"""Analysis input dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type GwpHorizon = Literal[20, 40]


@dataclass(frozen=True)
class AnalysisInput:
    """Input specification for an Analysis element."""

    name: str
    GWP_horizon: Literal["20", "100"] | None = None
    GWP_version: Literal["AR4", "AR5", "AR5_CCF", "AR6"] | None = None
    functional_unit: Literal["oil", "gas"] | None = None
    boundary: (
        Literal["Production", "Transportation", "Distribution", "Refinery"] | None
    ) = None
