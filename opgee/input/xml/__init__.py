"""
Functional XML processing pipeline for OPGEE model files.

Transforms raw lxml Elements through a series of pure-functional stages:
  0. Load AttrDefs — initialize attribute metadata singleton
  1. Static Defaults — insert missing <A> elements with default values
  2. Smart Defaults — compute dependent attribute values
  3. Process Choices — resolve ProcessChoice elements, remove disabled procs/streams
  4. Build Objects — construct lightweight model objects from clean XML
"""

from .builders import BuiltModel
from .loader import load_attr_defs
from .static_defaults import apply_static_defaults
from .smart_defaults import apply_smart_defaults
from .process_choices import resolve_process_choices
from .builders import build_model


def process_field_xml(model_elt, attr_defs_elt) -> BuiltModel:
    """
    Run the full XML processing pipeline.

    :param model_elt: lxml Element for <Model> containing one <Field> and one <Analysis>
    :param attr_defs_elt: lxml Element for <AttrDefs> containing attribute metadata
    :return: BuiltModel with typed attribute dicts and process/stream lists
    """
    load_attr_defs(attr_defs_elt)
    apply_static_defaults(model_elt)
    apply_smart_defaults(model_elt)
    resolve_process_choices(model_elt)
    return build_model(model_elt)
