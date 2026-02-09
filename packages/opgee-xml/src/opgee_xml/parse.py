"""Parse and split input XML into per-Field processing units."""
from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from lxml import etree


@dataclass
class FieldUnit:
    """A single Field element with its optional Analysis."""

    field: etree._Element
    analysis: etree._Element | None
    group: str | None = None


def _analysis_matches_field(
    analysis: etree._Element,
    field_group: str | None,
) -> bool:
    """Check if any Group in the analysis matches this field's group."""
    if field_group is None:
        return False
    for group_elt in analysis.findall("Group"):
        text = group_elt.text
        if not text:
            continue
        is_regex = group_elt.get("regex", "0") in ("1", "true")
        if is_regex:
            if re.search(text, field_group):
                return True
        else:
            if text == field_group:
                return True
    return False


def parse_and_split(root: etree._Element) -> Iterator[FieldUnit]:
    """Yield per-Field processing units from parsed XML root.

    Matches Fields to Analyses via the Field's ``group`` attribute
    and the Analysis's ``<Group>`` child elements:

    - Literal: Analysis Group text == Field's group attribute
    - Regex: Analysis Group with ``regex="1"`` matches Field's group attribute

    :param root: the already-parsed XML root element
    :yields: FieldUnit for each ``<Field>`` element
    """
    analyses = list(root.findall("Analysis"))

    for field_elt in root.findall("Field"):
        field_group = field_elt.get("group")

        matched_analysis = None
        for analysis in analyses:
            if _analysis_matches_field(analysis, field_group):
                matched_analysis = analysis
                break

        yield FieldUnit(field=field_elt, analysis=matched_analysis, group=field_group)
