"""
opgee_thermo — Functional thermodynamics for OPGEE.

A standalone, workspace-member package that re-implements the calculations
from ``opgee.thermodynamics`` in a **purely functional** style with
comprehensive type hints and pint-based unit safety.

No dependency on anything in ``opgee``.

Sub-modules
-----------
- ``opgee_thermo.units``         — pint registry and ``Q_`` shorthand
- ``opgee_thermo.constants``     — physical / model constants
- ``opgee_thermo.types``         — frozen dataclass proxies (StreamInfo, etc.)
- ``opgee_thermo.chemical_info`` — chemical property look-ups (requires thermosteam)
- ``opgee_thermo.air``           — air-mixture calculations (requires thermosteam)
- ``opgee_thermo.oil``           — oil thermodynamics
- ``opgee_thermo.gas``           — gas thermodynamics
- ``opgee_thermo.water``         — water / steam thermodynamics
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------
# Always-available, lightweight imports
# ---------------------------------------------------------------------------
from .units import ureg, Q_

from .types import (
    AirProperties,
    ComponentProperties,
    StreamInfo,
    TemperaturePressure,
)

from .constants import (
    PHASE_GAS,
    PHASE_LIQUID,
    PHASE_SOLID,
    STD_PRESSURE,
    STD_TEMPERATURE,
    UNIVERSAL_GAS_CONSTANT,
)

# ---------------------------------------------------------------------------
# Lazy sub-module access for heavy dependencies (thermosteam, pyXSteam, …)
# ---------------------------------------------------------------------------
# These names are resolved on first attribute access so that importing
# ``opgee_thermo`` itself stays fast and doesn't require thermosteam at
# import time.

_LAZY_SUBMODULES: dict[str, str] = {
    "chemical_info": "opgee_thermo.chemical_info",
    "air":           "opgee_thermo.air",
    "oil":           "opgee_thermo.oil",
    "gas":           "opgee_thermo.gas",
    "water":         "opgee_thermo.water",
}

# Names re-exported from chemical_info
_CHEMICAL_INFO_ATTRS: set[str] = {
    "Cp", "HHV", "LHV", "Pc", "Tc", "Tsat",
    "build_component_properties", "chemical", "component_names",
    "enthalpy", "heating_value", "hydrocarbon_names",
    "mol_weight", "mol_weights", "rho",
}

# Names re-exported from air
_AIR_ATTRS: set[str] = {
    "DRY_AIR_COMPOSITION", "WET_AIR_COMPOSITION",
    "compute_air_properties", "dry_air_properties", "wet_air_properties",
}


def __getattr__(name: str):
    # Sub-module access
    if name in _LAZY_SUBMODULES:
        mod = importlib.import_module(_LAZY_SUBMODULES[name])
        globals()[name] = mod
        return mod

    # Re-exported chemical_info names
    if name in _CHEMICAL_INFO_ATTRS:
        mod = importlib.import_module("opgee_thermo.chemical_info")
        globals().update({n: getattr(mod, n) for n in _CHEMICAL_INFO_ATTRS})
        return getattr(mod, name)

    # Re-exported air names
    if name in _AIR_ATTRS:
        mod = importlib.import_module("opgee_thermo.air")
        globals().update({n: getattr(mod, n) for n in _AIR_ATTRS})
        return getattr(mod, name)

    raise AttributeError(f"module 'opgee_thermo' has no attribute {name!r}")


# ---------------------------------------------------------------------------
# Static type-checking support
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    from .chemical_info import (
        Cp as Cp,
        HHV as HHV,
        LHV as LHV,
        Pc as Pc,
        Tc as Tc,
        Tsat as Tsat,
        build_component_properties as build_component_properties,
        chemical as chemical,
        component_names as component_names,
        enthalpy as enthalpy,
        heating_value as heating_value,
        hydrocarbon_names as hydrocarbon_names,
        mol_weight as mol_weight,
        mol_weights as mol_weights,
        rho as rho,
    )
    from .air import (
        DRY_AIR_COMPOSITION as DRY_AIR_COMPOSITION,
        WET_AIR_COMPOSITION as WET_AIR_COMPOSITION,
        compute_air_properties as compute_air_properties,
        dry_air_properties as dry_air_properties,
        wet_air_properties as wet_air_properties,
    )
    from . import oil as oil
    from . import gas as gas
    from . import water as water

__all__ = [
    # units
    "ureg",
    "Q_",
    # types
    "AirProperties",
    "ComponentProperties",
    "StreamInfo",
    "TemperaturePressure",
    # constants
    "PHASE_GAS",
    "PHASE_LIQUID",
    "PHASE_SOLID",
    "STD_PRESSURE",
    "STD_TEMPERATURE",
    "UNIVERSAL_GAS_CONSTANT",
    # chemical_info (lazy)
    "Cp",
    "HHV",
    "LHV",
    "Pc",
    "Tc",
    "Tsat",
    "build_component_properties",
    "chemical",
    "component_names",
    "enthalpy",
    "heating_value",
    "hydrocarbon_names",
    "mol_weight",
    "mol_weights",
    "rho",
    # air (lazy)
    "DRY_AIR_COMPOSITION",
    "WET_AIR_COMPOSITION",
    "compute_air_properties",
    "dry_air_properties",
    "wet_air_properties",
    # sub-modules (lazy)
    "oil",
    "gas",
    "water",
]
