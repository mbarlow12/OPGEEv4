"""Pre- and post-resolution validation."""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from opgee.input.models.field import FieldModel


def validate_pre_resolution(root: etree._Element) -> list[str]:
    """Check basic structure before XInclude resolution.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    # Must have at least one Field
    fields = root.findall("Field")
    if not fields:
        errors.append("No <Field> elements found")

    # Each Field must have a name
    for field in fields:
        if not field.get("name"):
            errors.append("Found <Field> without name attribute")

    # Check xi:include hrefs point to existing files
    fragments_dir = Path(__file__).parent / "fragments"
    for include in root.iter("{http://www.w3.org/2001/XInclude}include"):
        href = include.get("href")
        if href and not (fragments_dir / href).exists():
            errors.append(f"XInclude href not found: {href}")

    return errors


def validate_post_resolution(field_model: FieldModel) -> list[str]:
    """Validate a deserialized FieldModel.

    Returns a list of error messages (empty = valid).
    Pydantic handles type validation during deserialization;
    this adds cross-field constraints.
    """
    errors: list[str] = []

    # Must have at least one process
    if not field_model.processes:
        errors.append(f"Field '{field_model.name}' has no processes")

    return errors
