"""
Water / steam thermodynamic calculations — purely functional.
"""
from __future__ import annotations

import pint
from pyXSteam.XSteam import XSteam

from .chemical_info import Cp as chem_Cp, Tsat as chem_Tsat
from .constants import STD_PRESSURE, STD_TEMPERATURE, STEAM_TBL_DIGITS
from .types import StreamInfo
from .units import ureg, Q_

# Module-level steam table (FLS unit system: degF, psia, lb, btu)
_steam_table = XSteam(XSteam.UNIT_SYSTEM_FLS)


# ---------------------------------------------------------------------------
# Specific gravity from TDS
# ---------------------------------------------------------------------------
def water_specific_gravity(TDS: pint.Quantity) -> pint.Quantity:
    """Specific gravity correction from total dissolved solids (mg/L)."""
    return Q_(1.0 + TDS.magnitude * 0.695e-6, "frac")


# ---------------------------------------------------------------------------
# Density
# ---------------------------------------------------------------------------
def water_density(
    TDS: pint.Quantity,
    temperature: pint.Quantity | None = None,
    pressure: pint.Quantity | None = None,
) -> pint.Quantity:
    """Water density (kg/m**3) corrected for TDS.

    Parameters
    ----------
    TDS
        Total dissolved solids (mg/L).
    temperature, pressure
        Evaluation conditions.  Default to standard conditions.
    """
    T = (temperature if temperature is not None else STD_TEMPERATURE).to("degF").magnitude
    P = (pressure if pressure is not None else STD_PRESSURE).to("psia").magnitude
    sg = water_specific_gravity(TDS)

    rho = _steam_table.rho_pt(
        round(P, STEAM_TBL_DIGITS),
        round(T, STEAM_TBL_DIGITS),
    )
    return (sg * Q_(rho, "lb/ft**3")).to("kg/m**3")


# ---------------------------------------------------------------------------
# Volume flow rate
# ---------------------------------------------------------------------------
def water_volume_flow_rate(
    stream: StreamInfo,
    TDS: pint.Quantity,
) -> pint.Quantity:
    """Water volume flow rate (bbl_water/day)."""
    mass = stream.liquid_flow_rate("H2O")
    rho = water_density(TDS)
    return (mass / rho).to("bbl_water/day")


# ---------------------------------------------------------------------------
# Specific heat / heat capacity
# ---------------------------------------------------------------------------
def water_specific_heat(temperature: pint.Quantity) -> pint.Quantity:
    """Specific heat of water at *temperature* (btu/lb/degF)."""
    T_K = temperature.to("kelvin").magnitude
    cp = chem_Cp("H2O", Q_(T_K, "kelvin"))
    return cp.to("btu/lb/degF")


def water_heat_capacity(stream: StreamInfo) -> pint.Quantity:
    """Water heat capacity (btu/degF/day) for a stream."""
    mass = stream.liquid_flow_rate("H2O")
    cp = water_specific_heat(stream.tp.T)
    return (mass * cp).to("btu/degF/day")


# ---------------------------------------------------------------------------
# Saturation temperature
# ---------------------------------------------------------------------------
def saturated_temperature(saturated_pressure: pint.Quantity) -> pint.Quantity:
    """Water saturation temperature (kelvin) at *saturated_pressure*."""
    P_Pa = saturated_pressure.to("Pa").magnitude
    return chem_Tsat("H2O", Q_(P_Pa, "Pa"))


# ---------------------------------------------------------------------------
# Enthalpy helpers
# ---------------------------------------------------------------------------
def enthalpy_PT(
    pressure: pint.Quantity,
    temperature: pint.Quantity,
    mass_rate: pint.Quantity,
) -> pint.Quantity:
    """Water enthalpy at given P, T (MJ/day)."""
    P = pressure.to("psia").magnitude
    T = temperature.to("degF").magnitude

    h = _steam_table.h_pt(
        round(P, STEAM_TBL_DIGITS),
        round(T, STEAM_TBL_DIGITS),
    )
    return (Q_(h, "btu/lb") * mass_rate).to("MJ/day")


def steam_enthalpy(
    pressure: pint.Quantity,
    steam_quality: pint.Quantity,
    mass_rate: pint.Quantity,
) -> pint.Quantity:
    """Steam enthalpy from steam quality (MJ/day)."""
    P = pressure.to("psia").magnitude
    hV = Q_(_steam_table.hV_p(round(P, STEAM_TBL_DIGITS)), "btu/lb")
    hL = Q_(_steam_table.hL_p(round(P, STEAM_TBL_DIGITS)), "btu/lb")

    h = hV * steam_quality + hL * (1 - steam_quality)
    return (mass_rate * h).to("MJ/day")
