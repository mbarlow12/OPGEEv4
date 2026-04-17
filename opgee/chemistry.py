"""
Component chemistry data and physical constants.

Extracted from Stream class-level data to break stream<->emissions coupling.
"""
import re

import pandas as pd

from .error import ModelValidationError, OpgeeException
from .table_manager import TableManager
from .units import ureg

# Phase constants
PHASE_GAS: str = "gas"
PHASE_LIQUID: str = "liquid"
PHASE_SOLID: str = "solid"

_carbon_number_prog = re.compile(r"^C(\d+)$")
_hydrocarbon_prog = re.compile(r"^(C\d+)H(\d+)$")


def is_carbon_number(name: str) -> bool:
    return _carbon_number_prog.match(name) is not None


def is_hydrocarbon(name: str) -> bool:
    return name == "CH4" or _hydrocarbon_prog.match(name) is not None


def molecule_to_carbon(molecule: str) -> str:
    if molecule == "CH4":
        return "C1"
    m = _hydrocarbon_prog.match(molecule)
    if m is None:
        raise OpgeeException(f"Expected hydrocarbon molecule name like CxHy, got {molecule}")
    return m.group(1)


def carbon_to_molecule(c_name: str) -> str:
    if c_name == "C1":
        return "CH4"
    m = _carbon_number_prog.match(c_name)
    if m is None:
        raise OpgeeException(f"Expected carbon number name like Cn, got {c_name}")
    carbons = int(m.group(1))
    hydrogens = 2 * carbons + 2
    return f"{c_name}H{hydrogens}"


_mgr = TableManager()
_pubchem_cid_df = _mgr.get_table("pubchem-cid")

#: Public re-export of the pubchem-cid DataFrame for use by `thermodynamics.ChemicalInfo`.
PUBCHEM_CID_DF: pd.DataFrame = _pubchem_cid_df

HYDROCARBONS: list[str] = list(_pubchem_cid_df.index)
_max_carbon_number = len(HYDROCARBONS)
_carbon_number_dict: dict[str, float] = {f"C{n}": float(n) for n in range(1, _max_carbon_number + 1)}

if set(_carbon_number_dict.keys()) != set(HYDROCARBONS):
    raise ModelValidationError(f"pubchem-cid must contain carbon numbers 1..{_max_carbon_number}.")

VOCS: list[str] = HYDROCARBONS[1:]

_solids: list[str] = ["PC"]
_liquids: list[str] = ["oil"]
_gases: list[str] = [
    "N2", "O2", "CO2", "H2O", "H2", "H2S", "SO2", "CO",
    "Argon", "Neon", "Helium", "Krypton", "Xenon",
]
_other: list[str] = ["Na+", "Cl-", "Si-"]

SOLIDS: list[str] = _solids
LIQUIDS: list[str] = _liquids
GASES: list[str] = _gases
OTHER: list[str] = _other

for _gas in _gases:
    _carbon_number_dict[_gas] = 1.0 if _gas[0] == "C" else 0.0

CARBON_NUMBER: dict[str, float] = _carbon_number_dict

COMPONENT_NAMES: list[str] = _solids + _liquids + _gases + _other + HYDROCARBONS

R_GAS = ureg.Quantity(8.31446, "J/mol/K")
