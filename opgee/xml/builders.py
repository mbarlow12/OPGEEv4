#
# OPGEE XML Builders
#
# Object construction functions for complex object assembly
# Part of XML/Core package separation refactoring
#
# Author: Refactoring Team
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#

from __future__ import annotations

from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from xml.etree.ElementTree import Element

from opgee.core.error import OpgeeException
from opgee.core.log import getLogger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from opgee.core.field import Field
    from opgee.core.process import Process
    from opgee.core.stream import Stream

_logger = getLogger(__name__)


def build_field_with_processes(field_obj: Field, field_element: Element) -> Field:
    """
    Build a complete Field object with its processes and streams from a Field XML element.

    Based on XSD schema, Field can contain:
    - A elements (attributes)
    - Group elements
    - Aggregator elements
    - Process elements
    - ProcessChoice elements
    - Stream elements

    :param field_obj: Base Field object to populate
    :param field_element: XML Field element containing child elements
    :return: Fully constructed Field object
    """
    # Import here to avoid circular dependencies
    from .parsers import parse_process, parse_stream

    # Parse child elements according to XSD schema
    for child in field_element:
        if child.tag == "A":
            # Attribute element - handle via adapters
            continue
        elif child.tag == "Group":
            # Group membership - handle field grouping
            _handle_field_group(child, field_obj)
        elif child.tag == "Aggregator":
            # Aggregator element - build aggregator structure
            aggregator = _build_aggregator(child, field_obj)
            field_obj.add_aggregator(aggregator)
        elif child.tag == "Process":
            # Regular process element
            process_obj = parse_process(child, parent=field_obj)
            field_obj.add_process(process_obj)
        elif child.tag == "ProcessChoice":
            # ProcessChoice element - handle mutually exclusive processes
            choice_processes = _build_process_choice(child, field_obj)
            for proc in choice_processes:
                field_obj.add_process(proc)
        elif child.tag == "Stream":
            # Stream element
            stream_obj = parse_stream(child, parent=field_obj)
            field_obj.add_stream(stream_obj)

    # Validate field connectivity after building all components
    _validate_field_connectivity(field_obj)

    return field_obj


def build_process_hierarchy(
    process_elements: List[Element], parent: Optional[Field] = None
) -> List[Process]:
    """
    Build a hierarchy of Process objects from XML elements.

    Handles regular Process elements and ProcessChoice structures.

    :param process_elements: List of XML process elements
    :param parent: Parent Field object
    :return: List of constructed Process objects
    """
    # Import here to avoid circular dependencies
    from .parsers import parse_process

    processes: List[Process] = []

    for proc_elt in process_elements:
        if proc_elt.tag == "Process":
            # Regular process element
            process_obj = parse_process(proc_elt, parent)
            processes.append(process_obj)
        elif proc_elt.tag == "ProcessChoice":
            # ProcessChoice - handle mutually exclusive processes
            choice_processes = _build_process_choice(proc_elt, parent)
            processes.extend(choice_processes)

    return processes


def build_stream_network(
    stream_elements: List[Element], field_obj: Field
) -> Dict[str, Stream]:
    """
    Build a network of Stream objects with proper connectivity.

    Based on XSD schema, Stream elements have:
    - Required src and dst attributes
    - Optional name attribute (computed if not provided)
    - Optional A elements (attributes)
    - Optional Component elements
    - Optional Contains elements

    :param stream_elements: List of XML stream elements
    :param field_obj: Field object containing the processes
    :return: Dictionary mapping stream names to Stream objects
    """
    # Import here to avoid circular dependencies
    from .parsers import parse_stream

    streams: Dict[str, Stream] = {}

    for stream_elt in stream_elements:
        stream_obj = parse_stream(stream_elt, parent=field_obj)
        streams[stream_obj.name] = stream_obj

    # Validate that all stream connections reference valid processes
    _validate_stream_connections(streams, field_obj)

    return streams


def _build_aggregator(aggregator_elt: Element, parent: Optional[Field]) -> Any:
    """
    Build an Aggregator object from XML element.

    Based on XSD schema, Aggregator can contain:
    - Nested Aggregator elements (recursive)
    - A elements (attributes)
    - Process elements
    - ProcessChoice elements

    :param aggregator_elt: XML Aggregator element
    :param parent: Parent Field object
    :return: Aggregator object
    """
    # This is a placeholder for Aggregator handling
    # Full implementation will be added in Phase 1.3
    _logger.info("_build_aggregator placeholder - implementation pending")

    # Extract basic attributes
    name = aggregator_elt.get("name", "")
    enabled = aggregator_elt.get("enabled", "1") == "1"

    # TODO: Build nested structure and add processes
    return {"name": name, "enabled": enabled, "type": "aggregator"}


def _build_process_choice(
    choice_elt: Element, parent: Optional[Field]
) -> List[Process]:
    """
    Build processes from a ProcessChoice element.

    Based on XSD schema, ProcessChoice contains:
    - One or more ProcessGroup elements
    - Attributes: name (required), extend, default, delete

    :param choice_elt: XML ProcessChoice element
    :param parent: Parent Field object
    :return: List of selected Process objects
    """
    # This is a placeholder for ProcessChoice handling
    # Full implementation will be added in Phase 1.3
    _logger.info("_build_process_choice placeholder - implementation pending")

    choice_name = choice_elt.get("name", "")
    default_group = choice_elt.get("default", "")

    # Find ProcessGroup elements and select appropriate one
    process_groups = choice_elt.findall("ProcessGroup")
    selected_processes: List[Process] = []

    # TODO: Implement selection logic based on default or configuration
    # For now, return empty list
    return selected_processes


def _build_process_group(group_elt: Element, parent: Optional[Field]) -> List[Process]:
    """
    Build processes from a ProcessGroup element.

    Based on XSD schema, ProcessGroup can contain:
    - ProcessRef elements
    - StreamRef elements
    - ProcessChoice elements (recursive)

    :param group_elt: XML ProcessGroup element
    :param parent: Parent Field object
    :return: List of Process objects in the group
    """
    # This is a placeholder for ProcessGroup handling
    # Full implementation will be added in Phase 1.3
    _logger.info("_build_process_group placeholder - implementation pending")

    group_name = group_elt.get("name", "")
    processes: List[Process] = []

    # TODO: Handle ProcessRef, StreamRef, and nested ProcessChoice elements
    return processes


def _handle_field_group(group_elt: Element, field_obj: Field) -> None:
    """
    Handle Field Group membership.

    :param group_elt: XML Group element
    :param field_obj: Field object to add to group
    """
    group_name = group_elt.text or ""
    is_regex = group_elt.get("regex", "0") == "1"

    # TODO: Add field to group registry
    _logger.debug(
        f"Field {field_obj.name if hasattr(field_obj, 'name') else 'unknown'} belongs to group: {group_name}"
    )


def _validate_field_connectivity(field_obj: Field) -> None:
    """
    Validate that all processes and streams in a field are properly connected.

    :param field_obj: Field object to validate
    :raises OpgeeException: If connectivity issues are found
    """
    # Basic validation placeholder
    # Full implementation will include:
    # - Check that all stream src/dst processes exist
    # - Validate process input/output requirements
    # - Check for orphaned processes or streams

    processes = field_obj.processes if hasattr(field_obj, "processes") else {}
    streams = field_obj.streams if hasattr(field_obj, "streams") else {}

    for stream_name, stream in streams.items():
        if hasattr(stream, "src") and stream.src not in processes:
            _logger.warning(
                f"Stream {stream_name} references unknown source process: {stream.src}"
            )

        if hasattr(stream, "dst") and stream.dst not in processes:
            _logger.warning(
                f"Stream {stream_name} references unknown destination process: {stream.dst}"
            )


def _validate_stream_connections(streams: Dict[str, Stream], field_obj: Field) -> None:
    """
    Validate that stream connections reference valid processes.

    :param streams: Dictionary of stream name to Stream object
    :param field_obj: Field object containing processes
    :raises OpgeeException: If invalid connections are found
    """
    processes = field_obj.processes if hasattr(field_obj, "processes") else {}

    for stream_name, stream in streams.items():
        # Validate source process exists
        if hasattr(stream, "src") and stream.src not in processes:
            raise OpgeeException(
                f"Stream {stream_name} references unknown source process: {stream.src}"
            )

        # Validate destination process exists
        if hasattr(stream, "dst") and stream.dst not in processes:
            raise OpgeeException(
                f"Stream {stream_name} references unknown destination process: {stream.dst}"
            )


# Utility functions for object assembly
def merge_attributes(
    base_attrs: Dict[str, Any], override_attrs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge attribute dictionaries with override precedence.

    :param base_attrs: Base attributes
    :param override_attrs: Override attributes (take precedence)
    :return: Merged attribute dictionary
    """
    merged = base_attrs.copy()
    merged.update(override_attrs)
    return merged


def apply_inheritance(
    child_obj: Any, parent_obj: Any, inheritable_attrs: List[str]
) -> None:
    """
    Apply attribute inheritance from parent to child object.

    :param child_obj: Child object to update
    :param parent_obj: Parent object to inherit from
    :param inheritable_attrs: List of attribute names that can be inherited
    """
    for attr_name in inheritable_attrs:
        if hasattr(parent_obj, attr_name) and not hasattr(child_obj, attr_name):
            setattr(child_obj, attr_name, getattr(parent_obj, attr_name))


def extract_xml_attributes(element: Element) -> Dict[str, str]:
    """
    Extract all attributes from an XML element.

    :param element: XML element
    :return: Dictionary of attribute name to string value
    """
    return dict(element.attrib)


def parse_boolean_attr(element: Element, attr_name: str, default: bool = False) -> bool:
    """
    Parse a boolean attribute from XML element.

    :param element: XML element
    :param attr_name: Attribute name
    :param default: Default value if attribute not present
    :return: Boolean value
    """
    value = element.get(attr_name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")

