"""
Lightweight, frozen data-transfer objects that replace the ``self`` references
the original thermodynamics classes held on ``Stream``, ``Field``, and
``Model``.

Every field is a concrete scalar (:class:`pint.Quantity`) or a
:class:`pandas.Series` — no dependency on any ``opgee`` class.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pint


# ---------------------------------------------------------------------------
# Temperature / Pressure pair
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TemperaturePressure:
    """Immutable (T, P) pair, replacing ``opgee.core.TemperaturePressure``."""
    T: pint.Quantity
    P: pint.Quantity


# ---------------------------------------------------------------------------
# Stream proxy — the *only* data the thermo functions read from a Stream
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StreamInfo:
    """Flat view of the stream data consumed by thermodynamic calculations.

    Fields
    ------
    tp : TemperaturePressure
        Stream temperature and pressure.
    gas_flow_rates : pd.Series
        Positive gas-phase mass flow rates, dtype ``pint[tonne/day]``,
        indexed by component name.
    liquid_flow_rates : dict[str, pint.Quantity]
        Liquid-phase mass flow rates keyed by component name
        (e.g. ``{"oil": …, "H2O": …, "PC": …}``).
    API : pint.Quantity | None
        API gravity carried on the stream, if applicable.
    component_names : list[str]
        Full ordered list of component names tracked on this stream.
    """
    tp: TemperaturePressure
    gas_flow_rates: pd.Series
    liquid_flow_rates: dict[str, pint.Quantity]
    API: pint.Quantity | None = None
    component_names: list[str] | None = None

    # convenience helpers ------------------------------------------------

    def gas_flow_rate(self, name: str | list[str]) -> pint.Quantity | pd.Series:
        """Return gas flow rate(s) for *name* (single component or list)."""
        if isinstance(name, list):
            return self.gas_flow_rates.reindex(name, fill_value=self.gas_flow_rates.iloc[0] * 0)
        return self.gas_flow_rates.get(name, self.gas_flow_rates.iloc[0] * 0)

    def liquid_flow_rate(self, name: str) -> pint.Quantity:
        from .units import Q_
        return self.liquid_flow_rates.get(name, Q_(0.0, "tonne/day"))

    def total_gases_rates(self) -> pd.Series:
        """All gas-phase rates (HCs + non-HC gases)."""
        return self.gas_flow_rates

    def total_gas_rate(self) -> pint.Quantity:
        return self.gas_flow_rates.sum()

    def positive_gas_flow_rates(self, index: list[str] | None = None) -> pd.Series:
        """Return gas flow rates > 0, optionally filtered by *index*."""
        s = self.gas_flow_rates
        if index is not None:
            s = s.reindex(index, fill_value=s.iloc[0] * 0)
        return s[s > 0]


# ---------------------------------------------------------------------------
# Component-property tables — replaces the per-instance Series stored on
# ``AbstractSubstance``.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ComponentProperties:
    """Pre-computed per-component physical properties.

    Every Series is indexed by component name (matching
    ``StreamInfo.gas_flow_rates.index``).
    """
    MW: pd.Series
    """Molecular weights, dtype ``pint[g/mol]``."""

    LHV_molar: pd.Series
    """Lower heating values, dtype ``pint[joule/mol]``."""

    LHV_mass: pd.Series
    """Lower heating values per unit mass, dtype ``pint[joule/g]``."""

    HHV_molar: pd.Series
    """Higher heating values, dtype ``pint[joule/mol]``."""

    HHV_mass: pd.Series
    """Higher heating values per unit mass, dtype ``pint[joule/g]``."""

    Cp_STP: pd.Series
    """Specific heat at STP, dtype ``pint[joule/g/kelvin]``."""

    Tc: pd.Series
    """Critical temperatures, dtype ``pint[kelvin]``."""

    Pc: pd.Series
    """Critical pressures, dtype ``pint[Pa]``."""

    gas_rho_STP: pd.Series
    """Gas density at STP, dtype ``pint[kg/m**3]``."""


# ---------------------------------------------------------------------------
# Air mixture proxy
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AirProperties:
    """Pre-computed properties for a dry (or wet) air mixture."""
    mol_weight: pint.Quantity
    """Mixture molecular weight, ``g/mol``."""

    density_STP: pint.Quantity
    """Density at standard conditions, ``kg/m**3``."""
