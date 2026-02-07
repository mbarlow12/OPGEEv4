"""
Functional XML processing pipeline for OPGEE model files.

Transforms raw lxml Elements through a series of pure-functional stages:
  0. Load AttrDefs — initialize attribute metadata singleton
  1. Static Defaults — insert missing <A> elements with default values
  2. Smart Defaults — compute dependent attribute values
  3. Process Choices — resolve ProcessChoice elements, remove disabled procs/streams
  4. Build Objects — construct lightweight model objects from clean XML
"""

from lxml import etree

from .builders import BuiltModel, build_model
from .loader import load_attr_defs
from .models import ExtModel
from .static_defaults import apply_static_defaults
from .smart_defaults import apply_smart_defaults
from .process_choices import resolve_process_choices


def process_field_xml(model_elt: etree.Element, attr_defs_elt: etree.Element) -> BuiltModel:
    """
    Run the full XML processing pipeline.

    :param model_elt: lxml Element for <Model> containing one <Field> and one <Analysis>
    :param attr_defs_elt: lxml Element for <AttrDefs> containing attribute metadata
    :return: BuiltModel with typed attribute dicts and process/stream lists
    """
    # Validate input structure (raises ValidationError on failure)
    ExtModel.from_xml_tree(model_elt)

    load_attr_defs(attr_defs_elt)
    model_elt = apply_static_defaults(model_elt)
    model_elt = apply_smart_defaults(model_elt)
    model_elt = resolve_process_choices(model_elt)

    # Validates output structure via CoreModel, then builds BuiltModel
    return build_model(model_elt)
