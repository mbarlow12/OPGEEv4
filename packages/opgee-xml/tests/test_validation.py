"""Tests for pre- and post-resolution validation."""
from __future__ import annotations

from lxml import etree

from opgee_xml.include import INC_NS
from opgee_xml.validation import validate_post_resolution, validate_pre_resolution


class TestValidatePreResolution:
    def test_valid_model(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field", name="f1")
        errors = validate_pre_resolution(root)
        assert errors == []

    def test_no_fields(self):
        root = etree.Element("Model")
        errors = validate_pre_resolution(root)
        assert any("No <Field>" in e for e in errors)

    def test_field_without_name(self):
        root = etree.Element("Model")
        etree.SubElement(root, "Field")
        errors = validate_pre_resolution(root)
        assert any("without name" in e for e in errors)

    def test_unknown_inc_element(self):
        root = etree.Element("Model")
        field = etree.SubElement(root, "Field", name="f1")
        inc = etree.SubElement(field, f"{{{INC_NS}}}bogus_type")
        inc.text = "value"
        errors = validate_pre_resolution(root)
        assert any("Unknown inc element" in e for e in errors)

    def test_missing_fragment_file(self):
        root = etree.Element("Model")
        field = etree.SubElement(root, "Field", name="f1")
        inc = etree.SubElement(field, f"{{{INC_NS}}}template")
        inc.text = "nonexistent_template"
        errors = validate_pre_resolution(root)
        assert any("Fragment not found" in e for e in errors)

    def test_valid_inc_element(self):
        root = etree.Element("Model")
        field = etree.SubElement(root, "Field", name="f1")
        inc = etree.SubElement(field, f"{{{INC_NS}}}template")
        inc.text = "template"
        errors = validate_pre_resolution(root)
        assert errors == []

    def test_inc_none_value_is_valid(self):
        root = etree.Element("Model")
        field = etree.SubElement(root, "Field", name="f1")
        inc = etree.SubElement(field, f"{{{INC_NS}}}oil_sands_mine")
        inc.text = "None"
        errors = validate_pre_resolution(root)
        assert errors == []


class TestValidatePostResolution:
    def test_valid_field(self):
        from opgee_input import FieldInput
        from opgee_input.processes import Separation

        field = FieldInput(name="test", processes=[Separation()])
        errors = validate_post_resolution(field)
        assert errors == []

    def test_no_processes(self):
        from opgee_input import FieldInput

        field = FieldInput(name="test", processes=[])
        errors = validate_post_resolution(field)
        assert any("no processes" in e for e in errors)
