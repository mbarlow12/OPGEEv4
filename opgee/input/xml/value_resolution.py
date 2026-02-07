"""Shared value resolution layer for reading/writing typed values from lxml <A> elements."""

from typing import Any

from lxml import etree

from opgee.attributes import AttrDefs, AttrDef
from opgee.units import ureg, validate_unit
from opgee.utils import coercible


def get_attr_def(class_name: str, attr_name: str) -> AttrDef | None:
    """
    Look up an AttrDef from the AttrDefs singleton.

    For Process subclasses, falls back to the base 'Process' ClassAttrs
    if the attr isn't found in the subclass.

    :param class_name: class name (e.g. 'Field', 'Analysis', 'Separation')
    :param attr_name: attribute name
    :return: AttrDef or None
    """
    attr_defs = AttrDefs.get_instance()
    if attr_defs is None:
        return None

    class_attrs = attr_defs.class_attrs(class_name, raiseError=False)

    if class_attrs:
        attr_def = class_attrs.attr_dict.get(attr_name)
        if attr_def:
            return attr_def

    # Fall back to Process base class attrs
    process_attrs = attr_defs.class_attrs("Process", raiseError=False)
    if process_attrs:
        return process_attrs.attr_dict.get(attr_name)

    return None


def read_attr_value(elt: etree.Element, attr_name: str, class_name: str) -> Any:
    """
    Read a typed value from an <A> child element.

    Finds <A name="attr_name"> under elt, looks up AttrDef for type/unit info,
    coerces the text value, and wraps in pint.Quantity if unit is defined.

    :param elt: parent lxml Element containing <A> children
    :param attr_name: the attribute name to read
    :param class_name: class name for AttrDef lookup
    :return: typed value (int, float, str, pint.Quantity, etc.)
    """
    a_elt = _find_a_element(elt, attr_name)
    if a_elt is None:
        raise ValueError(f"Attribute '{attr_name}' not found under <{elt.tag}>")

    text = a_elt.text
    if text is None:
        return None

    attr_def = get_attr_def(class_name, attr_name)
    if attr_def is None:
        return text

    return _coerce_value(text, attr_def)


def write_attr_value(elt: etree.Element, attr_name: str, value: Any,
                     explicit: bool = False) -> None:
    """
    Write a typed value back to an <A> element, creating it if necessary.

    Extracts magnitude from pint.Quantity values before converting to string.

    :param elt: parent lxml Element
    :param attr_name: attribute name
    :param value: typed value to write
    :param explicit: whether to mark the attribute as explicit
    """
    import pint

    if isinstance(value, pint.Quantity):
        text = str(value.magnitude)
    elif isinstance(value, bool):
        text = "1" if value else "0"
    else:
        text = str(value)

    a_elt = _find_a_element(elt, attr_name)
    if a_elt is None:
        a_elt = etree.SubElement(elt, "A", name=attr_name)

    a_elt.text = text
    a_elt.set("explicit", "true" if explicit else "false")


def _find_a_element(elt: etree.Element, attr_name: str) -> etree.Element | None:
    """Find <A name="attr_name"> child element."""
    for a in elt.findall("A"):
        if a.get("name") == attr_name:
            return a
    return None


def _coerce_value(text: str, attr_def: AttrDef) -> Any:
    """Coerce text to the type and unit specified by attr_def."""
    value: Any = text

    if attr_def.pytype:
        value = coercible(text, attr_def.pytype)

    unit_obj = validate_unit(attr_def.unit)
    if unit_obj is not None:
        value = ureg.Quantity(float(value), unit_obj)

    return value
