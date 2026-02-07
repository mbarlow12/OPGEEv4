"""Stage 4: Build lightweight model objects from clean lxml tree."""

from dataclasses import dataclass
from typing import Any

from lxml import etree

from .value_resolution import read_attr_value, get_attr_def


@dataclass(frozen=True, slots=True)
class BuiltProcess:
    name: str
    class_name: str
    attr_dict: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BuiltAnalysis:
    name: str
    attr_dict: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BuiltField:
    name: str
    attr_dict: dict[str, Any]
    process_names: list[str]
    stream_names: list[str]


@dataclass(frozen=True, slots=True)
class BuiltModel:
    field: BuiltField
    analysis: BuiltAnalysis
    processes: dict[str, BuiltProcess]


def build_model(root: etree.Element) -> BuiltModel:
    """
    Build a BuiltModel from a clean (post-pipeline) lxml tree.

    :param root: <Model> lxml Element with all defaults applied and
                 process choices resolved
    :return: BuiltModel with typed attribute dicts
    """
    field_elt = root.find("Field")
    analysis_elt = root.find("Analysis")

    analysis = _build_analysis(analysis_elt) if analysis_elt is not None else BuiltAnalysis(name="", attr_dict={})

    processes: dict[str, BuiltProcess] = {}
    process_names: list[str] = []
    stream_names: list[str] = []

    if field_elt is not None:
        for proc_elt in field_elt.findall("Process"):
            built_proc = _build_process(proc_elt)
            processes[built_proc.name] = built_proc
            process_names.append(built_proc.name)

        for stream_elt in field_elt.findall("Stream"):
            name = stream_elt.get("name") or f"{stream_elt.get('src')} => {stream_elt.get('dst')}"
            stream_names.append(name)

    field = _build_field(field_elt, process_names, stream_names) if field_elt is not None else BuiltField(
        name="", attr_dict={}, process_names=[], stream_names=[]
    )

    return BuiltModel(field=field, analysis=analysis, processes=processes)


def _build_analysis(elt: etree.Element) -> BuiltAnalysis:
    """Build a BuiltAnalysis from an <Analysis> element."""
    name = elt.get("name", "")
    attr_dict = _extract_attrs(elt, "Analysis")
    return BuiltAnalysis(name=name, attr_dict=attr_dict)


def _build_process(elt: etree.Element) -> BuiltProcess:
    """Build a BuiltProcess from a <Process> element."""
    class_name = elt.get("class", "")
    name = elt.get("name") or class_name
    attr_dict = _extract_attrs(elt, class_name)
    return BuiltProcess(name=name, class_name=class_name, attr_dict=attr_dict)


def _build_field(elt: etree.Element, process_names: list[str],
                 stream_names: list[str]) -> BuiltField:
    """Build a BuiltField from a <Field> element."""
    name = elt.get("name", "")
    attr_dict = _extract_attrs(elt, "Field")
    return BuiltField(name=name, attr_dict=attr_dict,
                      process_names=process_names, stream_names=stream_names)


def _extract_attrs(elt: etree.Element, class_name: str) -> dict[str, Any]:
    """Extract all <A> children as a typed attribute dict."""
    attr_dict: dict[str, Any] = {}

    for a_elt in elt.findall("A"):
        attr_name = a_elt.get("name")
        if attr_name is None:
            continue

        text = a_elt.text
        if text is None:
            attr_dict[attr_name] = None
            continue

        attr_def = get_attr_def(class_name, attr_name)
        if attr_def is None:
            attr_dict[attr_name] = text
            continue

        try:
            attr_dict[attr_name] = read_attr_value(elt, attr_name, class_name)
        except (ValueError, KeyError):
            attr_dict[attr_name] = text

    return attr_dict
