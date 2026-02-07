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


# ── Composable element factories ───────────────────────────────
#
# Each E_* function returns an etree.Element.  Children are passed
# positionally and appended; XML attributes come as keyword args.
#
# Usage:
#   xml = E_model(
#       E_analysis(E_a("functional_unit", "oil")),
#       E_field(E_process("Separation"), E_stream("Reservoir", "Separation")),
#   )

_HYPHENATE = {"impute_start", "cycle_start"}

def _make(tag: str, *children: etree._Element, text: str | None = None,
          **attrs: str | None) -> etree.Element:
    """Low-level helper: create element, set non-None attrs, append children."""
    elt = etree.Element(tag)
    for k, v in attrs.items():
        if v is not None:
            xml_name = k.replace("_", "-") if k in _HYPHENATE else k
            elt.set(xml_name, v)
    if text is not None:
        elt.text = text
    for child in children:
        elt.append(child)
    return elt


# ── Core elements ──────────────────────────────────────────────

def E_model(*children: etree._Element, schema_version: str | None = None) -> etree.Element:
    return _make("Model", *children, schema_version=schema_version)


def E_analysis(*children: etree._Element, name: str = "test",
               delete: str | None = None) -> etree.Element:
    return _make("Analysis", *children, name=name, delete=delete)


def E_field(*children: etree._Element, name: str = "test",
            enabled: str | None = None, extend: str | None = None,
            delete: str | None = None, modifies: str | None = None,
            modified: str | None = None) -> etree.Element:
    return _make("Field", *children, name=name, enabled=enabled,
                 extend=extend, delete=delete, modifies=modifies,
                 modified=modified)


def E_a(name: str, value: str = "", *, explicit: str | None = None,
        delete: str | None = None) -> etree.Element:
    return _make("A", text=value, name=name, explicit=explicit, delete=delete)


def E_process(cls: str, *children: etree._Element, name: str | None = None,
              enabled: str | None = None, boundary: str | None = None,
              after: str | None = None, impute_start: str | None = None,
              cycle_start: str | None = None, extend: str | None = None,
              delete: str | None = None, desc: str | None = None) -> etree.Element:
    # "class" is a Python keyword — pass via **attrs dict
    attrs: dict[str, str | None] = {
        "class": cls, "name": name, "enabled": enabled, "boundary": boundary,
        "after": after, "impute_start": impute_start, "cycle_start": cycle_start,
        "extend": extend, "delete": delete, "desc": desc,
    }
    return _make("Process", *children, **attrs)


def E_stream(src: str, dst: str, *children: etree._Element,
             name: str | None = None, impute: str | None = None,
             boundary: str | None = None,
             delete: str | None = None) -> etree.Element:
    return _make("Stream", *children, name=name, src=src, dst=dst,
                 impute=impute, boundary=boundary, delete=delete)


def E_component(name: str, phase: str, value: str) -> etree.Element:
    return _make("Component", text=value, name=name, phase=phase)


def E_contains(text: str, *, delete: str | None = None) -> etree.Element:
    return _make("Contains", text=text, delete=delete)


def E_group(text: str, *, regex: str | None = None,
            delete: str | None = None) -> etree.Element:
    return _make("Group", text=text, regex=regex, delete=delete)


def E_field_ref(name: str, *, delete: str | None = None) -> etree.Element:
    return _make("FieldRef", text="", name=name, delete=delete)


# ── Ext-only elements ─────────────────────────────────────────

def E_process_choice(name: str, *groups: etree._Element,
                     extend: str | None = None, default: str | None = None,
                     delete: str | None = None) -> etree.Element:
    return _make("ProcessChoice", *groups, name=name, extend=extend,
                 default=default, delete=delete)


def E_process_group(name: str, *children: etree._Element,
                    delete: str | None = None) -> etree.Element:
    return _make("ProcessGroup", *children, name=name, delete=delete)


def E_process_ref(name: str | None = None, *, cls: str | None = None,
                  delete: str | None = None) -> etree.Element:
    attrs: dict[str, str | None] = {"name": name, "class": cls, "delete": delete}
    return _make("ProcessRef", **attrs)


def E_stream_ref(name: str, *, delete: str | None = None) -> etree.Element:
    return _make("StreamRef", text="", name=name, delete=delete)


def E_aggregator(name: str, *children: etree._Element,
                 enabled: str | None = None,
                 delete: str | None = None) -> etree.Element:
    return _make("Aggregator", *children, name=name, enabled=enabled,
                 delete=delete)


# ── AttrDefs elements ─────────────────────────────────────────

def E_attr_defs(*class_attrs: etree._Element) -> etree.Element:
    return _make("AttrDefs", *class_attrs)


def E_class_attrs(name: str, *children: etree._Element) -> etree.Element:
    return _make("ClassAttrs", *children, name=name)


def E_attr_def(name: str, value: str = "", *, type: str | None = None,
               unit: str | None = None, desc: str | None = None,
               options: str | None = None, exclusive: str | None = None,
               synchronized: str | None = None,
               GT: str | None = None, GE: str | None = None,
               LT: str | None = None, LE: str | None = None) -> etree.Element:
    # Constraint attrs are uppercase — don't underscore-translate them
    elt = etree.Element("AttrDef")
    elt.set("name", name)
    if value:
        elt.text = value
    for k, v in {"type": type, "unit": unit, "desc": desc, "options": options,
                 "exclusive": exclusive, "synchronized": synchronized,
                 "GT": GT, "GE": GE, "LT": LT, "LE": LE}.items():
        if v is not None:
            elt.set(k, v)
    return elt


def E_options(name: str, default: str, *option_elts: etree._Element) -> etree.Element:
    return _make("Options", *option_elts, name=name, default=default)


def E_option(value: str, *, label: str | None = None,
             desc: str | None = None) -> etree.Element:
    return _make("Option", text=value, label=label, desc=desc)


# ── Convenience fixture ───────────────────────────────────────

@pytest.fixture
def valid_core_model() -> etree.Element:
    """A minimal Model that passes opgee_core.xsd validation."""
    return E_model(
        E_analysis(E_a("functional_unit", "oil")),
        E_field(
            E_a("country", "US"),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        ),
    )


# ── Legacy string-fragment builder ────────────────────────────
# Prefer the E_* factories above for new tests.

def make_model_xml(field_body: str = "", analysis_body: str = "",
                   field_attrs: str = "", analysis_name: str = "test") -> etree.Element:
    """Build a minimal <Model> element from XML string fragments.

    .. deprecated:: Prefer E_* element factories for new tests.
    """
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
