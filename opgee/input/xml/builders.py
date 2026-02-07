"""Stage 4: Build lightweight model objects from clean lxml tree.

Parses the post-pipeline lxml tree into a CoreModel (pydantic-xml) for
structural validation, then builds BuiltModel dataclasses with typed
attr_dicts resolved via AttrDefs metadata.
"""

from dataclasses import dataclass
from typing import Any

from lxml import etree

from .models import CoreModel, CoreField, CoreAnalysis, ProcessElement
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

    Validates structure via CoreModel, then extracts typed attr_dicts.

    :param root: <Model> lxml Element with all defaults applied and
                 process choices resolved
    :return: BuiltModel with typed attribute dicts
    """
    core = CoreModel.from_xml_tree(root)

    analysis = _build_analysis(core.analysis, root.find("Analysis"))

    processes: dict[str, BuiltProcess] = {}
    process_names: list[str] = []
    stream_names: list[str] = []

    field_elt = root.find("Field")
    if core.field is not None and field_elt is not None:
        proc_elts = field_elt.findall("Process")
        for i, proc in enumerate(core.field.processes):
            built_proc = _build_process(proc, proc_elts[i])
            processes[built_proc.name] = built_proc
            process_names.append(built_proc.name)

        stream_names = core.field.stream_names

    field = _build_field(core.field, field_elt, process_names, stream_names)

    return BuiltModel(field=field, analysis=analysis, processes=processes)


def _build_analysis(
    analysis: CoreAnalysis | None, elt: etree.Element | None
) -> BuiltAnalysis:
    """Build a BuiltAnalysis from CoreAnalysis + lxml element."""
    if analysis is None or elt is None:
        return BuiltAnalysis(name="", attr_dict={})
    return BuiltAnalysis(name=analysis.name, attr_dict=_extract_attrs(elt, "Analysis"))


def _build_process(proc: ProcessElement, elt: etree.Element) -> BuiltProcess:
    """Build a BuiltProcess from ProcessElement + lxml element."""
    name = proc.resolved_name
    return BuiltProcess(
        name=name,
        class_name=proc.class_name,
        attr_dict=_extract_attrs(elt, proc.class_name),
    )


def _build_field(
    field: CoreField | None,
    elt: etree.Element | None,
    process_names: list[str],
    stream_names: list[str],
) -> BuiltField:
    """Build a BuiltField from CoreField + lxml element."""
    if field is None or elt is None:
        return BuiltField(name="", attr_dict={}, process_names=[], stream_names=[])
    return BuiltField(
        name=field.name,
        attr_dict=_extract_attrs(elt, "Field"),
        process_names=process_names,
        stream_names=stream_names,
    )


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
