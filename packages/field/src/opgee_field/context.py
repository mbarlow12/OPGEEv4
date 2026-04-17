"""
FieldContext and supporting configuration dataclasses.

FieldContext is injected into Process and Stream instances. It carries
shared infrastructure only — no physical parameters. Physical params
are passed directly to Process/Stream constructors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .core import TemperaturePressure
from .table_manager import TableManager


@dataclass(frozen=True)
class GWPData:
    """Immutable global warming potentials."""
    values: pd.Series
    horizon: int


@dataclass(frozen=True)
class SimulationParams:
    """Immutable iteration/convergence settings."""
    maximum_iterations: int
    maximum_change: float


@dataclass
class FieldContext:
    """Injected into Process and Stream instances.

    Contains shared infrastructure only. Physical parameters (api, gor,
    res_press, etc.) are explicit constructor args on the classes that
    use them.

    process_data is intentionally mutable — it's the inter-process
    communication bulletin board (23+ call sites).
    """
    stp: TemperaturePressure
    tables: TableManager
    gwp: GWPData
    simulation: SimulationParams
    process_data: dict[str, Any] = field(default_factory=dict)
