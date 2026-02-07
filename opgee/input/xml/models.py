"""Pydantic-XML models for validating OPGEE XML at pipeline boundaries.

Replaces the XSD schemas (attributes.xsd, opgee_core.xsd, opgee_ext.xsd)
with Python-level validation using typed fields, enums, and validators.

Three model families:
- Core models: post-pipeline output (no ProcessChoice/Aggregator)
- Ext models: pre-pipeline input (with ProcessChoice/Aggregator/modifies)
- AttrDef models: attribute definition structure
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, field_validator, model_validator
from pydantic_xml import BaseXmlModel, attr, element


# --- Issue 9: AttrDef.type enum ---
AttrType = Literal["binary", "int", "float", "str"]

# --- Issue 8: Process.class enum ---
# All 51 Process subclasses (49 in processes/ + Boundary + Reservoir in process.py)
ProcessClass = Literal[
    "AcidGasRemoval",
    "BitumenMining",
    "Boundary",
    "CO2InjectionWell",
    "CO2Membrane",
    "CO2ReinjectionCompressor",
    "CrudeOilDewatering",
    "CrudeOilStabilization",
    "CrudeOilStorage",
    "CrudeOilTransport",
    "Demethanizer",
    "DownholePump",
    "Drilling",
    "Exploration",
    "Flaring",
    "GasDehydration",
    "GasDistribution",
    "GasGathering",
    "GasLiftingCompressor",
    "GasPartition",
    "GasReinjectionCompressor",
    "GasReinjectionWell",
    "HeavyOilDilution",
    "HeavyOilUpgrading",
    "LNGLiquefaction",
    "LNGRegasification",
    "LNGTransport",
    "NGL",
    "PetrocokeTransport",
    "PostStorageCompressor",
    "PreMembraneChiller",
    "PreMembraneCompressor",
    "Reservoir",
    "ReservoirWellInterface",
    "RyanHolmes",
    "Separation",
    "SourGasCompressor",
    "SourGasInjection",
    "SteamGeneration",
    "StorageCompressor",
    "StorageSeparator",
    "StorageWell",
    "TransmissionCompressor",
    "VFPartition",
    "Venting",
    "VRUCompressor",
    "WaterInjection",
    "WaterTreatment",
]


# =====================================================================
# Shared element models
# =====================================================================


class AElement(BaseXmlModel, tag="A"):
    """A single attribute value element."""

    name: str = attr()
    value: str | None = None  # text content
    explicit: bool | None = attr(default=None)
    delete: bool | None = attr(default=None)


class ComponentElement(BaseXmlModel, tag="Component"):
    """A stream component with name, phase, and fractional value."""

    name: str = attr()
    phase: Literal["gas", "liquid", "solid"] = attr()
    value: str | None = None  # text content (decimal)


class ContainsElement(BaseXmlModel, tag="Contains"):
    """Declares what a stream contains."""

    value: str | None = None  # text content
    delete: bool | None = attr(default=None)


class StreamElement(BaseXmlModel, tag="Stream", search_mode="unordered"):
    """A material/energy flow connection between processes."""

    src: str = attr()
    dst: str = attr()
    name: str | None = attr(default=None)
    impute: bool | None = attr(default=None)
    boundary: str | None = attr(default=None)
    delete: bool | None = attr(default=None)
    attrs: list[AElement] = element(tag="A", default=[])
    components: list[ComponentElement] = element(tag="Component", default=[])
    contains: list[ContainsElement] = element(tag="Contains", default=[])

    @field_validator("attrs")
    @classmethod
    def max_three_attrs(cls, v: list[AElement]) -> list[AElement]:
        """Issue 6: Stream may have at most 3 <A> children."""
        if len(v) > 3:
            raise ValueError(f"Stream may have at most 3 <A> children, got {len(v)}")
        return v


class ProcessElement(BaseXmlModel, tag="Process", search_mode="unordered"):
    """A single LCA process step."""

    class_name: ProcessClass = attr(name="class")
    name: str | None = attr(default=None)
    enabled: bool | None = attr(default=None)
    extend: bool | None = attr(default=None)
    boundary: str | None = attr(default=None)
    delete: bool | None = attr(default=None)
    desc: str | None = attr(default=None)
    impute_start: bool | None = attr(name="impute-start", default=None)
    cycle_start: bool | None = attr(name="cycle-start", default=None)
    after: bool | None = attr(default=None)
    attrs: list[AElement] = element(tag="A", default=[])

    @property
    def resolved_name(self) -> str:
        return self.name or self.class_name


class GroupElement(BaseXmlModel, tag="Group"):
    """A field grouping tag."""

    value: str | None = None  # text content
    regex: bool | None = attr(default=None)
    delete: bool | None = attr(default=None)


class FieldRefElement(BaseXmlModel, tag="FieldRef"):
    """A reference to a field by name within an analysis."""

    name: str = attr()
    delete: bool | None = attr(default=None)


# =====================================================================
# Core models (post-pipeline, no ProcessChoice/Aggregator)
# =====================================================================


class CoreAnalysis(BaseXmlModel, tag="Analysis", search_mode="unordered"):
    """Post-pipeline analysis definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = attr()
    delete: bool | None = attr(default=None)
    attrs: list[AElement] = element(tag="A", default=[])
    field_refs: list[FieldRefElement] = element(tag="FieldRef", default=[])
    groups: list[GroupElement] = element(tag="Group", default=[])


class CoreField(BaseXmlModel, tag="Field", search_mode="unordered"):
    """Post-pipeline field definition (no ProcessChoice/Aggregator)."""

    model_config = ConfigDict(extra="forbid")

    name: str = attr()
    enabled: bool | None = attr(default=None)
    extend: bool | None = attr(default=None)
    delete: bool | None = attr(default=None)
    attrs: list[AElement] = element(tag="A", default=[])
    groups: list[GroupElement] = element(tag="Group", default=[])
    processes: list[ProcessElement] = element(tag="Process", default=[])
    streams: list[StreamElement] = element(tag="Stream", default=[])

    @property
    def process_names(self) -> list[str]:
        return [p.resolved_name for p in self.processes]

    @property
    def stream_names(self) -> list[str]:
        return [s.name or f"{s.src} => {s.dst}" for s in self.streams]


class CoreModel(BaseXmlModel, tag="Model", search_mode="unordered"):
    """Post-pipeline model -- no ProcessChoice, no Aggregator."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str | None = attr(default=None)
    top_attrs: list[AElement] = element(tag="A", default=[])
    analyses: list[CoreAnalysis] = element(tag="Analysis", default=[])
    fields: list[CoreField] = element(tag="Field", default=[])

    @property
    def field(self) -> CoreField | None:
        return self.fields[0] if self.fields else None

    @property
    def analysis(self) -> CoreAnalysis | None:
        return self.analyses[0] if self.analyses else None


# =====================================================================
# Ext models (pre-pipeline, adds ProcessChoice/Aggregator/modifies)
# =====================================================================


class ProcessRefElement(BaseXmlModel, tag="ProcessRef"):
    """Reference to a process by name or class within a ProcessGroup."""

    name: str | None = attr(default=None)
    class_name: str | None = attr(name="class", default=None)
    delete: bool | None = attr(default=None)


class StreamRefElement(BaseXmlModel, tag="StreamRef"):
    """Reference to a stream by name within a ProcessGroup."""

    name: str = attr()
    delete: bool | None = attr(default=None)


class ProcessChoiceElement(BaseXmlModel, tag="ProcessChoice"):
    """A choice between process groups, resolved during pipeline stage 3."""

    name: str = attr()
    default: str | None = attr(default=None)
    extend: bool | None = attr(default=None)
    delete: bool | None = attr(default=None)
    groups: list[ProcessGroupElement] = element(tag="ProcessGroup", default=[])

    @model_validator(mode="after")
    def at_least_one_group(self) -> ProcessChoiceElement:
        if len(self.groups) < 1:
            raise ValueError("ProcessChoice requires at least one ProcessGroup")
        return self


class ProcessGroupElement(BaseXmlModel, tag="ProcessGroup", search_mode="unordered"):
    """A group of process/stream refs within a ProcessChoice."""

    name: str = attr()
    delete: bool | None = attr(default=None)
    process_refs: list[ProcessRefElement] = element(tag="ProcessRef", default=[])
    stream_refs: list[StreamRefElement] = element(tag="StreamRef", default=[])
    process_choices: list[ProcessChoiceElement] = element(tag="ProcessChoice", default=[])


class AggregatorElement(BaseXmlModel, tag="Aggregator", search_mode="unordered"):
    """Groups processes for aggregated reporting."""

    name: str = attr()
    enabled: bool | None = attr(default=None)
    delete: bool | None = attr(default=None)
    attrs: list[AElement] = element(tag="A", default=[])
    processes: list[ProcessElement] = element(tag="Process", default=[])
    process_refs: list[ProcessRefElement] = element(tag="ProcessRef", default=[])
    aggregators: list[AggregatorElement] = element(tag="Aggregator", default=[])
    process_choices: list[ProcessChoiceElement] = element(tag="ProcessChoice", default=[])


class ExtField(BaseXmlModel, tag="Field", search_mode="unordered"):
    """Pre-pipeline field -- adds ProcessChoice, Aggregator, modifies/modified."""

    model_config = ConfigDict(extra="forbid")

    name: str = attr()
    enabled: bool | None = attr(default=None)
    extend: bool | None = attr(default=None)
    delete: bool | None = attr(default=None)
    modifies: str | None = attr(default=None)
    modified: str | None = attr(default=None)
    attrs: list[AElement] = element(tag="A", default=[])
    groups: list[GroupElement] = element(tag="Group", default=[])
    processes: list[ProcessElement] = element(tag="Process", default=[])
    streams: list[StreamElement] = element(tag="Stream", default=[])
    aggregators: list[AggregatorElement] = element(tag="Aggregator", default=[])
    process_choices: list[ProcessChoiceElement] = element(tag="ProcessChoice", default=[])


class ExtModel(BaseXmlModel, tag="Model", search_mode="unordered"):
    """Pre-pipeline model -- accepts ProcessChoice and Aggregator."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str | None = attr(default=None)
    top_attrs: list[AElement] = element(tag="A", default=[])
    analyses: list[CoreAnalysis] = element(tag="Analysis", default=[])
    fields: list[ExtField] = element(tag="Field", default=[])


# =====================================================================
# AttrDef models (validates <AttrDefs> structure)
# =====================================================================


class OptionElement(BaseXmlModel, tag="Option"):
    """A single option within an Options set."""

    value: str | None = None  # text content
    label: str | None = attr(default=None)
    desc: str | None = attr(default=None)


class OptionsElement(BaseXmlModel, tag="Options"):
    """A named set of valid options for an attribute."""

    name: str = attr()
    default: str = attr()
    options: list[OptionElement] = element(tag="Option", default=[])

    @model_validator(mode="after")
    def at_least_one_option(self) -> OptionsElement:
        if len(self.options) < 1:
            raise ValueError("Options requires at least one Option child")
        return self


class AttrDefElement(BaseXmlModel, tag="AttrDef"):
    """Definition of a single attribute with type, unit, and constraints."""

    name: str = attr()
    type: AttrType | None = attr(default=None)
    unit: str | None = attr(default=None)
    desc: str | None = attr(default=None)
    options: str | None = attr(default=None)
    exclusive: str | None = attr(default=None)
    synchronized: str | None = attr(default=None)
    gt: float | None = attr(name="GT", default=None)
    ge: float | None = attr(name="GE", default=None)
    lt: float | None = attr(name="LT", default=None)
    le: float | None = attr(name="LE", default=None)
    default_value: str | None = None  # text content


class ClassAttrsElement(BaseXmlModel, tag="ClassAttrs", search_mode="unordered"):
    """Attribute definitions for a specific class (Field, Analysis, etc.)."""

    name: str = attr()
    options: list[OptionsElement] = element(tag="Options", default=[])
    attr_defs: list[AttrDefElement] = element(tag="AttrDef", default=[])


class AttrDefsElement(BaseXmlModel, tag="AttrDefs"):
    """Top-level container for all class attribute definitions."""

    class_attrs: list[ClassAttrsElement] = element(tag="ClassAttrs", default=[])


# Update forward references for recursive models
ProcessChoiceElement.model_rebuild()
AggregatorElement.model_rebuild()
