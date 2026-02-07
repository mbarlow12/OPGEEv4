"""Stage 2: Smart default system — compute dependent attribute values on lxml trees.

Named SmartDefault_ (trailing underscore) to avoid conflicts with the existing
SmartDefault class during coexistence.
"""

from collections.abc import Callable
from copy import deepcopy
from typing import Any, ParamSpec, TypeVar

import networkx as nx
from lxml import etree

from opgee.core import split_attr_name
from opgee.error import OpgeeException
from opgee.log import getLogger

from .value_resolution import read_attr_value, write_attr_value

_logger = getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

_registry: dict[str, tuple[Callable[..., Any], list[str]]] = {}
_run_order: list[str] | None = None


def register(attr_name: str, dependencies: list[str]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to register a smart default function.

    :param attr_name: target attribute name (may be "ClassName.attr_name")
    :param dependencies: list of attribute names this default depends on
    """
    global _run_order

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        _registry[attr_name] = (func, dependencies)
        _run_order = None  # invalidate cache
        return func

    return decorator


def run_order() -> list[str]:
    """Return attribute names in topological dependency order. Cached."""
    global _run_order

    if _run_order is None:
        g = nx.DiGraph()

        for attr_name, (_, dependencies) in _registry.items():
            for dep in dependencies:
                g.add_edge(dep, attr_name)

        cycles = list(nx.simple_cycles(g))
        if cycles:
            raise OpgeeException(f"Smart default dependencies contain cycles: {cycles}")

        _run_order = list(nx.topological_sort(g))

    return _run_order


def apply_smart_defaults(root: etree.Element) -> etree.Element:
    """
    Apply all registered smart defaults to the lxml tree.

    For each attribute in topological order:
    - Find the target element (Field, Analysis, or Process by class name)
    - Skip if the <A> element is marked explicit="true"
    - Resolve dependency values
    - Call the registered function
    - Write the result back

    :param root: <Model> lxml Element
    :return: a new Element with smart defaults applied (input is not modified)
    """
    root = deepcopy(root)
    # Import defaults module to trigger registrations
    from . import defaults as _  # noqa: F401

    field_elt = root.find("Field")
    analysis_elt = root.find("Analysis")

    for attr_name in run_order():
        entry = _registry.get(attr_name)
        if entry is None:
            # This is a leaf dependency (depended upon but has no computation)
            continue

        func, dependencies = entry

        # Determine target element and class name
        target_class, target_attr = split_attr_name(attr_name)
        if target_class is None:
            target_class = "Field"

        target_elt = _find_element(root, field_elt, analysis_elt, target_class)
        if target_elt is None:
            _logger.debug(f"Skipping smart default for '{attr_name}': target element not found")
            continue

        # Check if explicit
        a_elt = _find_a(target_elt, target_attr)
        if a_elt is not None and a_elt.get("explicit") == "true":
            _logger.debug(f"Skipping smart default for '{attr_name}': explicit value")
            continue

        # Resolve dependency values
        try:
            values = _resolve_dependencies(root, field_elt, analysis_elt, dependencies)
        except (ValueError, KeyError) as e:
            _logger.warning(f"Skipping smart default for '{attr_name}': {e}")
            continue

        # Call the function and write the result
        try:
            result = func(*values)
        except Exception as e:
            raise OpgeeException(
                f"Smart default function for '{attr_name}' failed: {e}"
            ) from e

        write_attr_value(target_elt, target_attr, result, explicit=False)

    return root


def _find_element(root: etree.Element, field_elt: etree.Element | None,
                  analysis_elt: etree.Element | None,
                  class_name: str) -> etree.Element | None:
    """Find the element for a given class name."""
    if class_name == "Field":
        return field_elt
    elif class_name == "Analysis":
        return analysis_elt
    else:
        # Process subclass — find by class attribute
        if field_elt is not None:
            for proc in field_elt.findall("Process"):
                if proc.get("class") == class_name:
                    return proc
        return None


def _find_a(elt: etree.Element, attr_name: str) -> etree.Element | None:
    """Find <A name="attr_name"> child."""
    for a in elt.findall("A"):
        if a.get("name") == attr_name:
            return a
    return None


def _resolve_dependencies(root: etree.Element, field_elt: etree.Element | None,
                          analysis_elt: etree.Element | None,
                          dependencies: list[str]) -> list[Any]:
    """Resolve all dependency attribute values."""
    values: list[Any] = []

    for dep_name in dependencies:
        dep_class, dep_attr = split_attr_name(dep_name)
        if dep_class is None:
            dep_class = "Field"

        dep_elt = _find_element(root, field_elt, analysis_elt, dep_class)
        if dep_elt is None:
            raise ValueError(f"Element for '{dep_class}' not found")

        value = read_attr_value(dep_elt, dep_attr, dep_class)
        values.append(value)

    return values


def clear_registry() -> None:
    """Clear all registrations. Useful for testing."""
    global _run_order
    _registry.clear()
    _run_order = None
