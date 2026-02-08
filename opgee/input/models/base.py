"""Base model for all OPGEE pydantic-xml models."""
from __future__ import annotations

from pydantic import ConfigDict
from pydantic_xml import BaseXmlModel


class OPGEEBaseModel(BaseXmlModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)
