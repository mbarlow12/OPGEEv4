"""Shared fixtures for opgee-xml tests."""
from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree


@pytest.fixture()
def tmp_xml_file(tmp_path: Path):
    """Factory fixture: write XML to a temp file."""
    counter = 0

    def _write(content) -> Path:
        nonlocal counter
        counter += 1
        path = tmp_path / f"model_{counter}.xml"
        if isinstance(content, etree._Element):
            path.write_bytes(etree.tostring(content, xml_declaration=True, encoding="UTF-8"))
        elif isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(str(content), encoding="utf-8")
        return path

    return _write


def make_field_xml(
    name: str = "test", children: list | None = None, **attrs
) -> etree._Element:
    """Build a <Field name="..."> element with optional children and extra element children."""
    field = etree.Element("Field", name=name)
    for k, v in attrs.items():
        elt = etree.SubElement(field, k)
        elt.text = str(v)
    if children:
        for child in children:
            field.append(child)
    else:
        etree.SubElement(field, "Separation")
    return field
