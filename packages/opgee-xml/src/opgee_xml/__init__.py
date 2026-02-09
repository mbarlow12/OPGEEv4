"""XML processing pipeline for OPGEE model files.

Public API:
    process_field_xml(input_path) -> Iterator[ParsedField]
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from opgee_input import AnalysisInput, FieldInput

from .extract import extract_analysis, extract_field
from .include import resolve_includes
from .parse import parse_and_split
from .validation import validate_post_resolution, validate_pre_resolution


@dataclass
class ParsedField:
    """Result of processing a single Field from XML."""

    field: FieldInput
    choices: dict[str, str]
    analysis: AnalysisInput | None = None
    group: str | None = None


def process_field_xml(input_path: Path) -> Iterator[ParsedField]:
    """Parse XML -> resolve includes -> extract -> validate. Yields per-Field."""
    tree = etree.parse(str(input_path))
    root = tree.getroot()

    # Pre-resolution validation
    errors = validate_pre_resolution(root)
    if errors:
        raise ValueError(f"Pre-resolution validation failed: {'; '.join(errors)}")

    for unit in parse_and_split(root):
        # Resolve <inc:*> includes and get choice attrs
        choices = resolve_includes(unit.field)

        # Extract to pydantic dataclass
        field_input = extract_field(unit.field)

        # Post-resolution validation
        post_errors = validate_post_resolution(field_input)
        if post_errors:
            raise ValueError(
                f"Post-resolution validation failed for '{field_input.name}': "
                f"{'; '.join(post_errors)}"
            )

        analysis_input = extract_analysis(unit.analysis) if unit.analysis is not None else None

        yield ParsedField(
            field=field_input,
            choices=choices,
            analysis=analysis_input,
            group=unit.group,
        )
