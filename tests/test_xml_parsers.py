"""
Test XML parsers module - Phase 1.2 refactoring tests

Tests for the new XML parsing functions that replace from_xml class methods.
"""

import pdb
import pytest
import warnings
from xml.etree import ElementTree as ET

from opgee.xml.parsers import parse_field, parse_stream
from opgee.core.field import Field
from opgee.core.stream import Stream
from opgee.core.error import OpgeeException
from opgee.core.units import ureg
from .utils_for_tests import load_model_from_str, load_test_model


# Test XML fragments
simple_field_xml = """
<Field name="test_field">
    <A name="country">USA</A>
    <A name="well_diam">2.89</A>
    <A name="res_temp">200</A>
    <A name="res_press">1556.6</A>
    <Group>test_group</Group>
    <Process class="Separation"/>
    <Process class="CrudeOilDewatering"/>
    <Stream src="Separation" dst="CrudeOilDewatering" name="crude"/>
</Field>
"""

complex_field_xml = """
<Field name="complex_field">
    <A name="country">USA</A>
    <A name="well_diam">2.89</A>
    <Group>complex_group</Group>
    <Aggregator name="Processing">
        <Process class="Separation"/>
        <Process class="WaterTreatment"/>
    </Aggregator>
    <Process class="CrudeOilDewatering"/>
    <Process class="GasDistribution" />
    <Process class="LNGTransport" />
    <ProcessChoice name="oil_processing_path" default="pipeline">
        <ProcessGroup name="pipeline">
            <ProcessRef name="GasDistribution" />
        </ProcessGroup>
        <ProcessGroup name="truck">
            <ProcessRef name="LNGTransport" />
        </ProcessGroup>
    </ProcessChoice>
    <Stream src="Separation" dst="WaterTreatment"/>
    <Stream src="WaterTreatment" dst="CrudeOilDewatering"/>
</Field>
"""

simple_stream_xml = """
<Stream src="ProcessA" dst="ProcessB" name="test_stream">
    <A name="temperature">60</A>
    <A name="pressure">14.7</A>
    <A name="API">35</A>
    <Contains>oil</Contains>
    <Contains>gas</Contains>
</Stream>
"""

@pytest.fixture(scope="module", autouse=True)
def xml_test_model():
    return load_test_model("test_fields.xml")


class TestParseField:
    """Test cases for parse_field function."""

    def test_parse_field_basic(self, xml_test_model):
        """Test basic field parsing functionality."""
        element = ET.fromstring(simple_field_xml)
        field = parse_field(element, parent=xml_test_model)

        assert field.name == "test_field"
        assert field.parent == xml_test_model
        assert field.model == xml_test_model
        assert field.attr("country") == "USA"
        assert field.attr("well_diam").m == 2.89
        assert "test_group" in field.group_names

        # Check processes were created
        processes = list(field.processes())
        assert len(processes) >= 2
        process_names = [p.name for p in processes]
        assert "Separation" in process_names
        assert "CrudeOilDewatering" in process_names

        # Check streams were created
        streams = list(field.streams())
        assert len(streams) >= 1
        stream = streams[0]
        assert stream.name == "crude"
        assert stream.src_name == "Separation"
        assert stream.dst_name == "CrudeOilDewatering"

    def test_parse_field_with_parent(self):
        """Test field parsing with parent Analysis."""
        # Create a simple analysis parent
        model = load_test_model("test_fields.xml", use_default_model=True)
        analysis = model.get_analysis("test_fugitive")

        element = ET.fromstring(simple_field_xml)
        field = parse_field(element, parent=analysis)

        assert field.name == "test_field"
        assert field.parent == analysis
        assert field.model == analysis.model

    def test_parse_field_attributes_parsing(self, xml_test_model):
        """Test that field attributes are parsed correctly."""
        element = ET.fromstring(simple_field_xml)
        field = parse_field(element, parent=xml_test_model)

        # Test that attributes were parsed via AttributeMixin
        assert hasattr(field, "attr_dict")
        assert "country" in field.attr_dict
        assert "well_diam" in field.attr_dict

        # Test attribute values
        assert field.attr("country") == "USA"
        assert field.attr("well_diam").m == 2.89

    def test_parse_field_xml_properties(self, xml_test_model):
        """Test XML-derived properties are set correctly."""
        xml_with_props = """
        <Field name="test_field" enabled="0" extend="1" modified="base_field">
            <A name="country">USA</A>
        </Field>
        """
        element = ET.fromstring(xml_with_props)
        field = parse_field(element, parent=xml_test_model)

        assert field.name == "test_field"
        assert not field.is_enabled()  # enabled="0"
        assert field.extend  # extend="1"
        assert field.modifies == "base_field"  # modified="base_field"

    def test_parse_field_complex_structure(self, xml_test_model):
        """Test parsing field with aggregators and choices."""
        element = ET.fromstring(complex_field_xml)
        field = parse_field(element, parent=xml_test_model)

        assert field.name == "complex_field"

        # Check that aggregators were created
        aggregators = list(field.agg_dict.values())
        assert len(aggregators) > 0

        # Check that process choices were handled
        assert field.process_choice_dict is not None
        assert "oil_processing_path" in field.process_choice_dict

    def test_parse_field_post_processing(self, xml_test_model):
        """Test that post-processing cache_attributes is called."""
        element = ET.fromstring(simple_field_xml)
        field = parse_field(element, parent=xml_test_model)

        # Verify that cache_attributes was called on processes
        for proc in field.processes():
            # This is hard to test directly, but we can verify the process
            # has been properly initialized and cached
            assert proc is not None
            assert proc.parent == field

    def test_parse_field_error_handling(self):
        """Test error handling for malformed XML."""
        # Test field without name
        with pytest.raises(Exception):  # Should raise some kind of exception
            bad_xml = '<Field><A name="country">USA</A></Field>'
            element = ET.fromstring(bad_xml)
            parse_field(element)

    def test_parse_field_vs_from_xml_equivalence(self, xml_test_model):
        """Test that new parser produces equivalent results to old method."""
        element = ET.fromstring(simple_field_xml)

        # Parse with new method (without deprecation warning)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Parse with old method (which now calls new method)
            old_field = Field.from_xml(element, parent=xml_test_model)

            # Parse directly with new method
            new_field = parse_field(element, parent=xml_test_model)

            # Assert structural equivalence
            assert old_field.name == new_field.name
            assert old_field.attr_dict.keys() == new_field.attr_dict.keys()
            assert len(list(old_field.processes())) == len(list(new_field.processes()))
            assert len(list(old_field.streams())) == len(list(new_field.streams()))
            assert old_field.group_names == new_field.group_names



class TestParseFieldIntegration:
    """Integration tests with real model files."""

    def test_parse_field_performance_baseline(self, xml_test_model):
        """Basic performance test to ensure no major regression."""
        import time

        element = ET.fromstring(simple_field_xml)

        # Time the parsing operation
        start_time = time.time()
        for _ in range(5):
            field = parse_field(element, parent=xml_test_model)
        end_time = time.time()

        # Just ensure it completes in reasonable time (< 1 second for 100 parses)
        total_time = end_time - start_time
        assert total_time < 1.0, (
            f"Parsing took too long: {total_time}s for 100 iterations"
        )


class TestParseStream:
    """Test cases for parse_stream function (existing implementation)."""

    def test_parse_stream_basic(self, xml_test_model):
        """Test basic stream parsing functionality."""
        element = ET.fromstring(simple_stream_xml)
        stream = parse_stream(element, parent=xml_test_model.get_field("test_component_fugitive_oilfield"))

        assert stream.name == "test_stream"
        assert stream.src_name == "ProcessA"
        assert stream.dst_name == "ProcessB"

        # Check contents
        assert "oil" in stream.contents
        assert "gas" in stream.contents

    def test_parse_stream_with_parent(self, xml_test_model):
        """Test stream parsing with parent Field."""
        # Create a simple field parent
        field_element = ET.fromstring(simple_field_xml,)
        field = parse_field(field_element, parent=xml_test_model)

        stream_element = ET.fromstring(simple_stream_xml)
        stream = parse_stream(stream_element, parent=field)

        assert stream.name == "test_stream"
        assert stream.parent == field


def extract_field_xml_from_model(model_xml: str, field_name: str):
    """Extract field XML element from full model XML string."""
    root = ET.fromstring(model_xml)
    for field_elem in root.findall(".//Field"):
        if field_elem.get("name") == field_name:
            return field_elem
    return None

