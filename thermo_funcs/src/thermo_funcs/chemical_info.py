"""
Chemical property look-ups backed by *thermosteam*.

This module replaces the ``ChemicalInfo`` singleton with pure functions and a
lazily-initialised module-level cache.  Every public function returns a
:class:`pint.Quantity`.
"""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from typing import Sequence

import pandas as pd
import pint
from thermosteam import Chemical, IdealMixture

from .constants import PHASE_GAS, PHASE_LIQUID, PHASE_SOLID, STD_PRESSURE, STD_TEMPERATURE
from .units import ureg, Q_

# ---------------------------------------------------------------------------
# Non-hydrocarbon gases (same list as opgee.stream)
# ---------------------------------------------------------------------------
NON_HYDROCARBON_GASES: list[str] = [
    "N2", "O2", "CO2", "H2O", "H2", "H2S",
    "SO2", "CO", "Argon", "Neon", "Helium", "Krypton", "Xenon",
]

# ---------------------------------------------------------------------------
# PubChem CID table (bundled CSV)
# ---------------------------------------------------------------------------
def _load_pubchem_cid() -> pd.DataFrame:
    csv_path = Path(__file__).resolve().parent / "etc" / "pubchem_cid.csv"
    return pd.read_csv(str(csv_path), index_col="carbon_number")

_pubchem_cid_df: pd.DataFrame | None = None

def pubchem_cid_df() -> pd.DataFrame:
    global _pubchem_cid_df
    if _pubchem_cid_df is None:
        _pubchem_cid_df = _load_pubchem_cid()
    return _pubchem_cid_df


def hydrocarbon_names() -> list[str]:
    """Ordered list of hydrocarbon carbon-number names (C1 … C30)."""
    return list(pubchem_cid_df().index)


# ---------------------------------------------------------------------------
# Lazy chemical dict
# ---------------------------------------------------------------------------
_chemical_dict: dict[str, Chemical] | None = None


def _ensure_chemicals() -> dict[str, Chemical]:
    global _chemical_dict
    if _chemical_dict is not None:
        return _chemical_dict

    df = pubchem_cid_df()
    hc_dict = {name: Chemical(f"PubChem={cid}") for name, cid in df.PubChem.items()}
    nhc_dict = {name: Chemical(name) for name in NON_HYDROCARBON_GASES}
    _chemical_dict = {**hc_dict, **nhc_dict}
    return _chemical_dict


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def chemical(component: str) -> Chemical:
    """Return the thermosteam ``Chemical`` object for *component*."""
    return _ensure_chemicals()[component]


def component_names() -> list[str]:
    """All tracked component names (hydrocarbons + non-HC gases)."""
    return list(_ensure_chemicals().keys())


# ---------------------------------------------------------------------------
# Molecular weight
# ---------------------------------------------------------------------------
_mol_weights_cache: pd.Series | None = None


def mol_weights() -> pd.Series:
    """Series of molecular weights, dtype ``pint[g/mol]``."""
    global _mol_weights_cache
    if _mol_weights_cache is None:
        d = _ensure_chemicals()
        _mol_weights_cache = pd.Series(
            {name: chem.MW for name, chem in d.items()},
            dtype="pint[g/mole]",
        )
    return _mol_weights_cache


def mol_weight(component: str) -> pint.Quantity:
    """Molecular weight of *component* as a Quantity (g/mol)."""
    return mol_weights()[component]


# ---------------------------------------------------------------------------
# Density at arbitrary (T, P, phase)
# ---------------------------------------------------------------------------
_phase_map = {PHASE_GAS: "g", PHASE_LIQUID: "l", PHASE_SOLID: "s"}


@ureg.wraps("kg/m**3", ("", "kelvin", "Pa", None), strict=False)
def rho(
    component: str,
    temperature: float,
    pressure: float,
    phase: str,
) -> float:
    """Density of *component* at *temperature* / *pressure* / *phase*.

    Parameters are automatically converted to SI base units by :func:`pint.wraps`.
    """
    chem = chemical(component)
    letter = _phase_map[phase]
    curr = chem.get_phase(temperature, pressure)
    return chem.rho(curr if curr != letter else letter, temperature, pressure)


# ---------------------------------------------------------------------------
# Heating values
# ---------------------------------------------------------------------------
@ureg.wraps("joule/mol", ("", None), strict=False)
def heating_value(component: str, *, use_LHV: bool = True) -> float:
    """Lower or higher molar heating value for *component*."""
    chem = chemical(component)
    hv = chem.LHV if use_LHV else chem.HHV
    return abs(hv) if hv is not None else 0.0


def LHV(component: str) -> pint.Quantity:
    """Lower heating value (joule/mol)."""
    return heating_value(component, use_LHV=True)


def HHV(component: str) -> pint.Quantity:
    """Higher heating value (joule/mol)."""
    return heating_value(component, use_LHV=False)


# ---------------------------------------------------------------------------
# Specific heat
# ---------------------------------------------------------------------------
@ureg.wraps("joule/g/kelvin", ("", "kelvin"), strict=False)
def Cp(component: str, temperature_K: float) -> float:
    """Gas-phase specific heat at *temperature_K* (in Kelvin)."""
    chem = chemical(component)
    return chem.Cp(phase="g", T=temperature_K)


# ---------------------------------------------------------------------------
# Enthalpy
# ---------------------------------------------------------------------------
@ureg.wraps("joule/mol", ("", "kelvin", None), strict=False)
def enthalpy(component: str, temperature_K: float, phase: str = PHASE_GAS) -> float:
    """Enthalpy of *component* at *temperature_K* and *phase*."""
    chem = chemical(component)
    letter = "g" if phase == PHASE_GAS else "l"
    return chem.H(phase=letter, T=temperature_K)


# ---------------------------------------------------------------------------
# Saturation temperature / Critical properties
# ---------------------------------------------------------------------------
@ureg.wraps("kelvin", ("", "Pa"), strict=False)
def Tsat(component: str, pressure_Pa: float) -> float:
    """Saturation temperature at *pressure_Pa*."""
    chem = chemical(component)
    p_capped = min(chem.Pc * 0.99, pressure_Pa)
    return chem.Tsat(p_capped)


@ureg.wraps("kelvin", ("",), strict=False)
def Tc(component: str) -> float:
    """Critical temperature (kelvin)."""
    return chemical(component).Tc


@ureg.wraps("Pa", ("",), strict=False)
def Pc(component: str) -> float:
    """Critical pressure (Pa)."""
    return chemical(component).Pc


# ---------------------------------------------------------------------------
# Build a ComponentProperties bundle (replaces AbstractSubstance.__init__)
# ---------------------------------------------------------------------------
def build_component_properties(
    stp_T: pint.Quantity | None = None,
    stp_P: pint.Quantity | None = None,
) -> "ComponentProperties":
    """Create a :class:`~thermo_funcs.types.ComponentProperties` for all
    tracked components.

    Parameters
    ----------
    stp_T, stp_P
        Temperature / pressure used for STP density.  Defaults to module
        constants.
    """
    from .types import ComponentProperties

    stp_T = stp_T if stp_T is not None else STD_TEMPERATURE
    stp_P = stp_P if stp_P is not None else STD_PRESSURE

    mw = mol_weights()
    components = mw.index

    lhv_molar = pd.Series(
        {n: heating_value(n, use_LHV=True).magnitude for n in components},
        dtype="pint[joule/mole]",
    )
    lhv_mass = lhv_molar / mw  # joule/gram

    hhv_molar = pd.Series(
        {n: heating_value(n, use_LHV=False).magnitude for n in components},
        dtype="pint[joule/mole]",
    )
    hhv_mass = hhv_molar / mw

    cp_stp = pd.Series(
        {n: Cp(n, Q_(288.706, "kelvin")).magnitude for n in components},
        dtype="pint[joule/g/kelvin]",
    )
    tc_series = pd.Series(
        {n: Tc(n).magnitude for n in components}, dtype="pint[kelvin]"
    )
    pc_series = pd.Series(
        {n: Pc(n).magnitude for n in components}, dtype="pint[Pa]"
    )
    rho_stp = pd.Series(
        {n: rho(n, stp_T, stp_P, PHASE_GAS).magnitude for n in components},
        dtype="pint[kg/m**3]",
    )

    return ComponentProperties(
        MW=mw,
        LHV_molar=lhv_molar,
        LHV_mass=lhv_mass,
        HHV_molar=hhv_molar,
        HHV_mass=hhv_mass,
        Cp_STP=cp_stp,
        Tc=tc_series,
        Pc=pc_series,
        gas_rho_STP=rho_stp,
    )
