"""XML processing pipeline for OPGEE model files.

Pipeline steps:
1. Parse input XML, split into per-Field units
2. For each Field: resolve XIncludes, unwrap fragments, merge
3. Deserialize to pydantic models
4. Apply smart defaults
5. Validate

Public API:
    process_field_xml(input_path) -> list[FieldModel]
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from opgee.input.models.field import FieldModel

from .deserialize import deserialize_field
from .resolve import FRAGMENTS_DIR, resolve_includes, unwrap_fragments
from .validation import validate_post_resolution, validate_pre_resolution


def process_field_xml(input_path: Path) -> list[FieldModel]:
    """Main entry point: parse XML -> resolve -> deserialize -> validate.

    :param input_path: path to the XML model file
    :return: list of validated FieldModel instances
    """
    tree = etree.parse(str(input_path), base_url=str(FRAGMENTS_DIR) + "/")
    root = tree.getroot()

    # Pre-resolution validation
    errors = validate_pre_resolution(root)
    if errors:
        raise ValueError(f"Pre-resolution validation failed: {'; '.join(errors)}")

    # Resolve XIncludes and unwrap fragments
    resolve_includes(tree)
    unwrap_fragments(root)

    # Deserialize each Field
    results: list[FieldModel] = []
    for field_elt in root.findall("Field"):
        field_model = deserialize_field(field_elt)

        # Apply smart defaults
        from opgee.input.smart_defaults import apply_defaults
        apply_defaults(field_model)

        # Post-resolution validation
        post_errors = validate_post_resolution(field_model)
        if post_errors:
            raise ValueError(
                f"Post-resolution validation failed for '{field_model.name}': "
                f"{'; '.join(post_errors)}"
            )

        results.append(field_model)

    return results
