"""Tests for opgee.input.xml.resolve — XInclude resolution and fragment unwrapping."""
from __future__ import annotations

from lxml import etree
from lxml.builder import E

from opgee.input.xml.resolve import resolve_includes, unwrap_fragments


# ---------------------------------------------------------------------------
# unwrap_fragments
# ---------------------------------------------------------------------------


class TestUnwrapFragmentsSingleFragment:
    """Single <fragment> with children -> children moved to parent, fragment removed."""

    def test_children_moved_to_parent(self):
        root = E.Field(
            E.fragment(
                E.Process(name="A"),
                E.Process(name="B"),
            ),
        )
        unwrap_fragments(root)

        assert len(root) == 2
        assert root[0].tag == "Process"
        assert root[0].get("name") == "A"
        assert root[1].tag == "Process"
        assert root[1].get("name") == "B"

    def test_fragment_element_removed(self):
        root = E.Field(
            E.fragment(E.Process(name="X")),
        )
        unwrap_fragments(root)

        assert root.find("fragment") is None


class TestUnwrapFragmentsEmpty:
    """Empty <fragment> -> removed with no children added."""

    def test_empty_fragment_removed(self):
        root = E.Field(E.fragment())
        unwrap_fragments(root)

        assert len(root) == 0
        assert root.find("fragment") is None

    def test_empty_fragment_among_siblings(self):
        root = E.Field(
            E.Process(name="before"),
            E.fragment(),
            E.Process(name="after"),
        )
        unwrap_fragments(root)

        assert len(root) == 2
        assert root[0].get("name") == "before"
        assert root[1].get("name") == "after"


class TestUnwrapFragmentsMultiple:
    """Multiple <fragment> elements -> all unwrapped."""

    def test_two_fragments_both_unwrapped(self):
        root = E.Field(
            E.fragment(E.Process(name="A")),
            E.fragment(E.Stream(src="A", dst="B")),
        )
        unwrap_fragments(root)

        assert root.find("fragment") is None
        assert len(root) == 2
        assert root[0].tag == "Process"
        assert root[1].tag == "Stream"

    def test_three_fragments_all_unwrapped(self):
        root = E.Field(
            E.fragment(E.Process(name="X")),
            E.fragment(E.Process(name="Y")),
            E.fragment(E.Process(name="Z")),
        )
        unwrap_fragments(root)

        assert root.find("fragment") is None
        names = [child.get("name") for child in root]
        assert names == ["X", "Y", "Z"]


class TestUnwrapFragmentsNested:
    """Nested fragments (fragment inside fragment) -> both unwrapped."""

    def test_nested_fragments_fully_unwrapped(self):
        root = E.Field(
            E.fragment(
                E.Process(name="outer"),
                E.fragment(
                    E.Process(name="inner"),
                ),
            ),
        )
        unwrap_fragments(root)

        assert root.find("fragment") is None
        assert root.find(".//fragment") is None
        names = [child.get("name") for child in root]
        assert names == ["outer", "inner"]

    def test_deeply_nested_fragments(self):
        root = E.Field(
            E.fragment(
                E.fragment(
                    E.fragment(
                        E.Process(name="deep"),
                    ),
                ),
            ),
        )
        unwrap_fragments(root)

        assert root.find(".//fragment") is None
        assert len(root) == 1
        assert root[0].get("name") == "deep"


class TestUnwrapFragmentsOrder:
    """Fragment children appear at the fragment's original position."""

    def test_children_inserted_at_fragment_position(self):
        root = E.Field(
            E.Process(name="first"),
            E.fragment(
                E.Process(name="frag_a"),
                E.Process(name="frag_b"),
            ),
            E.Process(name="last"),
        )
        unwrap_fragments(root)

        names = [child.get("name") for child in root]
        assert names == ["first", "frag_a", "frag_b", "last"]

    def test_multiple_fragments_preserve_relative_order(self):
        root = E.Field(
            E.Process(name="p1"),
            E.fragment(E.Process(name="f1a"), E.Process(name="f1b")),
            E.Process(name="p2"),
            E.fragment(E.Process(name="f2a")),
            E.Process(name="p3"),
        )
        unwrap_fragments(root)

        names = [child.get("name") for child in root]
        assert names == ["p1", "f1a", "f1b", "p2", "f2a", "p3"]


class TestUnwrapFragmentsPreservesContent:
    """Fragment children keep their attributes and sub-elements."""

    def test_children_keep_attributes(self):
        root = E.Field(
            E.fragment(
                E.Stream(src="A", dst="B", name="my-stream"),
            ),
        )
        unwrap_fragments(root)

        stream = root[0]
        assert stream.tag == "Stream"
        assert stream.get("src") == "A"
        assert stream.get("dst") == "B"
        assert stream.get("name") == "my-stream"

    def test_children_keep_sub_elements(self):
        root = E.Field(
            E.fragment(
                E.Stream(
                    E.Contains("gas for flaring"),
                    src="VFPartition",
                    dst="Flaring",
                ),
            ),
        )
        unwrap_fragments(root)

        stream = root[0]
        contains = stream.find("Contains")
        assert contains is not None
        assert contains.text == "gas for flaring"

    def test_children_keep_tail_text(self):
        # Tail text on fragment children should be preserved
        root = E.Field(E.fragment())
        frag = root[0]
        child = etree.SubElement(frag, "Process", name="X")
        child.tail = "\n    "

        unwrap_fragments(root)

        assert root[0].tail == "\n    "

    def test_no_fragments_is_noop(self):
        root = E.Field(
            E.Process(name="A"),
            E.Process(name="B"),
        )
        unwrap_fragments(root)

        assert len(root) == 2
        assert root[0].get("name") == "A"
        assert root[1].get("name") == "B"


# ---------------------------------------------------------------------------
# resolve_includes
# ---------------------------------------------------------------------------

XINCLUDE_NS = "http://www.w3.org/2001/XInclude"


class TestResolveIncludes:
    """Light test using tmp_path — avoids depending on real fragment files."""

    def test_xinclude_resolves_included_file(self, tmp_path):
        # Create the included fragment file
        included = tmp_path / "part.xml"
        included.write_text(
            '<?xml version="1.0"?>\n'
            '<fragment><Process name="included"/></fragment>\n'
        )

        # Create the main XML with xi:include
        main_xml = (
            '<?xml version="1.0"?>\n'
            f'<Model xmlns:xi="{XINCLUDE_NS}">\n'
            f'  <xi:include href="{included}"/>\n'
            "</Model>\n"
        )
        tree = etree.ElementTree(etree.fromstring(main_xml.encode()))

        result = resolve_includes(tree)

        # The xi:include should be replaced by the content of part.xml
        assert result is tree  # returns same tree
        root = result.getroot()
        fragment = root.find("fragment")
        assert fragment is not None
        proc = fragment.find("Process")
        assert proc is not None
        assert proc.get("name") == "included"

    def test_xinclude_with_relative_href(self, tmp_path):
        # Create a subdirectory with the included file
        subdir = tmp_path / "fragments"
        subdir.mkdir()
        included = subdir / "piece.xml"
        included.write_text(
            '<?xml version="1.0"?>\n'
            '<Stream src="A" dst="B"><Contains>oil</Contains></Stream>\n'
        )

        # Main XML referencing the fragment via relative path
        main_file = tmp_path / "main.xml"
        main_file.write_text(
            '<?xml version="1.0"?>\n'
            f'<Model xmlns:xi="{XINCLUDE_NS}">\n'
            f'  <xi:include href="fragments/piece.xml"/>\n'
            "</Model>\n"
        )

        tree = etree.parse(str(main_file))
        result = resolve_includes(tree)

        root = result.getroot()
        stream = root.find("Stream")
        assert stream is not None
        assert stream.get("src") == "A"
        assert stream.find("Contains").text == "oil"

    def test_xinclude_multiple_includes(self, tmp_path):
        # Two separate included files
        part_a = tmp_path / "a.xml"
        part_a.write_text(
            '<?xml version="1.0"?>\n<Process name="A"/>\n'
        )
        part_b = tmp_path / "b.xml"
        part_b.write_text(
            '<?xml version="1.0"?>\n<Process name="B"/>\n'
        )

        main_file = tmp_path / "main.xml"
        main_file.write_text(
            '<?xml version="1.0"?>\n'
            f'<Model xmlns:xi="{XINCLUDE_NS}">\n'
            f'  <xi:include href="a.xml"/>\n'
            f'  <xi:include href="b.xml"/>\n'
            "</Model>\n"
        )

        tree = etree.parse(str(main_file))
        result = resolve_includes(tree)

        root = result.getroot()
        procs = root.findall("Process")
        assert len(procs) == 2
        assert procs[0].get("name") == "A"
        assert procs[1].get("name") == "B"
