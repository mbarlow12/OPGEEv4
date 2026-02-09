"""Pre- and post-resolution validation."""
from __future__ import annotations

from lxml import etree

from opgee_input import FieldInput


def validate_pre_resolution(root: etree._Element) -> list[str]:
    """Check basic structure before include resolution."""
    errors: list[str] = []

    fields = root.findall("Field")
    if not fields:
        errors.append("No <Field> elements found")

    for field in fields:
        if not field.get("name"):
            errors.append("Found <Field> without name attribute")

    # Check inc:* elements point to known fragment types
    from .include import INC_NS, _FRAGMENT_DIRS, FRAGMENTS_DIR, _slugify

    for field in root.findall("Field"):
        for inc_elt in field.findall(f"{{{INC_NS}}}*"):
            attr_name = etree.QName(inc_elt).localname
            if attr_name not in _FRAGMENT_DIRS:
                errors.append(f"Unknown inc element: {attr_name}")
                continue
            value = (inc_elt.text or "").strip()
            if value and value != "None":
                slug = _slugify(value)
                subdir = _FRAGMENT_DIRS[attr_name]
                path = FRAGMENTS_DIR / subdir / f"{slug}.xml"
                if not path.exists():
                    errors.append(f"Fragment not found: {path}")

    return errors


def validate_post_resolution(field_input: FieldInput) -> list[str]:
    """Validate an extracted FieldInput."""
    errors: list[str] = []

    if not field_input.processes:
        errors.append(f"Field '{field_input.name}' has no processes")

    return errors
