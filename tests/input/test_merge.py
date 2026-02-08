"""Tests for opgee.input.xml.merge — element matching and merging."""
from __future__ import annotations

from lxml.builder import E
from lxml import etree

from opgee.input.xml.merge import match_element, merge_element, merge_elements


# ---------------------------------------------------------------------------
# match_element
# ---------------------------------------------------------------------------
class TestMatchElement:
    """Tests for match_element(elt1, elt2)."""

    def test_same_tag_no_identity_attrs(self):
        """Elements with same tag and no identity attrs match."""
        assert match_element(E.Process(), E.Process()) is True

    def test_same_tag_same_name(self):
        assert match_element(E.Field(name="f1"), E.Field(name="f1")) is True

    def test_same_tag_different_name(self):
        assert match_element(E.Field(name="f1"), E.Field(name="f2")) is False

    def test_different_tags(self):
        assert match_element(E.Field(name="f1"), E.Process(name="f1")) is False

    def test_same_tag_same_boundary(self):
        assert match_element(
            E.Analysis(boundary="Production"),
            E.Analysis(boundary="Production"),
        ) is True

    def test_same_tag_different_boundary(self):
        assert match_element(
            E.Analysis(boundary="Production"),
            E.Analysis(boundary="Transportation"),
        ) is False

    def test_one_has_name_other_does_not(self):
        """If only one element has an identity attr, they do not match."""
        assert match_element(E.Field(name="f1"), E.Field()) is False

    def test_one_has_boundary_other_does_not(self):
        assert match_element(E.Analysis(boundary="Production"), E.Analysis()) is False

    def test_neither_has_identity_attr_different_non_identity_attrs(self):
        """Non-identity attributes are ignored for matching."""
        a = E.A(value="10")
        b = E.A(value="20")
        assert match_element(a, b) is True

    def test_same_tag_both_identity_attrs_match(self):
        a = E.X(name="x", boundary="b")
        b = E.X(name="x", boundary="b")
        assert match_element(a, b) is True

    def test_same_tag_name_matches_boundary_differs(self):
        a = E.X(name="x", boundary="b1")
        b = E.X(name="x", boundary="b2")
        assert match_element(a, b) is False

    def test_process_tags_no_attrs(self):
        """Two bare Process tags match by tag alone."""
        assert match_element(E.Process(), E.Process()) is True


# ---------------------------------------------------------------------------
# merge_element
# ---------------------------------------------------------------------------
class TestMergeElement:
    """Tests for merge_element(parent, new_elt)."""

    def test_no_match_appends(self):
        """When no child matches, a copy of new_elt is appended."""
        parent = E.Root(E.A(name="a1"))
        merge_element(parent, E.B(name="b1"))

        tags = [ch.tag for ch in parent]
        assert tags == ["A", "B"]

    def test_append_uses_deepcopy(self):
        """Appended element should be a copy, not the original."""
        parent = E.Root()
        original = E.A(name="new")
        original.text = "hello"

        merge_element(parent, original)

        appended = parent[0]
        assert appended is not original
        assert appended.text == "hello"
        assert appended.get("name") == "new"

    def test_match_by_tag_updates_text(self):
        """Matching by tag (no identity attrs) updates text."""
        parent = E.Root(E.A("old-text"))
        merge_element(parent, E.A("new-text"))

        assert len(parent) == 1
        assert parent[0].text == "new-text"

    def test_match_by_name_updates_text(self):
        """Matching by name attr updates text of existing child."""
        parent = E.Root(E.Field("old", name="f1"))
        merge_element(parent, E.Field("new", name="f1"))

        assert len(parent) == 1
        assert parent[0].text == "new"

    def test_different_name_appends(self):
        """Elements with different names do not match; new one is appended."""
        parent = E.Root(E.Field(name="f1"))
        merge_element(parent, E.Field(name="f2"))

        assert len(parent) == 2
        names = [ch.get("name") for ch in parent]
        assert names == ["f1", "f2"]

    def test_delete_removes_matching_child(self):
        """new_elt with delete='1' removes the matching child."""
        parent = E.Root(E.Field(name="f1"), E.Field(name="f2"))
        merge_element(parent, E.Field(name="f1", delete="1"))

        assert len(parent) == 1
        assert parent[0].get("name") == "f2"

    def test_delete_no_match_appends(self):
        """delete='1' on non-matching element still appends a copy."""
        parent = E.Root(E.Field(name="f1"))
        merge_element(parent, E.Field(name="no-match", delete="1"))

        assert len(parent) == 2

    def test_recursive_merge_children(self):
        """Children of a matching element are recursively merged."""
        parent = E.Root(
            E.Field(
                E.A("10", name="attr1"),
                E.A("20", name="attr2"),
                name="f1",
            )
        )
        new_field = E.Field(
            E.A("99", name="attr2"),
            E.A("30", name="attr3"),
            name="f1",
        )
        merge_element(parent, new_field)

        # Still one Field
        assert len(parent) == 1
        field = parent[0]
        children = {ch.get("name"): ch.text for ch in field}
        assert children == {"attr1": "10", "attr2": "99", "attr3": "30"}

    def test_recursive_merge_deep(self):
        """Merge works at multiple nesting levels."""
        parent = E.Root(
            E.Model(
                E.Field(
                    E.A("original", name="x"),
                    name="f1",
                ),
                name="m1",
            )
        )
        override = E.Model(
            E.Field(
                E.A("updated", name="x"),
                name="f1",
            ),
            name="m1",
        )
        merge_element(parent, override)

        assert len(parent) == 1
        field = parent[0][0]
        assert field[0].text == "updated"

    def test_text_set_to_none_when_new_elt_has_no_text(self):
        """If the new element has no text, matched child text is set to None."""
        parent = E.Root(E.A("old-text"))
        merge_element(parent, E.A())

        assert parent[0].text is None

    def test_no_mutation_of_new_elt(self):
        """new_elt and its children should not be mutated by merge."""
        parent = E.Root(E.Field(name="f1"))
        new_elt = E.Field(E.A("val", name="a1"), name="f2")

        # Capture original state
        original_xml = etree.tostring(new_elt)
        merge_element(parent, new_elt)

        # new_elt was appended as a deepcopy, so original should be unchanged
        assert etree.tostring(new_elt) == original_xml


# ---------------------------------------------------------------------------
# merge_elements
# ---------------------------------------------------------------------------
class TestMergeElements:
    """Tests for merge_elements(parent, elt_list)."""

    def test_batch_merge(self):
        """Multiple elements are merged in order."""
        parent = E.Root(E.A("1", name="a1"), E.A("2", name="a2"))
        merge_elements(
            parent,
            [
                E.A("10", name="a1"),  # update
                E.A("3", name="a3"),   # append
            ],
        )

        texts = {ch.get("name"): ch.text for ch in parent}
        assert texts == {"a1": "10", "a2": "2", "a3": "3"}

    def test_mix_of_appends_and_updates(self):
        """Merge list with updates, appends, and deletes."""
        parent = E.Root(
            E.Field(name="f1"),
            E.Field(name="f2"),
            E.Field(name="f3"),
        )
        merge_elements(
            parent,
            [
                E.Field(name="f2", delete="1"),  # delete
                E.Field(name="f4"),               # append
                E.Field(name="f1"),               # update (no-op, no text change)
            ],
        )

        names = [ch.get("name") for ch in parent]
        assert names == ["f1", "f3", "f4"]

    def test_empty_list_is_noop(self):
        parent = E.Root(E.A("1", name="a1"))
        merge_elements(parent, [])
        assert len(parent) == 1

    def test_sequential_updates_to_same_element(self):
        """Two updates to the same element apply in order."""
        parent = E.Root(E.A("orig", name="x"))
        merge_elements(
            parent,
            [
                E.A("first", name="x"),
                E.A("second", name="x"),
            ],
        )

        assert len(parent) == 1
        assert parent[0].text == "second"
