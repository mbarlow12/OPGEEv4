"""Tests for opgee.input.xml.parse — parsing and splitting XML into FieldUnits."""
from __future__ import annotations

from opgee.input.xml.parse import parse_and_split


class TestSingleFieldNoAnalysis:
    """Single Field with no Analysis element -> FieldUnit with analysis=None."""

    def test_returns_one_field_unit(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert len(units) == 1

    def test_field_element_present(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].field.get("name") == "field1"

    def test_analysis_is_none(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].analysis is None


class TestSingleFieldWithMatchingAnalysis:
    """Single Field with a matching Analysis (via FieldRef) -> analysis set."""

    def test_analysis_is_set(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="field1"/>\n'
            '  </Analysis>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert len(units) == 1
        assert units[0].analysis is not None

    def test_analysis_has_correct_name(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="field1"/>\n'
            '  </Analysis>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].analysis.get("name") == "a1"

    def test_field_element_present(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="field1"/>\n'
            '  </Analysis>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].field.get("name") == "field1"


class TestMultipleFields:
    """Multiple Fields -> returns multiple FieldUnits."""

    def test_returns_correct_count(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="f1"/>\n'
            '    <FieldRef name="f2"/>\n'
            '  </Analysis>\n'
            '  <Field name="f1"/>\n'
            '  <Field name="f2"/>\n'
            '  <Field name="f3"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert len(units) == 3

    def test_field_names_match(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="f1"/>\n'
            '    <FieldRef name="f2"/>\n'
            '  </Analysis>\n'
            '  <Field name="f1"/>\n'
            '  <Field name="f2"/>\n'
            '  <Field name="f3"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        names = [u.field.get("name") for u in units]
        assert names == ["f1", "f2", "f3"]

    def test_matched_fields_have_analysis(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="f1"/>\n'
            '    <FieldRef name="f2"/>\n'
            '  </Analysis>\n'
            '  <Field name="f1"/>\n'
            '  <Field name="f2"/>\n'
            '  <Field name="f3"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].analysis is not None
        assert units[1].analysis is not None

    def test_unmatched_field_has_no_analysis(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="f1"/>\n'
            '    <FieldRef name="f2"/>\n'
            '  </Analysis>\n'
            '  <Field name="f1"/>\n'
            '  <Field name="f2"/>\n'
            '  <Field name="f3"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[2].analysis is None


class TestFieldNoMatchingFieldRef:
    """Field with an Analysis that has no matching FieldRef -> analysis=None."""

    def test_analysis_is_none(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="other_field"/>\n'
            '  </Analysis>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert len(units) == 1
        assert units[0].analysis is None

    def test_analysis_with_no_fieldrefs(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1"/>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].analysis is None


class TestMultipleAnalysesFieldMatchesOne:
    """Multiple analyses, field matches one -> correct analysis associated."""

    def test_field_matches_second_analysis(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="other"/>\n'
            '  </Analysis>\n'
            '  <Analysis name="a2">\n'
            '    <FieldRef name="field1"/>\n'
            '  </Analysis>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert len(units) == 1
        assert units[0].analysis is not None
        assert units[0].analysis.get("name") == "a2"

    def test_field_matches_first_analysis(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="field1"/>\n'
            '  </Analysis>\n'
            '  <Analysis name="a2">\n'
            '    <FieldRef name="other"/>\n'
            '  </Analysis>\n'
            '  <Field name="field1"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert units[0].analysis.get("name") == "a1"

    def test_multiple_fields_different_analyses(self, tmp_path):
        xml_file = tmp_path / "model.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n'
            '<Model>\n'
            '  <Analysis name="a1">\n'
            '    <FieldRef name="f1"/>\n'
            '  </Analysis>\n'
            '  <Analysis name="a2">\n'
            '    <FieldRef name="f2"/>\n'
            '  </Analysis>\n'
            '  <Field name="f1"/>\n'
            '  <Field name="f2"/>\n'
            '</Model>\n'
        )

        units = parse_and_split(xml_file)

        assert len(units) == 2
        assert units[0].analysis.get("name") == "a1"
        assert units[1].analysis.get("name") == "a2"
