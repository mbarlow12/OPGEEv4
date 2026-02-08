"""Tests for opgee.input.xml.validation — pre- and post-resolution validation."""
from __future__ import annotations

from lxml import etree
from lxml.builder import E

from opgee.input.models.field import FieldModel
from opgee.input.xml.validation import validate_pre_resolution, validate_post_resolution


# ---------------------------------------------------------------------------
# validate_pre_resolution
# ---------------------------------------------------------------------------


class TestPreResolutionValid:
    """Model with a named Field -> no errors."""

    def test_no_errors(self):
        root = E.Model(E.Field(name="test"))

        errors = validate_pre_resolution(root)

        assert errors == []

    def test_multiple_valid_fields(self):
        root = E.Model(
            E.Field(name="f1"),
            E.Field(name="f2"),
        )

        errors = validate_pre_resolution(root)

        assert errors == []


class TestPreResolutionNoFields:
    """Model with no Field elements -> error."""

    def test_error_message(self):
        root = E.Model()

        errors = validate_pre_resolution(root)

        assert len(errors) == 1
        assert "No <Field> elements found" in errors[0]

    def test_non_field_children_still_error(self):
        root = E.Model(E.Analysis(name="a1"))

        errors = validate_pre_resolution(root)

        assert any("No <Field> elements found" in e for e in errors)


class TestPreResolutionNoName:
    """Model with a Field missing the name attribute -> error."""

    def test_error_message(self):
        root = E.Model(E.Field())

        errors = validate_pre_resolution(root)

        assert any("without name" in e for e in errors)

    def test_mixed_named_and_unnamed(self):
        root = E.Model(
            E.Field(name="ok"),
            E.Field(),
        )

        errors = validate_pre_resolution(root)

        assert len(errors) == 1
        assert "without name" in errors[0]


class TestPreResolutionBadXInclude:
    """Model with xi:include pointing to non-existent file -> error."""

    def test_missing_href_error(self):
        xi_ns = "http://www.w3.org/2001/XInclude"
        xml_str = (
            f'<Model xmlns:xi="{xi_ns}">'
            f'  <Field name="f1"/>'
            f'  <xi:include href="nonexistent_file.xml"/>'
            f'</Model>'
        )
        root = etree.fromstring(xml_str.encode())

        errors = validate_pre_resolution(root)

        assert any("XInclude href not found" in e for e in errors)
        assert any("nonexistent_file.xml" in e for e in errors)

    def test_valid_field_with_bad_include_still_reports_include_error(self):
        xi_ns = "http://www.w3.org/2001/XInclude"
        xml_str = (
            f'<Model xmlns:xi="{xi_ns}">'
            f'  <Field name="valid"/>'
            f'  <xi:include href="does_not_exist.xml"/>'
            f'</Model>'
        )
        root = etree.fromstring(xml_str.encode())

        errors = validate_pre_resolution(root)

        # Field is valid, so only the include error
        assert len(errors) == 1
        assert "XInclude href not found" in errors[0]


# ---------------------------------------------------------------------------
# validate_post_resolution
# ---------------------------------------------------------------------------


class TestPostResolutionValid:
    """FieldModel with processes -> no errors."""

    def test_no_errors(self):
        field_xml = etree.fromstring(
            '<Field name="test"><Separation/></Field>'
        )
        model = FieldModel.from_xml_tree(field_xml)

        errors = validate_post_resolution(model)

        assert errors == []

    def test_multiple_processes(self):
        field_xml = etree.fromstring(
            '<Field name="test">'
            '  <Separation/>'
            '  <Flaring/>'
            '</Field>'
        )
        model = FieldModel.from_xml_tree(field_xml)

        errors = validate_post_resolution(model)

        assert errors == []


class TestPostResolutionNoProcesses:
    """FieldModel with no processes -> error."""

    def test_error_message(self):
        model = FieldModel(name="empty")

        errors = validate_post_resolution(model)

        assert len(errors) == 1
        assert "no processes" in errors[0]

    def test_error_includes_field_name(self):
        model = FieldModel(name="my_field")

        errors = validate_post_resolution(model)

        assert "my_field" in errors[0]
