"""Tests for opgee.input.xml.parse — parsing and splitting XML into FieldUnits."""
from __future__ import annotations

from lxml import etree
from lxml.builder import E

from opgee.input.xml.parse import FieldUnit, _analysis_matches_field, parse_and_split


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _root(*children: etree._Element) -> etree._Element:
    """Build a <Model> root from child elements."""
    return E.Model(*children)


# ---------------------------------------------------------------------------
# _analysis_matches_field (unit tests for the helper)
# ---------------------------------------------------------------------------

class TestAnalysisMatchesField:
    """Direct tests for the _analysis_matches_field helper."""

    def test_literal_match(self):
        analysis = E.Analysis(E.Group("oil"), name="a1")
        assert _analysis_matches_field(analysis, "oil") is True

    def test_literal_no_match(self):
        analysis = E.Analysis(E.Group("oil"), name="a1")
        assert _analysis_matches_field(analysis, "gas") is False

    def test_field_group_none_returns_false(self):
        analysis = E.Analysis(E.Group("oil"), name="a1")
        assert _analysis_matches_field(analysis, None) is False

    def test_regex_match(self):
        group = E.Group("oil.*", regex="1")
        analysis = E.Analysis(group, name="a1")
        assert _analysis_matches_field(analysis, "oil-heavy") is True

    def test_regex_no_match(self):
        group = E.Group("^gas$", regex="1")
        analysis = E.Analysis(group, name="a1")
        assert _analysis_matches_field(analysis, "oil") is False

    def test_regex_true_string(self):
        group = E.Group("oil", regex="true")
        analysis = E.Analysis(group, name="a1")
        assert _analysis_matches_field(analysis, "oil-field") is True

    def test_empty_group_text_skipped(self):
        group = etree.SubElement(E.Analysis(name="a1"), "Group")
        analysis = group.getparent()
        assert _analysis_matches_field(analysis, "anything") is False

    def test_multiple_groups_first_matches(self):
        analysis = E.Analysis(E.Group("gas"), E.Group("oil"), name="a1")
        assert _analysis_matches_field(analysis, "gas") is True

    def test_multiple_groups_second_matches(self):
        analysis = E.Analysis(E.Group("gas"), E.Group("oil"), name="a1")
        assert _analysis_matches_field(analysis, "oil") is True

    def test_no_groups_returns_false(self):
        analysis = E.Analysis(name="a1")
        assert _analysis_matches_field(analysis, "oil") is False


# ---------------------------------------------------------------------------
# parse_and_split — generator behavior
# ---------------------------------------------------------------------------

class TestGeneratorBehavior:
    """parse_and_split returns an iterator, not a list."""

    def test_returns_iterator(self):
        root = _root(E.Field(name="f1"))
        result = parse_and_split(root)
        assert hasattr(result, "__next__")

    def test_can_convert_to_list(self):
        root = _root(E.Field(name="f1"))
        units = list(parse_and_split(root))
        assert len(units) == 1
        assert isinstance(units[0], FieldUnit)


# ---------------------------------------------------------------------------
# Single field, no analysis
# ---------------------------------------------------------------------------

class TestSingleFieldNoAnalysis:
    """Single Field with no Analysis element -> FieldUnit with analysis=None."""

    def test_returns_one_field_unit(self):
        root = _root(E.Field(name="field1"))
        units = list(parse_and_split(root))
        assert len(units) == 1

    def test_field_element_present(self):
        root = _root(E.Field(name="field1"))
        units = list(parse_and_split(root))
        assert units[0].field.get("name") == "field1"

    def test_analysis_is_none(self):
        root = _root(E.Field(name="field1"))
        units = list(parse_and_split(root))
        assert units[0].analysis is None


# ---------------------------------------------------------------------------
# Single field with matching analysis (via Group)
# ---------------------------------------------------------------------------

class TestSingleFieldWithMatchingAnalysis:
    """Single Field with a matching Analysis (via Group) -> analysis set."""

    def test_analysis_is_set(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="field1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert len(units) == 1
        assert units[0].analysis is not None

    def test_analysis_has_correct_name(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="field1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis.get("name") == "a1"

    def test_field_element_present(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="field1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert units[0].field.get("name") == "field1"


# ---------------------------------------------------------------------------
# Multiple fields
# ---------------------------------------------------------------------------

class TestMultipleFields:
    """Multiple Fields -> returns multiple FieldUnits."""

    def test_returns_correct_count(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="f1", group="oil"),
            E.Field(name="f2", group="oil"),
            E.Field(name="f3"),
        )
        units = list(parse_and_split(root))
        assert len(units) == 3

    def test_field_names_match(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="f1", group="oil"),
            E.Field(name="f2", group="oil"),
            E.Field(name="f3"),
        )
        units = list(parse_and_split(root))
        names = [u.field.get("name") for u in units]
        assert names == ["f1", "f2", "f3"]

    def test_matched_fields_have_analysis(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="f1", group="oil"),
            E.Field(name="f2", group="oil"),
            E.Field(name="f3"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis is not None
        assert units[1].analysis is not None

    def test_unmatched_field_has_no_analysis(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="f1", group="oil"),
            E.Field(name="f2", group="oil"),
            E.Field(name="f3"),
        )
        units = list(parse_and_split(root))
        assert units[2].analysis is None


# ---------------------------------------------------------------------------
# Field with no matching group
# ---------------------------------------------------------------------------

class TestFieldNoMatchingGroup:
    """Field whose group attribute doesn't match any Analysis Group -> analysis=None."""

    def test_analysis_is_none_when_group_differs(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="field1", group="gas"),
        )
        units = list(parse_and_split(root))
        assert len(units) == 1
        assert units[0].analysis is None

    def test_analysis_is_none_when_no_group_attr(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Field(name="field1"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis is None

    def test_analysis_with_no_groups(self):
        root = _root(
            E.Analysis(name="a1"),
            E.Field(name="field1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis is None


# ---------------------------------------------------------------------------
# Multiple analyses — first match wins
# ---------------------------------------------------------------------------

class TestMultipleAnalysesFirstMatchWins:
    """Multiple analyses, field matches one -> correct analysis associated."""

    def test_field_matches_second_analysis(self):
        root = _root(
            E.Analysis(E.Group("gas"), name="a1"),
            E.Analysis(E.Group("oil"), name="a2"),
            E.Field(name="field1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert len(units) == 1
        assert units[0].analysis is not None
        assert units[0].analysis.get("name") == "a2"

    def test_field_matches_first_analysis(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Analysis(E.Group("gas"), name="a2"),
            E.Field(name="field1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis.get("name") == "a1"

    def test_multiple_fields_different_analyses(self):
        root = _root(
            E.Analysis(E.Group("oil"), name="a1"),
            E.Analysis(E.Group("gas"), name="a2"),
            E.Field(name="f1", group="oil"),
            E.Field(name="f2", group="gas"),
        )
        units = list(parse_and_split(root))
        assert len(units) == 2
        assert units[0].analysis.get("name") == "a1"
        assert units[1].analysis.get("name") == "a2"


# ---------------------------------------------------------------------------
# Regex matching
# ---------------------------------------------------------------------------

class TestRegexMatching:
    """Group with regex="1" uses regex matching against field group."""

    def test_regex_matches_field_group(self):
        root = _root(
            E.Analysis(E.Group("oil.*", regex="1"), name="a1"),
            E.Field(name="f1", group="oil-heavy"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis is not None
        assert units[0].analysis.get("name") == "a1"

    def test_regex_no_match(self):
        root = _root(
            E.Analysis(E.Group("^gas$", regex="1"), name="a1"),
            E.Field(name="f1", group="oil"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis is None

    def test_regex_mixed_with_literal(self):
        root = _root(
            E.Analysis(
                E.Group("gas"),
                E.Group("oil-.*", regex="1"),
                name="a1",
            ),
            E.Field(name="f1", group="oil-heavy"),
            E.Field(name="f2", group="gas"),
        )
        units = list(parse_and_split(root))
        assert units[0].analysis.get("name") == "a1"
        assert units[1].analysis.get("name") == "a1"
