"""Tests for XML element merging logic."""
from __future__ import annotations

from lxml import etree

from opgee_xml.merge import match_element, merge_element, merge_elements


class TestMatchElement:
    def test_same_tag_no_attrs(self):
        a = etree.Element("Foo")
        b = etree.Element("Foo")
        assert match_element(a, b) is True

    def test_different_tags(self):
        a = etree.Element("Foo")
        b = etree.Element("Bar")
        assert match_element(a, b) is False

    def test_same_tag_same_name(self):
        a = etree.Element("Stream", name="x")
        b = etree.Element("Stream", name="x")
        assert match_element(a, b) is True

    def test_same_tag_different_name(self):
        a = etree.Element("Stream", name="x")
        b = etree.Element("Stream", name="y")
        assert match_element(a, b) is False

    def test_one_has_name_other_does_not(self):
        a = etree.Element("Stream", name="x")
        b = etree.Element("Stream")
        assert match_element(a, b) is False

    def test_same_boundary(self):
        a = etree.Element("Boundary", boundary="Production")
        b = etree.Element("Boundary", boundary="Production")
        assert match_element(a, b) is True

    def test_different_boundary(self):
        a = etree.Element("Boundary", boundary="Production")
        b = etree.Element("Boundary", boundary="Transportation")
        assert match_element(a, b) is False


class TestMergeElement:
    def test_append_new_element(self):
        parent = etree.Element("Root")
        new = etree.Element("Child")
        new.text = "value"
        merge_element(parent, new)
        assert len(parent) == 1
        assert parent[0].tag == "Child"
        assert parent[0].text == "value"

    def test_update_existing_text(self):
        parent = etree.Element("Root")
        existing = etree.SubElement(parent, "Child")
        existing.text = "old"
        new = etree.Element("Child")
        new.text = "new"
        merge_element(parent, new)
        assert len(parent) == 1
        assert parent[0].text == "new"

    def test_delete_matching(self):
        parent = etree.Element("Root")
        etree.SubElement(parent, "Child")
        new = etree.Element("Child", delete="1")
        merge_element(parent, new)
        assert len(parent) == 0

    def test_recursive_merge(self):
        parent = etree.Element("Root")
        child = etree.SubElement(parent, "Child")
        etree.SubElement(child, "Inner")

        new_child = etree.Element("Child")
        new_inner = etree.SubElement(new_child, "Inner")
        new_inner.text = "updated"

        merge_element(parent, new_child)
        assert parent[0].find("Inner").text == "updated"


class TestMergeElements:
    def test_merge_list(self):
        parent = etree.Element("Root")
        etree.SubElement(parent, "A")
        etree.SubElement(parent, "B")

        new_elts = [
            etree.Element("A"),
            etree.Element("C"),
        ]
        new_elts[0].text = "updated_a"
        new_elts[1].text = "new_c"

        merge_elements(parent, new_elts)
        tags = [c.tag for c in parent]
        assert "A" in tags
        assert "B" in tags
        assert "C" in tags
        assert parent.find("A").text == "updated_a"
        assert parent.find("C").text == "new_c"

    def test_merge_empty_list(self):
        parent = etree.Element("Root")
        etree.SubElement(parent, "A")
        merge_elements(parent, [])
        assert len(parent) == 1

    def test_merge_with_named_elements(self):
        parent = etree.Element("Root")
        etree.SubElement(parent, "Stream", name="s1")
        etree.SubElement(parent, "Stream", name="s2")

        new = etree.Element("Stream", name="s1")
        new.text = "updated"
        merge_elements(parent, [new])

        # s1 should be updated, s2 untouched
        streams = parent.findall("Stream")
        assert len(streams) == 2
        s1 = [s for s in streams if s.get("name") == "s1"][0]
        assert s1.text == "updated"
