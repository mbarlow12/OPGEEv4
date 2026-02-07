"""Stage 1: Apply static defaults — insert missing <A> elements with default values."""

from copy import deepcopy
from typing import Any

import pint
from lxml import etree

from opgee.attributes import AttrDefs


def apply_static_defaults(root: etree.Element) -> etree.Element:
    """
    For each class-bearing element (Field, Analysis, each Process), look up
    its ClassAttrs from AttrDefs and insert missing <A> elements with defaults.

    Existing <A> elements are marked explicit="true". New default <A> elements
    are marked explicit="false".

    :param root: <Model> lxml Element
    :return: a new Element with all defaults applied (input is not modified)
    """
    root = deepcopy(root)
    attr_defs = AttrDefs.get_instance()

    field_elt = root.find("Field")
    if field_elt is not None:
        _apply_defaults_to_element(field_elt, "Field", attr_defs)

    analysis_elt = root.find("Analysis")
    if analysis_elt is not None:
        _apply_defaults_to_element(analysis_elt, "Analysis", attr_defs)

    if field_elt is not None:
        for proc_elt in field_elt.findall("Process"):
            class_name = proc_elt.get("class")
            if class_name:
                _apply_defaults_to_element(proc_elt, class_name, attr_defs, is_process=True)

    return root


def _apply_defaults_to_element(elt: etree.Element, class_name: str,
                               attr_defs: AttrDefs, is_process: bool = False) -> None:
    """
    Insert missing <A> elements with default values for a single element.

    :param elt: the lxml Element to add defaults to
    :param class_name: class name for AttrDef lookup
    :param attr_defs: the AttrDefs singleton
    :param is_process: True if this is a Process element (also inherits base Process attrs)
    """
    # Collect existing attribute names and mark them explicit
    existing_names: set[str] = set()
    for a_elt in elt.findall("A"):
        name = a_elt.get("name")
        if name:
            existing_names.add(name)
            if a_elt.get("explicit") is None:
                a_elt.set("explicit", "true")

    # Build combined attr dict: Process base + subclass for processes
    combined_dict: dict[str, Any] = {}

    if is_process:
        process_attrs = attr_defs.class_attrs("Process", raiseError=False)
        if process_attrs:
            combined_dict.update(process_attrs.attr_dict)

    class_attrs = attr_defs.class_attrs(class_name, raiseError=False)
    if class_attrs:
        combined_dict.update(class_attrs.attr_dict)

    # Add missing defaults
    for name, attr_def in combined_dict.items():
        if name not in existing_names and attr_def.default is not None:
            default_str = _default_to_str(attr_def.default)
            a_elt = etree.SubElement(elt, "A", name=name, explicit="false")
            a_elt.text = default_str


def _default_to_str(default: Any) -> str:
    """Convert a default value to string, extracting magnitude from pint Quantities."""
    if isinstance(default, pint.Quantity):
        return str(default.magnitude)
    return str(default)
