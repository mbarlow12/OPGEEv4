"""Parse and split input XML into per-Field processing units."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lxml import etree


@dataclass
class FieldUnit:
    """A single Field element with its optional Analysis."""

    field: etree._Element
    analysis: etree._Element | None


# backwards,
# analysis is the selection mechanism to gather fields under single "simulation" group
def parse_and_split(input_path: Path) -> list[FieldUnit]:
    """Parse input XML and split into per-Field processing units.

    :param input_path: path to the XML model file
    :return: list of FieldUnit, one per <Field> element
    """
    tree = etree.parse(str(input_path))
    root = tree.getroot()

    # Find all analyses (there's usually one)
    analyses = {a.get("name"): a for a in root.findall("Analysis")}

    units = []
    for field_elt in root.findall("Field"):
        # Try to find the matching analysis via FieldRef
        analysis_elt = None
        for analysis in analyses.values():
            for ref in analysis.findall("FieldRef"):
                if ref.get("name") == field_elt.get("name"):
                    analysis_elt = analysis
                    break
            if analysis_elt is not None:
                break

        units.append(FieldUnit(field=field_elt, analysis=analysis_elt))

    return units
