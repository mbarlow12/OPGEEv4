"""Tests for <inc:*> resolution and fragment inclusion."""
from __future__ import annotations

import pytest
from lxml import etree

from opgee_xml.include import (
    INC_NS,
    _load_fragment,
    _slugify,
    resolve_includes,
    unwrap_fragments,
)


class TestSlugify:
    def test_spaces_to_underscores(self):
        assert _slugify("Acid Gas") == "acid_gas"

    def test_hyphens_to_underscores(self):
        assert _slugify("CO2-EOR Membrane") == "co2_eor_membrane"

    def test_already_lowercase(self):
        assert _slugify("minimal") == "minimal"

    def test_mixed_case(self):
        assert _slugify("Sour Gas Reinjection") == "sour_gas_reinjection"


class TestLoadFragment:
    def test_load_template(self):
        root = _load_fragment("template", "template")
        assert root.tag == "fragment"
        # Template should have process elements and streams
        assert len(list(root)) > 0

    def test_load_gas_processing_path(self):
        root = _load_fragment("gas_processing_path", "minimal")
        assert root.tag == "fragment"

    def test_unknown_attr_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown inc element"):
            _load_fragment("nonexistent_type", "value")

    def test_missing_fragment_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Fragment not found"):
            _load_fragment("template", "does_not_exist")


class TestResolveIncludes:
    def _make_field_with_inc(self, attr_name: str, value: str) -> etree._Element:
        """Build a <Field> with one <inc:attr_name>value</inc:attr_name>."""
        field = etree.Element("Field", name="test")
        inc = etree.SubElement(field, f"{{{INC_NS}}}{attr_name}")
        inc.text = value
        return field

    def test_resolve_template(self):
        field = self._make_field_with_inc("template", "template")
        choices = resolve_includes(field)
        assert choices == {"template": "template"}
        # inc element should be removed
        assert field.findall(f"{{{INC_NS}}}*") == []
        # Fragment content should be merged in
        assert len(list(field)) > 0

    def test_resolve_none_value(self):
        field = self._make_field_with_inc("oil_sands_mine", "None")
        choices = resolve_includes(field)
        assert choices == {"oil_sands_mine": "None"}
        # inc element should be removed
        assert field.findall(f"{{{INC_NS}}}*") == []
        # No fragment content should be merged
        assert len(list(field)) == 0

    def test_resolve_empty_value(self):
        field = self._make_field_with_inc("gas_processing_path", "")
        choices = resolve_includes(field)
        assert choices == {"gas_processing_path": ""}
        assert field.findall(f"{{{INC_NS}}}*") == []

    def test_resolve_returns_choices_dict(self):
        field = etree.Element("Field", name="test")
        inc1 = etree.SubElement(field, f"{{{INC_NS}}}gas_processing_path")
        inc1.text = "minimal"
        inc2 = etree.SubElement(field, f"{{{INC_NS}}}oil_sands_mine")
        inc2.text = "None"
        choices = resolve_includes(field)
        assert "gas_processing_path" in choices
        assert "oil_sands_mine" in choices
        assert choices["gas_processing_path"] == "minimal"
        assert choices["oil_sands_mine"] == "None"

    def test_no_inc_elements_returns_empty(self):
        field = etree.Element("Field", name="test")
        choices = resolve_includes(field)
        assert choices == {}


class TestUnwrapFragments:
    def test_unwrap_single_fragment(self):
        root = etree.Element("Root")
        frag = etree.SubElement(root, "fragment")
        etree.SubElement(frag, "Child1")
        etree.SubElement(frag, "Child2")

        unwrap_fragments(root)

        tags = [child.tag for child in root]
        assert tags == ["Child1", "Child2"]

    def test_unwrap_nested_fragments(self):
        root = etree.Element("Root")
        frag_outer = etree.SubElement(root, "fragment")
        frag_inner = etree.SubElement(frag_outer, "fragment")
        etree.SubElement(frag_inner, "Deep")
        etree.SubElement(frag_outer, "Shallow")

        unwrap_fragments(root)

        tags = [child.tag for child in root]
        assert "Deep" in tags
        assert "Shallow" in tags
        assert "fragment" not in tags

    def test_no_fragments_is_noop(self):
        root = etree.Element("Root")
        etree.SubElement(root, "A")
        etree.SubElement(root, "B")

        unwrap_fragments(root)

        tags = [child.tag for child in root]
        assert tags == ["A", "B"]

    def test_empty_fragment_removed(self):
        root = etree.Element("Root")
        etree.SubElement(root, "fragment")

        unwrap_fragments(root)

        assert len(list(root)) == 0
