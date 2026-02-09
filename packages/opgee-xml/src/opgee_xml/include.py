"""Custom <inc:*> namespace element system for fragment inclusion."""
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from .merge import merge_elements

_logger = logging.getLogger(__name__)

INC_NS = "urn:opgee:include"
FRAGMENTS_DIR = Path(__file__).parent / "fragments"

_FRAGMENT_DIRS: dict[str, str] = {
    "template": "templates",
    "oil_sands_mine": "process_groups/oil_sands_mine",
    "gas_processing_path": "process_groups/gas_processing_path",
    "oil_processing_path": "process_groups/oil_processing_path",
    "common_gas_process_choice": "process_groups/common_gas_process_choice",
    "upgrader_type": "process_groups/upgrader_type",
}


def _slugify(value: str) -> str:
    """Convert a choice value to a fragment filename slug."""
    return value.lower().replace(" ", "_").replace("-", "_")


def _load_fragment(attr_name: str, value: str) -> etree._Element:
    """Load and return the root element of a fragment file."""
    subdir = _FRAGMENT_DIRS.get(attr_name)
    if subdir is None:
        raise ValueError(f"Unknown inc element: {attr_name}")

    slug = _slugify(value)
    path = FRAGMENTS_DIR / subdir / f"{slug}.xml"
    if not path.exists():
        raise FileNotFoundError(f"Fragment not found: {path}")

    tree = etree.parse(str(path))
    return tree.getroot()


def unwrap_fragments(root: etree._Element) -> None:
    """Find all <fragment> elements, reparent children into parent, remove wrappers.

    Handles nested fragments by processing in document order (the inner-most
    fragments from recursive includes are already flattened by lxml's XInclude).
    """
    while True:
        fragments = list(root.iter("fragment"))
        if not fragments:
            break

        for fragment in fragments:
            parent = fragment.getparent()
            if parent is None:
                continue

            idx = list(parent).index(fragment)

            # Move children from fragment to parent at the fragment's position
            for i, child in enumerate(list(fragment)):
                parent.insert(idx + i, child)

            parent.remove(fragment)


def resolve_includes(field_elt: etree._Element) -> dict[str, str]:
    """Resolve <inc:*> elements in a Field, merge fragments, return choices dict.

    For each <inc:*> element found:
    1. Load the corresponding fragment file
    2. Unwrap the <fragment> wrapper
    3. Merge fragment contents into the field element
    4. Remove the <inc:*> element
    5. Record the choice in the returned dict
    """
    choices: dict[str, str] = {}
    inc_elts = field_elt.findall(f"{{{INC_NS}}}*")

    for inc_elt in inc_elts:
        attr_name = etree.QName(inc_elt).localname
        value = (inc_elt.text or "").strip()

        if not value or value == "None":
            choices[attr_name] = value
            field_elt.remove(inc_elt)
            continue

        choices[attr_name] = value

        # Load fragment
        frag_root = _load_fragment(attr_name, value)

        # Get children from fragment wrapper
        if frag_root.tag == "fragment":
            children = list(frag_root)
        else:
            children = [frag_root]

        # Merge fragment contents into field
        merge_elements(field_elt, children)

        field_elt.remove(inc_elt)

    return choices
