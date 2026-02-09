"""Tests for XML parsing and field-analysis splitting."""
from __future__ import annotations

from lxml import etree

from opgee_xml.parse import FieldUnit, _analysis_matches_field, parse_and_split


class TestAnalysisMatchesField:
    def test_no_group_returns_false(self):
        analysis = etree.Element("Analysis")
        group = etree.SubElement(analysis, "Group")
        group.text = "some_group"
        assert _analysis_matches_field(analysis, None) is False

    def test_literal_match(self):
        analysis = etree.Element("Analysis")
        group = etree.SubElement(analysis, "Group")
        group.text = "group_a"
        assert _analysis_matches_field(analysis, "group_a") is True

    def test_literal_no_match(self):
        analysis = etree.Element("Analysis")
        group = etree.SubElement(analysis, "Group")
        group.text = "group_a"
        assert _analysis_matches_field(analysis, "group_b") is False

    def test_regex_match(self):
        analysis = etree.Element("Analysis")
        group = etree.SubElement(analysis, "Group", regex="1")
        group.text = "group_.*"
        assert _analysis_matches_field(analysis, "group_xyz") is True

    def test_regex_no_match(self):
        analysis = etree.Element("Analysis")
        group = etree.SubElement(analysis, "Group", regex="1")
        group.text = "^exact$"
        assert _analysis_matches_field(analysis, "not_exact") is False

    def test_empty_group_text(self):
        analysis = etree.Element("Analysis")
        group = etree.SubElement(analysis, "Group")
        group.text = ""
        assert _analysis_matches_field(analysis, "anything") is False

    def test_no_groups(self):
        analysis = etree.Element("Analysis")
        assert _analysis_matches_field(analysis, "group_a") is False


class TestParseAndSplit:
    def test_single_field_no_analysis(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1")
        units = list(parse_and_split(root))
        assert len(units) == 1
        assert units[0].field.get("name") == "f1"
        assert units[0].analysis is None

    def test_field_with_matching_analysis(self):
        root = etree.Element("Model")
        analysis = etree.SubElement(root, "Analysis", name="a1")
        group = etree.SubElement(analysis, "Group")
        group.text = "grp"
        etree.SubElement(root, "Field", name="f1", group="grp")

        units = list(parse_and_split(root))
        assert len(units) == 1
        assert units[0].analysis is not None
        assert units[0].analysis.get("name") == "a1"

    def test_field_without_matching_analysis(self):
        root = etree.Element("Model")
        analysis = etree.SubElement(root, "Analysis", name="a1")
        group = etree.SubElement(analysis, "Group")
        group.text = "grp"
        etree.SubElement(root, "Field", name="f1", group="other")

        units = list(parse_and_split(root))
        assert units[0].analysis is None

    def test_multiple_fields(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1")
        etree.SubElement(root, "Field", name="f2")
        units = list(parse_and_split(root))
        assert len(units) == 2

    def test_group_attribute_on_field_unit(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1", group="my_group")
        units = list(parse_and_split(root))
        assert units[0].group == "my_group"

    def test_group_none_when_absent(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1")
        units = list(parse_and_split(root))
        assert units[0].group is None

    def test_returns_iterator(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1")
        result = parse_and_split(root)
        # Should be an iterator, not a list
        assert hasattr(result, "__next__")

    def test_field_unit_dataclass(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1", group="g")
        units = list(parse_and_split(root))
        unit = units[0]
        assert isinstance(unit, FieldUnit)
        assert unit.group == "g"
        assert unit.analysis is None
