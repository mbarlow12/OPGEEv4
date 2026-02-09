"""Smart default system — compute dependent attribute values on pydantic models.

Uses a decorator-based registry with topological dependency ordering.
Operates on FieldModel instances using model_fields_set to skip explicitly
set values.
"""

from __future__ import annotations
from opgee.input.models.processes import ProcessClassName
from opgee.input.models import FieldModel, AnalysisModel, ProcessUnion

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, overload, Literal

import networkx as nx

from opgee.core import split_attr_name
from opgee.error import OpgeeException
from opgee.log import getLogger

_logger = getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

_registry: dict[str, tuple[Callable[..., Any], list[str]]] = {}
_run_order: list[str] | None = None


def register(
    attr_name: str, dependencies: list[str]
) -> Callable[[Callable[P, R]], Callable[P, R]]:
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


def apply_defaults(
    field_model: FieldModel, analysis_model: AnalysisModel | None = None
) -> None:
    """Apply all smart defaults to pydantic model instances.

    For each attr in topological order:
    - Find the target model (Field, Process subclass, or Analysis)
    - Skip if the attr is in target_model.model_fields_set
    - Resolve dependency values from models
    - Call the registered function
    - setattr on the target model

    :param field_model: FieldModel instance (mutable, frozen=False)
    :param analysis_model: optional AnalysisModel instance
    """
    # Import defaults modules to trigger registrations
    from . import field_defaults as _  # noqa: F401
    from . import process_defaults as _pd  # noqa: F401

    for attr_name in run_order():
        entry = _registry.get(attr_name)
        if entry is None:
            # Leaf dependency (depended upon but no computation)
            continue

        func, dependencies = entry

        # Determine target model and attribute name
        target_class, target_attr = split_attr_name(attr_name)
        if target_class is None:
            target_class = "Field"

        target_model = _find_model(target_class, field_model, analysis_model)
        if target_model is None:
            _logger.debug(
                "Skipping smart default for '%s': target model not found", attr_name
            )
            continue

        # Skip if explicitly set in XML
        if target_attr in target_model.model_fields_set:
            _logger.debug("Skipping smart default for '%s': explicitly set", attr_name)
            continue

        # Resolve dependency values
        try:
            values = _resolve_dependencies(field_model, analysis_model, dependencies)
        except (ValueError, KeyError, AttributeError) as e:
            _logger.warning("Skipping smart default for '%s': %s", attr_name, e)
            continue

        # Call the function
        try:
            result = func(*values)
        except Exception as e:
            raise OpgeeException(
                f"Smart default function for '{attr_name}' failed: {e}"
            ) from e

        # Write result back to model
        setattr(target_model, target_attr, result)


@overload
def _find_model(
    class_name: Literal["Field"],
    field_model: FieldModel,
    analysis_model: AnalysisModel | None,
) -> FieldModel: ...
@overload
def _find_model(
    class_name: Literal["AnalysisModel"],
    field_model: FieldModel,
    analysis_model: AnalysisModel | None,
) -> AnalysisModel: ...
@overload
def _find_model(
    class_name: ProcessClassName,
    field_model: FieldModel,
    analysis_model: AnalysisModel | None,
) -> ProcessUnion: ...
@overload
def _find_model(
    class_name: str, field_model: FieldModel, analysis_model: AnalysisModel | None
) -> ProcessUnion: ...
def _find_model(
    class_name: str, field_model: FieldModel, analysis_model: AnalysisModel | None
) -> FieldModel | AnalysisModel | ProcessUnion:
    """Find the target model for a given class name."""
    if class_name == "Field":
        return field_model
    elif class_name == "Analysis":
        return analysis_model
    else:
        # Process subclass — find by tag (class name)
        for proc in field_model.processes:
            if type(proc).__name__ == class_name:
                return proc
    raise ValueError(f"Unknown `class_name` ({class_name}).")


def _resolve_dependencies(
    field_model: FieldModel,
    analysis_model: Any | None,
    dependencies: list[str],
) -> list[Any]:
    """Resolve all dependency attribute values from models."""
    values: list[Any] = []

    for dep_name in dependencies:
        dep_class, dep_attr = split_attr_name(dep_name)
        if dep_class is None:
            dep_class = "Field"

        dep_model = _find_model(dep_class, field_model, analysis_model)
        if dep_model is None:
            raise ValueError(f"Model for '{dep_class}' not found")

        value = getattr(dep_model, dep_attr)
        if value is None:
            raise ValueError(f"Dependency '{dep_name}' is None")

        values.append(value)

    return values


def clear_registry() -> None:
    """Clear all registrations. Useful for testing."""
    global _run_order
    _registry.clear()
    _run_order = None
