#
# OPGEE XML Adapters
#
# Attribute handling functions without AttributeMixin dependency
# Part of XML/Core package separation refactoring
#
# Author: Refactoring Team
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#

from __future__ import annotations

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from xml.etree.ElementTree import Element

from opgee.common import elt_name
from opgee.core.error import AttributeError, ModelValidationError, OpgeeException
from opgee.core.log import getLogger
from opgee.core.units import ureg, validate_unit, magnitude
from opgee.utils import coercible

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from opgee.xml.attributes import AttrDef, AttrDefs

_logger = getLogger(__name__)


def parse_attributes_from_xml(
    element: Element, class_name: str, is_process: bool = False
) -> Dict[str, Any]:
    """
    Parse XML attributes without using AttributeMixin.

    Replaces the AttributeMixin.instantiate_attrs class method functionality.

    :param element: XML element containing A child elements
    :param class_name: Name of the class for attribute lookup
    :param is_process: Whether this is a Process subclass
    :return: Dictionary mapping attribute names to Attribute objects
    """
    # Import here to avoid circular dependencies
    from opgee.xml.attributes import AttrDefs

    attr_dict = {}
    attr_defs = AttrDefs.get_instance()

    # Get attribute definitions for this class
    process_attrs = attr_defs.classes.get("Process") if is_process else None
    class_attrs = attr_defs.class_attrs(class_name, raiseError=False)

    if not (class_attrs or process_attrs):
        return attr_dict

    # Create dictionary of explicit values from XML A elements
    user_values = {elt_name(a): a.text for a in element.findall("A")}

    # Process class-specific attributes
    if class_attrs:
        for attr_def in class_attrs.values():
            attr_name = attr_def.name
            value = user_values.get(attr_name, attr_def.default)
            if value is not None:
                attr_obj = create_attribute_from_def(attr_def, value)
                attr_dict[attr_name] = attr_obj

    # Process inherited Process attributes if this is a process
    if process_attrs and is_process:
        for attr_def in process_attrs.values():
            attr_name = attr_def.name
            if attr_name not in attr_dict:  # Don't override class-specific attrs
                value = user_values.get(attr_name, attr_def.default)
                if value is not None:
                    attr_obj = create_attribute_from_def(attr_def, value)
                    attr_dict[attr_name] = attr_obj

    return attr_dict


def create_attribute_from_def(attr_def: AttrDef, value: Any) -> Attribute:
    """
    Create an Attribute object from an AttrDef and value.

    :param attr_def: Attribute definition
    :param value: Attribute value (string from XML or default)
    :return: Attribute object
    """
    # Convert string value to appropriate Python type
    if attr_def.pytype:
        try:
            if attr_def.pytype == bool:
                typed_value = coercible(value, bool)
            elif attr_def.pytype == int:
                typed_value = coercible(value, int)
            elif attr_def.pytype == float:
                typed_value = coercible(value, float)
            else:
                typed_value = coercible(value, attr_def.pytype)
        except (ValueError, TypeError) as e:
            raise AttributeError(
                f"Cannot convert '{value}' to type {attr_def.pytype.__name__} for attribute {attr_def.name}: {e}"
            )
    else:
        typed_value = value

    # Handle units if specified
    if attr_def.unit:
        try:
            # Validate unit and create Quantity
            validate_unit(attr_def.unit)
            if isinstance(typed_value, (int, float)):
                typed_value = ureg.Quantity(typed_value, attr_def.unit)
        except Exception as e:
            raise AttributeError(
                f"Invalid unit '{attr_def.unit}' for attribute {attr_def.name}: {e}"
            )

    # Create Attribute object
    attr_obj = Attribute(attr_def.name, typed_value, attr_def)

    # Validate constraints if present
    if attr_def.constraints:
        validate_attribute_constraints(attr_obj, attr_def.constraints)

    return attr_obj


def validate_attribute_constraints(
    attr_obj: Attribute, constraints: Dict[str, Any]
) -> None:
    """
    Validate attribute value against constraints.

    :param attr_obj: Attribute object to validate
    :param constraints: Dictionary of constraint name to value
    :raises AttributeError: If constraints are violated
    """
    value = attr_obj.value

    # Handle quantity values
    if hasattr(value, "magnitude"):
        numeric_value = value.magnitude
    else:
        numeric_value = value

    # Validate numeric constraints
    if "GT" in constraints and numeric_value <= constraints["GT"]:
        raise AttributeError(
            f"Attribute {attr_obj.name} value {numeric_value} must be > {constraints['GT']}"
        )

    if "GE" in constraints and numeric_value < constraints["GE"]:
        raise AttributeError(
            f"Attribute {attr_obj.name} value {numeric_value} must be >= {constraints['GE']}"
        )

    if "LT" in constraints and numeric_value >= constraints["LT"]:
        raise AttributeError(
            f"Attribute {attr_obj.name} value {numeric_value} must be < {constraints['LT']}"
        )

    if "LE" in constraints and numeric_value > constraints["LE"]:
        raise AttributeError(
            f"Attribute {attr_obj.name} value {numeric_value} must be <= {constraints['LE']}"
        )


def extract_xml_element_attributes(element: Element) -> Dict[str, str]:
    """
    Extract XML element attributes (not A child elements).

    :param element: XML element
    :return: Dictionary of attribute name to string value
    """
    return dict(element.attrib)


def parse_boolean_xml_attr(
    element: Element, attr_name: str, default: bool = False
) -> bool:
    """
    Parse a boolean attribute from XML element attributes.

    :param element: XML element
    :param attr_name: Attribute name
    :param default: Default value if attribute not present
    :return: Boolean value
    """
    value = element.get(attr_name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def parse_optional_attr(
    element: Element, attr_name: str, attr_type: type = str, default: Any = None
) -> Any:
    """
    Parse an optional attribute from XML element with type conversion.

    :param element: XML element
    :param attr_name: Attribute name
    :param attr_type: Type to convert to
    :param default: Default value if attribute not present
    :return: Converted attribute value or default
    """
    value = element.get(attr_name)
    if value is None:
        return default

    try:
        return coercible(value, attr_type)
    except (ValueError, TypeError) as e:
        raise AttributeError(
            f"Cannot convert attribute '{attr_name}' value '{value}' to {attr_type.__name__}: {e}"
        )


class Attribute:
    """
    Standalone Attribute class to replace AttributeMixin functionality.

    Represents a single attribute with its value, definition, and constraints.
    """

    def __init__(self, name: str, value: Any, attr_def: Optional[AttrDef] = None):
        self.name = name
        self._value = value
        self.attr_def = attr_def

    @property
    def value(self) -> Any:
        """Get the attribute value."""
        return self._value

    def set_value(self, value: Any) -> None:
        """
        Set the attribute value with validation.

        :param value: New value to set
        :raises AttributeError: If value is invalid
        """
        # Type conversion if attr_def specifies a type
        if self.attr_def and self.attr_def.pytype:
            try:
                converted_value = coercible(value, self.attr_def.pytype)
            except (ValueError, TypeError) as e:
                raise AttributeError(
                    f"Cannot convert '{value}' to type {self.attr_def.pytype.__name__} for attribute {self.name}: {e}"
                )
        else:
            converted_value = value

        # Unit handling
        if self.attr_def and self.attr_def.unit:
            if isinstance(converted_value, (int, float)):
                converted_value = ureg.Quantity(converted_value, self.attr_def.unit)

        # Constraint validation
        if self.attr_def and self.attr_def.constraints:
            temp_attr = Attribute(self.name, converted_value, self.attr_def)
            validate_attribute_constraints(temp_attr, self.attr_def.constraints)

        self._value = converted_value

    def __str__(self) -> str:
        return f"Attribute({self.name}={self.value})"

    def __repr__(self) -> str:
        return self.__str__()


class SimpleAttributeContainer:
    """
    Simple container for attributes without complex mixin inheritance.

    Provides basic attribute access functionality to replace AttributeMixin
    in core classes during the transition.
    """

    def __init__(self, attr_dict: Optional[Dict[str, Attribute]] = None):
        self.attr_dict = attr_dict or {}

    def _get_attr(self, attr_name: str) -> Attribute:
        """Get attribute object by name."""
        try:
            return self.attr_dict[attr_name]
        except KeyError:
            raise AttributeError(f"Attribute '{attr_name}' not found")

    def attr(self, attr_name: str) -> Any:
        """Get attribute value by name."""
        attr_obj = self._get_attr(attr_name)
        return attr_obj.value

    def set_attr(self, attr_name: str, value: Any) -> None:
        """Set attribute value by name."""
        attr_obj = self._get_attr(attr_name)
        attr_obj.set_value(value)

    def has_attr(self, attr_name: str) -> bool:
        """Check if attribute exists."""
        return attr_name in self.attr_dict

    def attrs_with_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get all attributes with given prefix."""
        return {
            name: attr.value
            for name, attr in self.attr_dict.items()
            if name.startswith(prefix)
        }

