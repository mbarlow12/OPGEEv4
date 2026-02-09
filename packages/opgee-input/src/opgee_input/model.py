"""Top-level Model input dataclass."""
from __future__ import annotations

from dataclasses import field as dc_field

from .analysis import AnalysisInput
from .base import OPGEEInput, opgee_dataclass
from .field import FieldInput


@opgee_dataclass
class ModelInput(OPGEEInput):
    """Top-level input specification for an OPGEE Model."""

    schema_version: str | None = None
    analyses: list[AnalysisInput] = dc_field(default_factory=list)
    fields: list[FieldInput] = dc_field(default_factory=list)

    @property
    def field(self) -> FieldInput | None:
        return self.fields[0] if self.fields else None

    @property
    def analysis(self) -> AnalysisInput | None:
        return self.analyses[0] if self.analyses else None
