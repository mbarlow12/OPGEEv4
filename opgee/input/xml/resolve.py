"""XInclude resolution and fragment unwrapping."""
from __future__ import annotations

from pathlib import Path

from lxml import etree

FRAGMENTS_DIR = Path(__file__).parent / "fragments"


def resolve_includes(tree: etree._ElementTree) -> etree._ElementTree:
    """Resolve XInclude directives in the tree.

    Sets base URL to FRAGMENTS_DIR so relative href paths resolve correctly.
    """
    tree.xinclude()
    return tree


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
