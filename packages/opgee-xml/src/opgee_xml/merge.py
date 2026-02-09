"""XML element merging logic.

Adapted from opgee/xml_utils.py. Key change: uses identity attributes
for matching instead of all attributes.
"""
from __future__ import annotations

import logging
from copy import deepcopy

from lxml import etree

_logger = logging.getLogger(__name__)

# Attributes used for element identity matching
IDENTITY_ATTRS = ("name", "boundary")


def match_element(elt1: etree._Element, elt2: etree._Element) -> bool:
    """Match two elements by tag + identity attributes only.

    Two elements match if:
    - Same tag
    - Same values for all identity attributes present in either element
    """
    if elt1.tag != elt2.tag:
        return False

    for attr_name in IDENTITY_ATTRS:
        v1 = elt1.get(attr_name)
        v2 = elt2.get(attr_name)
        # If both have the attr, they must match
        if v1 is not None and v2 is not None and v1 != v2:
            return False
        # If only one has it, they don't match (identity mismatch)
        if (v1 is None) != (v2 is None):
            return False

    return True


def merge_element(parent: etree._Element, new_elt: etree._Element) -> None:
    """Merge new_elt into parent's children.

    If a matching child is found:
    - If new_elt has delete='1', remove the matching child
    - Otherwise, update text and recursively merge children
    If no match, append a copy of new_elt.
    """
    for sibling in parent:
        if match_element(new_elt, sibling):
            if new_elt.attrib.get("delete", "0") == "1":
                _logger.debug("Deleting <%s>", sibling.tag)
                parent.remove(sibling)
            else:
                sibling.text = new_elt.text
                merge_elements(sibling, list(new_elt))
            return

    # No match found -- append copy
    parent.append(deepcopy(new_elt))


def merge_elements(parent: etree._Element, elt_list: list[etree._Element]) -> None:
    """Merge each element in elt_list into parent."""
    for elt in elt_list:
        merge_element(parent, elt)
