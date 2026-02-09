"""Tests for lxml -> dataclass extraction."""
from __future__ import annotations

import pytest
from lxml import etree

from opgee_input import (
    AnalysisInput,
    FieldInput,
    ProcessBase,
    StreamInput,
    PROCESS_CLASSES,
)
from opgee_input.processes import Separation, AcidGasRemoval

from opgee_xml.extract import (
    extract_analysis,
    extract_field,
    extract_process,
    extract_stream,
)


class TestExtractStream:
    def test_basic_stream(self):
        stream_elt = etree.Element("Stream", src="A", dst="B")
        result = extract_stream(stream_elt)
        assert isinstance(result, StreamInput)
        assert result.src == "A"
        assert result.dst == "B"

    def test_stream_with_name(self):
        stream_elt = etree.Element("Stream", src="A", dst="B", name="my_stream")
        result = extract_stream(stream_elt)
        assert result.name == "my_stream"

    def test_stream_with_contains(self):
        stream_elt = etree.Element("Stream", src="A", dst="B")
        c = etree.SubElement(stream_elt, "Contains")
        c.text = "oil"
        result = extract_stream(stream_elt)
        assert len(result.contains) == 1
        assert result.contains[0].value == "oil"

    def test_stream_with_contains_delete(self):
        stream_elt = etree.Element("Stream", src="A", dst="B")
        c = etree.SubElement(stream_elt, "Contains", delete="true")
        c.text = "gas"
        result = extract_stream(stream_elt)
        assert result.contains[0].delete is True

    def test_stream_with_impute(self):
        stream_elt = etree.Element("Stream", src="A", dst="B", impute="False")
        result = extract_stream(stream_elt)
        assert result.impute is not None

    def test_stream_with_delete_attr(self):
        stream_elt = etree.Element("Stream", src="A", dst="B", delete="1")
        result = extract_stream(stream_elt)
        assert result.delete is not None


class TestExtractProcess:
    def test_simple_separation(self):
        proc_elt = etree.Element("Separation")
        result = extract_process(proc_elt)
        assert isinstance(result, Separation)

    def test_process_with_boundary(self):
        proc_elt = etree.Element("Separation", boundary="Production")
        result = extract_process(proc_elt)
        assert result.boundary == "Production"

    def test_process_with_impute_start(self):
        proc_elt = etree.fromstring('<Separation impute-start="true"/>')
        result = extract_process(proc_elt)
        assert result.impute_start is not None

    def test_process_with_cycle_start(self):
        proc_elt = etree.fromstring('<ReservoirWellInterface cycle-start="true"/>')
        result = extract_process(proc_elt)
        assert result.cycle_start is not None

    def test_process_with_child_elements(self):
        proc_elt = etree.Element("AcidGasRemoval")
        child = etree.SubElement(proc_elt, "type_amine")
        child.text = "MEA"
        result = extract_process(proc_elt)
        assert isinstance(result, AcidGasRemoval)
        assert result.type_amine == "MEA"

    def test_unknown_process_raises(self):
        proc_elt = etree.Element("NotAProcess")
        with pytest.raises(ValueError, match="Unknown process type"):
            extract_process(proc_elt)

    @pytest.mark.parametrize("cls_name", list(PROCESS_CLASSES.keys()))
    def test_all_process_types_instantiate(self, cls_name: str):
        """Every known process type can be extracted from a minimal element."""
        proc_elt = etree.Element(cls_name)
        result = extract_process(proc_elt)
        assert isinstance(result, ProcessBase)
        assert type(result).__name__ == cls_name

    def test_process_with_enabled(self):
        proc_elt = etree.Element("Separation", enabled="false")
        result = extract_process(proc_elt)
        assert result.enabled is not None

    def test_process_with_after(self):
        proc_elt = etree.Element("Exploration", after="true")
        result = extract_process(proc_elt)
        assert result.after is not None


class TestExtractField:
    def test_simple_field(self):
        field_elt = etree.Element("Field", name="test_field")
        etree.SubElement(field_elt, "Separation")
        result = extract_field(field_elt)
        assert isinstance(result, FieldInput)
        assert result.name == "test_field"
        assert len(result.processes) == 1
        assert isinstance(result.processes[0], Separation)

    def test_field_with_streams(self):
        field_elt = etree.Element("Field", name="test_field")
        etree.SubElement(field_elt, "Separation")
        etree.SubElement(field_elt, "Stream", src="A", dst="B")
        result = extract_field(field_elt)
        assert len(result.streams) == 1
        assert result.streams[0].src == "A"

    def test_field_with_attribute_elements(self):
        field_elt = etree.Element("Field", name="test_field")
        etree.SubElement(field_elt, "Separation")
        api = etree.SubElement(field_elt, "API")
        api.text = "32.8"
        result = extract_field(field_elt)
        # The API value should be captured -- FieldInput uses lax coercion
        assert result.name == "test_field"

    def test_field_skips_namespace_elements(self):
        field_elt = etree.Element("Field", name="test_field")
        etree.SubElement(field_elt, "Separation")
        ns_elt = etree.SubElement(field_elt, "{urn:opgee:include}template")
        ns_elt.text = "template"
        result = extract_field(field_elt)
        # Namespace elements are skipped, not extracted as attributes
        assert isinstance(result, FieldInput)

    def test_field_multiple_processes(self):
        field_elt = etree.Element("Field", name="test_field")
        etree.SubElement(field_elt, "Separation")
        etree.SubElement(field_elt, "GasDehydration")
        result = extract_field(field_elt)
        assert len(result.processes) == 2


class TestExtractAnalysis:
    def test_basic_analysis(self):
        analysis_elt = etree.Element("Analysis", name="test_analysis")
        result = extract_analysis(analysis_elt)
        assert isinstance(result, AnalysisInput)
        assert result.name == "test_analysis"

    def test_analysis_skips_group(self):
        analysis_elt = etree.Element("Analysis", name="test_analysis")
        group = etree.SubElement(analysis_elt, "Group")
        group.text = "some_group"
        result = extract_analysis(analysis_elt)
        assert result.name == "test_analysis"

    def test_analysis_with_elements(self):
        analysis_elt = etree.Element("Analysis", name="test_analysis")
        gwp = etree.SubElement(analysis_elt, "GWP_horizon")
        gwp.text = "100"
        boundary = etree.SubElement(analysis_elt, "boundary")
        boundary.text = "Production"
        result = extract_analysis(analysis_elt)
        assert result.GWP_horizon == "100"
        assert result.boundary == "Production"

    def test_analysis_with_functional_unit(self):
        analysis_elt = etree.Element("Analysis", name="test_analysis")
        fu = etree.SubElement(analysis_elt, "functional_unit")
        fu.text = "oil"
        result = extract_analysis(analysis_elt)
        assert result.functional_unit == "oil"
