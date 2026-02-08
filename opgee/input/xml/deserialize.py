"""Deserialize lxml elements to pydantic-xml models."""
from __future__ import annotations

from lxml import etree

from opgee.input.models.field import FieldModel
from opgee.input.models.model import ModelModel


def deserialize_field(field_elt: etree._Element) -> FieldModel:
    """Convert a resolved lxml Field element to a FieldModel.

    Uses search_mode='unordered' on FieldModel, so no pre-sorting needed.
    """
    return FieldModel.from_xml_tree(field_elt)


def deserialize_model(root: etree._Element) -> ModelModel:
    """Convert a resolved lxml Model element to a ModelModel."""
    return ModelModel.from_xml_tree(root)
