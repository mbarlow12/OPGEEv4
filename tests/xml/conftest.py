"""Fixtures for the XML processing pipeline tests."""

from pathlib import Path

import pytest
from lxml import etree

from opgee.attributes import AttrDefs


# ── Path helpers ──────────────────────────────────────────────────

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "opgee" / "input" / "xml" / "schemas"
OPGEE_ETC = Path(__file__).resolve().parents[2] / "opgee" / "etc"
TEST_FILES = Path(__file__).resolve().parents[1] / "files"


# ── Schema fixtures ──────────────────────────────────────────────

@pytest.fixture
def core_schema() -> etree.XMLSchema:
    """Post-pipeline schema (no ProcessChoice/Aggregator)."""
    doc = etree.parse(str(SCHEMA_DIR / "opgee_core.xsd"))
    return etree.XMLSchema(doc)


@pytest.fixture
def ext_schema() -> etree.XMLSchema:
    """Pre-pipeline schema (with ProcessChoice/Aggregator)."""
    doc = etree.parse(str(SCHEMA_DIR / "opgee_ext.xsd"))
    return etree.XMLSchema(doc)


@pytest.fixture
def attr_schema() -> etree.XMLSchema:
    """AttrDefs schema."""
    doc = etree.parse(str(SCHEMA_DIR / "attributes.xsd"))
    return etree.XMLSchema(doc)


# ── AttrDefs fixtures ────────────────────────────────────────────

@pytest.fixture
def attr_defs_elt() -> etree.Element:
    """Parse the real attributes.xml and return the <AttrDefs> element."""
    tree = etree.parse(str(OPGEE_ETC / "attributes.xml"))
    root = tree.getroot()
    return root.find("AttrDefs")


@pytest.fixture
def loaded_attr_defs(attr_defs_elt) -> AttrDefs:
    """Load AttrDefs singleton from the real attributes.xml and return it."""
    AttrDefs.load_attr_defs(attr_defs_elt)
    yield AttrDefs.get_instance()
    AttrDefs.clear()


# ── Minimal XML builders ────────────────────────────────────────

def make_model_xml(field_body: str = "", analysis_body: str = "",
                   field_attrs: str = "", analysis_name: str = "test") -> etree.Element:
    """Build a minimal <Model> element from XML string fragments."""
    xml = f"""\
<Model>
  <Analysis name="{analysis_name}">
    {analysis_body}
  </Analysis>
  <Field name="test" {field_attrs}>
    {field_body}
  </Field>
</Model>"""
    return etree.fromstring(xml.encode())


@pytest.fixture
def minimal_model_elt() -> etree.Element:
    """A bare-bones <Model> with empty Field and Analysis."""
    return make_model_xml()


@pytest.fixture
def test_process_groups_xml() -> etree.Element:
    """Parse tests/files/test_process_groups.xml and return the root."""
    tree = etree.parse(str(TEST_FILES / "test_process_groups.xml"))
    return tree.getroot()
