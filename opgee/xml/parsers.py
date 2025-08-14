#
# OPGEE XML Parsers
#
# Standalone functions to replace from_xml class methods
# Part of XML/Core package separation refactoring
#
# Author: Refactoring Team
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#

from __future__ import annotations
from functools import lru_cache
from typing import (
    Literal,
    Optional,
    TYPE_CHECKING,
    Callable,
    TypeGuard,
    TypeVar,
    TypeAlias,
    overload,
)

# from lxml.etree import _Element as Element
from lxml import etree

# Import utilities needed for XML parsing
from opgee.common import elt_name, TemperaturePressure
from opgee.core.error import OpgeeException, ModelValidationError
from opgee.core.log import getLogger
from opgee.table_update import Cell, TableUpdate
from opgee.utils import getBooleanXML, coercible
from opgee.xml.attributes import AttrDefs
from opgee.core.field import Field
from opgee.core.process import Process
from opgee.core.stream import Stream

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from opgee.core.model import Model
    from typing_extensions import override

_logger = getLogger(__name__)

Element: TypeAlias = etree._Element
Parsable = type[Field] | type[Stream] | type[Process] | type[TableUpdate]

ParsableClassName = Literal[
    Field.__name__, Process.__name__, Stream.__name__, TableUpdate.__name__
]


@lru_cache(maxsize=1)
def _parser_map():
    return {
        Field.__name__: parse_field,
        Stream.__name__: parse_stream,
        Process.__name__: parse_process,
        TableUpdate.__name__: parse_table_update,
    }


def is_parsable_class(klass) -> TypeGuard[Parsable]:
    return isinstance(klass, (type(Field), type(Model), type(Stream)))


@overload
def get_parser_function(
    klass: Literal["TableUpdate"] | type[TableUpdate],
) -> Callable[[Element, Model | None], TableUpdate]: ...


@overload
def get_parser_function(
    klass: Literal["Field"] | type[Field],
) -> Callable[[Element, Model | None], Field]: ...


@lru_cache(maxsize=10)
def get_parser_function(
    klass: str | Parsable,
):
    if not isinstance(klass, str):
        klass = klass.__name__
    return _parser_map()[klass]


T = TypeVar("T")


def parse_table_update(elt: Element, parent: Model | None):
    sub_elts = elt.findall("Cell")
    cells = [Cell(e.attrib["row"], e.attrib["col"], e.text) for e in sub_elts]
    return TableUpdate(elt_name(elt), cells)


def parse_stream(elt, parent: Optional["Field"] = None) -> "Stream":
    """
    Parse a Stream XML element into a Stream object.

    Replaces the Stream.from_xml class method.

    :param elt: (etree.Element) representing a <Stream> element
    :param parent: (Field) the Field containing the new Stream
    :return: (Stream) instance of Stream class
    """
    # Import here to avoid circular dependencies
    from opgee.core.stream import Stream

    # Parse XML attributes
    a = elt.attrib
    src = a["src"]
    dst = a["dst"]
    name = a.get("name") or f"{src} => {dst}"
    impute = getBooleanXML(a.get("impute", "1"))

    # Parse stream attributes (temperature, pressure, API)
    # Note: These are currently handled via AttributeMixin.instantiate_attrs
    # This will be refactored in Phase 1.3 to use adapters module
    attr_dict = Stream.instantiate_attrs(elt)  # Temporary - will be replaced

    expected = {"temperature", "pressure", "API"}
    if set(attr_dict.keys()) != expected:
        raise OpgeeException(f"Stream {name}: expected attributes {sorted(expected)}")

    temp = attr_dict["temperature"].value
    pres = attr_dict["pressure"].value
    tp = TemperaturePressure(temp, pres)
    API = attr_dict["API"].value

    # Parse stream contents
    contents = [node.text for node in elt.findall("Contains")]

    # Parse component information
    comp_elts = elt.findall("Component")
    has_exogenous_data = len(comp_elts) > 0

    # Create Stream object
    # Note: This constructor call will need to be updated when Stream class
    # is refactored to not inherit from AttributeMixin
    obj = Stream(
        name=name,
        src_name=src,
        dst_name=dst,
        tp=tp,
        API=API,
        contents=contents,
        impute=impute,
    )

    # Handle exogenous component data
    if has_exogenous_data:
        matrix = Stream.create_component_matrix()
        for comp_elt in comp_elts:
            a = comp_elt.attrib
            comp_name = elt_name(comp_elt)
            rate = coercible(comp_elt.text, float)
            phase = a["phase"]  # required by XML schema

            # Add component data to matrix (implementation will be completed
            # when full component parsing is moved from Stream class)
            # matrix.set_rate(comp_name, phase, rate)  # Placeholder

    return obj


def parse_field(elt, parent=None) -> Field:
    """
    Parse a Field XML element into a Field object.

    Replaces the Field.from_xml class method.

    :param elt: (etree.Element) representing a <Field> element
    :param parent: (Analysis) the Analysis containing the new Field
    :return: (Field) instance populated from XML
    """
    # Import here to avoid circular dependencies
    from opgee.core.field import Field
    from opgee.common import instantiate_subelts
    from opgee.aggregator import Aggregator
    from opgee.core.process import Process
    from opgee.core.stream import Stream
    from opgee.xml.process_groups import ProcessChoice
    from .adapters import extract_xml_element_attributes

    # Parse basic field properties
    name = elt_name(elt)
    attrib = extract_xml_element_attributes(elt)

    # AttrDefs.load_attr_defs(elt=elt)

    # Parse attributes using existing AttributeMixin system (for now)
    # This will be replaced with parse_attributes_from_xml in Phase 1.3
    attr_dict = Field.instantiate_attrs(elt)

    # Parse group memberships
    group_names = [node.text for node in elt.findall("Group")]

    # Create Field instance
    field = Field(name, attr_dict=attr_dict, model=parent, group_names=group_names)

    # Set XML-derived properties
    field.set_enabled(attrib.get("enabled", "1") == "1")
    field.set_extend(attrib.get("extend", "0"))
    field.set_modifies(
        attrib.get("modified")
    )  # "modified" attr is changed after merging

    # Parse child elements using instantiate_subelts (existing system)
    # This maintains full compatibility with current architecture
    aggs = instantiate_subelts(elt, Aggregator, parent=field)
    procs = instantiate_subelts(elt, Process, parent=field)
    streams = instantiate_subelts(elt, Stream, parent=field)
    choices = instantiate_subelts(elt, ProcessChoice)

    # Build process choice dictionary (convert to lowercase to avoid lookup errors)
    process_choice_dict = {choice.name.lower(): choice for choice in choices}

    # Add all children to field
    field.add_children(
        aggs=aggs,
        procs=procs,
        streams=streams,
        process_choice_dict=process_choice_dict,
    )

    # Post-processing: cache attributes for smart defaults
    for proc in field.processes():
        proc.cache_attributes()

    return field


def parse_process(elt, field: Field | None = None) -> "Process":
    """
    Parse a Process XML element into a Process object.

    Replaces the Process.from_xml class method.

    :param elt: (etree.Element) representing a <Process> element
    :param parent: (Field) the Field containing the new Process
    :return: (Process) instance of Process class or subclass
    """
    # Import here to avoid circular dependencies
    from opgee.core.process import Process, _get_subclass
    name = elt_name(elt)

    if name == "test_proc":
        pass

    a = elt.attrib
    desc = a.get("desc")
    impute_start = a.get("impute-start")
    cycle_start = a.get("cycle-start")
    boundary = a.get("boundary")  # optional

    classname = a["class"]  # required by XML schema
    subclass = _get_subclass(Process, classname)
    attr_dict = subclass.instantiate_attrs(elt, is_process=True)

    proc = subclass(
        name,
        attr_dict=attr_dict,
        field=field,
        desc=desc,
        cycle_start=cycle_start,
        impute_start=impute_start,
        boundary=boundary,
    )

    proc.set_enabled(a.get("enabled", "1"))
    proc.set_extend(a.get("extend", "0"))
    proc.set_run_after(getBooleanXML(a.get("after", "0")))

    return proc


# Utility functions for common XML parsing operations
def parse_xml_attributes(elt, expected_attrs: set = None):
    """
    Parse XML element attributes with validation.

    :param elt: XML element
    :param expected_attrs: Set of expected attribute names for validation
    :return: Dictionary of parsed attributes
    """
    attrs = dict(elt.attrib)

    if expected_attrs is not None:
        missing = expected_attrs - set(attrs.keys())
        if missing:
            raise OpgeeException(f"Missing required attributes: {sorted(missing)}")

    return attrs


def find_child_elements(elt, tag_name: str, required: bool = False):
    """
    Find child elements with specified tag name.

    :param elt: Parent XML element
    :param tag_name: Tag name to search for
    :param required: Whether at least one element is required
    :return: List of matching child elements
    """
    children = elt.findall(tag_name)

    if required and not children:
        raise OpgeeException(f"Required child element <{tag_name}> not found")

    return children
