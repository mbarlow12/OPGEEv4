"""Extract data from lxml elements into opgee_input dataclasses."""
from __future__ import annotations

from lxml import etree

from opgee_input import (
    AnalysisInput,
    ContainsSpec,
    FieldInput,
    ProcessBase,
    StreamInput,
    PROCESS_CLASSES,
)

# Set of all process tag names for identification
_PROCESS_TAGS = frozenset(PROCESS_CLASSES.keys())


def extract_stream(stream_elt: etree._Element) -> StreamInput:
    """Extract a <Stream> element into a StreamInput dataclass."""
    data: dict = {}
    # XML attributes
    for attr_name in ("src", "dst", "name", "impute", "boundary", "delete"):
        val = stream_elt.get(attr_name)
        if val is not None:
            data[attr_name] = val

    # Contains children
    contains = []
    for child in stream_elt.findall("Contains"):
        contains.append(ContainsSpec(value=child.text, delete=_parse_bool_attr(child, "delete")))
    if contains:
        data["contains"] = contains

    return StreamInput(**data)


def extract_process(proc_elt: etree._Element) -> ProcessBase:
    """Extract a process element into the correct ProcessBase subclass."""
    cls_name = proc_elt.tag
    cls = PROCESS_CLASSES.get(cls_name)
    if cls is None:
        raise ValueError(f"Unknown process type: {cls_name}")

    data: dict = {}
    # XML attributes (enabled, boundary, after, impute-start, cycle-start)
    for attr_name, field_name in [
        ("enabled", "enabled"),
        ("boundary", "boundary"),
        ("after", "after"),
        ("impute-start", "impute_start"),
        ("cycle-start", "cycle_start"),
    ]:
        val = proc_elt.get(attr_name)
        if val is not None:
            data[field_name] = val

    # Child elements (process-specific fields)
    for child in proc_elt:
        if child.tag in ("Contains", "Stream"):
            continue
        data[child.tag] = child.text

    return cls(**data)


def extract_field(field_elt: etree._Element) -> FieldInput:
    """Extract a <Field> element into a FieldInput dataclass.

    Iterates child elements: process tags go to process list,
    <Stream> tags go to stream list, everything else is a field attribute.
    """
    data: dict = {}
    processes = []
    streams = []

    # XML attributes on <Field>
    name = field_elt.get("name")
    if name is not None:
        data["name"] = name
    enabled = field_elt.get("enabled")
    if enabled is not None:
        data["enabled"] = enabled

    # Child elements
    for child in field_elt:
        tag = child.tag
        # Skip namespace elements (inc:*)
        if isinstance(tag, str) and tag.startswith("{"):
            continue

        if tag in _PROCESS_TAGS:
            processes.append(extract_process(child))
        elif tag == "Stream":
            streams.append(extract_stream(child))
        else:
            # Field attribute element -- use text content
            if child.text is not None:
                data[tag] = child.text

    if processes:
        data["processes"] = processes
    if streams:
        data["streams"] = streams

    return FieldInput(**data)


def extract_analysis(analysis_elt: etree._Element) -> AnalysisInput:
    """Extract an <Analysis> element into an AnalysisInput dataclass.

    Skips <Group> children (XML-routing only, not part of AnalysisInput).
    """
    data: dict = {}

    name = analysis_elt.get("name")
    if name is not None:
        data["name"] = name

    for child in analysis_elt:
        if child.tag == "Group":
            continue
        if child.text is not None:
            data[child.tag] = child.text

    return AnalysisInput(**data)


def _parse_bool_attr(elt: etree._Element, attr_name: str) -> bool | None:
    """Parse a boolean XML attribute, returning None if absent."""
    val = elt.get(attr_name)
    if val is None:
        return None
    return val.lower() in ("true", "1", "yes")
