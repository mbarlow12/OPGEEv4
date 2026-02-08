"""Shared fixtures for tests/input/ test modules."""
from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree
from lxml.builder import E


def make_field_xml(name: str = "test", children: list | None = None, **attrs) -> etree._Element:
    """Build a <Field name="..."> element with optional children and extra element children.

    :param name: value for the name attribute
    :param children: list of lxml sub-elements to append (e.g. processes, streams)
    :param attrs: extra child *elements* expressed as keyword=value pairs
                  (e.g. ``oil_sands_mine="None"`` becomes ``<oil_sands_mine>None</oil_sands_mine>``)
    :return: an lxml ``<Field>`` element
    """
    field = etree.Element("Field", name=name)
    for k, v in attrs.items():
        elt = etree.SubElement(field, k)
        elt.text = str(v)
    if children:
        for child in children:
            field.append(child)
    else:
        # Default: add a Separation process so the field satisfies validation
        etree.SubElement(field, "Separation")
    return field


@pytest.fixture()
def minimal_model_xml() -> etree._Element:
    """A minimal <Model> with one Field (containing a Separation process)
    and one Analysis referencing it via Group.
    """
    field = make_field_xml("test_field", oil_sands_mine="None")
    field.set("group", "default")
    analysis = E.Analysis(
        E.Group("default"),
        name="test_analysis",
    )
    model = E.Model(field, analysis)
    return model


@pytest.fixture()
def tmp_xml_file(tmp_path: Path):
    """Factory fixture: write an XML string (or lxml element) to a temp file.

    Returns a callable ``write(content) -> Path``.

    *content* may be:
    - an ``lxml.etree._Element`` (will be serialized with XML declaration)
    - a ``bytes`` or ``str`` (written verbatim)
    """
    counter = 0

    def _write(content) -> Path:
        nonlocal counter
        counter += 1
        path = tmp_path / f"model_{counter}.xml"
        if isinstance(content, etree._Element):
            path.write_bytes(
                etree.tostring(content, xml_declaration=True, encoding="UTF-8")
            )
        elif isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(str(content), encoding="utf-8")
        return path

    return _write
