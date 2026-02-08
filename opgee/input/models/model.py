"""Top-level Model for XML deserialization."""
from __future__ import annotations

from pydantic_xml import attr, element

from .analysis import AnalysisModel
from .base import OPGEEBaseModel
from .field import FieldModel


class ModelModel(OPGEEBaseModel, tag="Model", search_mode="unordered"):
    """Top-level pydantic-xml model for an OPGEE <Model> element."""
    schema_version: str | None = attr(default=None)

    analyses: list[AnalysisModel] = element(tag="Analysis", default=[])
    fields: list[FieldModel] = element(tag="Field", default=[])

    @property
    def field(self) -> FieldModel | None:
        return self.fields[0] if self.fields else None

    @property
    def analysis(self) -> AnalysisModel | None:
        return self.analyses[0] if self.analyses else None
