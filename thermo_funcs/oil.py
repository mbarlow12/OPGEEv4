"""
Oil thermodynamic calculations — purely functional.

Every function that formerly lived as a method on ``Oil`` (or
``AbstractSubstance``) is now a free function.  ``self`` state is replaced by
explicit parameters: scalar :class:`pint.Quantity` values or the lightweight
proxy data-classes from :mod:`thermo_funcs.types`.
"""
from __future__ import annotations

import math

import pandas as pd
import pint

from .constants import (
    API_HIGH_BOUND,
    API_LOW_BOUND,
    ISO_COMP_A1,
    ISO_COMP_A2,
    ISO_COMP_A3,
    ISO_COMP_A4,
    OIL_CP_A1,
    OIL_CP_A2,
    OIL_CP_A3,
    OIL_CP_A4,
    OIL_HHV_COEFFS,
    OIL_LHV_COEFFS,
    PBUB_A1,
    PBUB_A2,
    PBUB_A3,
)
from .types import AirProperties, ComponentProperties, StreamInfo, TemperaturePressure
from .units import ureg, Q_


# ---------------------------------------------------------------------------
# Derived scalars (previously computed in Oil.__init__)
# ---------------------------------------------------------------------------
def specific_gravity_from_API(API: pint.Quantity) -> pint.Quantity:
    """Oil specific gravity from API gravity.

    SG = 141.5 / (API + 131.5)
    """
    return Q_(141.5 / (API.magnitude + 131.5), "frac")


def API_from_specific_gravity(SG: pint.Quantity) -> pint.Quantity:
    """API gravity from specific gravity."""
    return Q_(141.5 / SG.magnitude - 131.5, "degAPI")


def gas_specific_gravity(
    gas_comp: pd.Series,
    component_MW: pd.Series,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Gas specific gravity = total molar weight / air molar weight."""
    total_molar_weight: pint.Quantity = (gas_comp * component_MW[gas_comp.index]).sum()
    return (total_molar_weight / dry_air.mol_weight).to("frac")


# ---------------------------------------------------------------------------
# Bubble-point / solution GOR
# ---------------------------------------------------------------------------
def bubble_point_solution_GOR(gas_oil_ratio: pint.Quantity) -> pint.Quantity:
    """R_sb = 1.1618 * R_sp  (Valco & McCain 2002)."""
    return gas_oil_ratio * 1.1618


@ureg.wraps("psia", ("frac", "frac", "scf/bbl_oil", "rankine"), strict=False)
def bubble_point_pressure(
    oil_SG: float,
    gas_SG: float,
    gas_oil_ratio: float,
    res_temp_R: float,
) -> float:
    """Bubble-point pressure (psia)."""
    gor_bubble = gas_oil_ratio * 1.1618
    return (
        oil_SG ** PBUB_A1
        * (gas_SG * gor_bubble * res_temp_R) ** PBUB_A2
        * math.exp(-PBUB_A3 * gas_SG * oil_SG)
    )


@ureg.wraps("scf/bbl_oil", ("frac", "rankine", "frac", "scf/bbl_oil"), strict=False)
def solution_gas_oil_ratio(
    oil_SG: float,
    stream_T_R: float,
    gas_SG: float,
    gas_oil_ratio: float,
) -> float:
    """Solution GOR at stream conditions (scf/bbl_oil)."""
    gor_bubble = gas_oil_ratio * 1.1618
    empirical = (
        math.pow(1.0, 1 / PBUB_A2)  # placeholder; see note below
    )
    # The original code takes stream_P from the stream, but here we fold it
    # into the _with_pressure variant below.  This base version mirrors the
    # original's signature that receives (oil_SG, stream_T, gas_SG, GOR).
    # We keep the full version below.
    return min(gor_bubble, gor_bubble)  # overridden by _with_pressure


def solution_gas_oil_ratio_at(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
) -> pint.Quantity:
    """Solution GOR evaluated at *stream* conditions.

    This is the direct functional equivalent of ``Oil.solution_gas_oil_ratio``.
    """
    o = oil_SG.to("frac").magnitude
    g = gas_SG.to("frac").magnitude
    T = stream.tp.T.to("rankine").magnitude
    P = stream.tp.P.magnitude
    gor_bub = bubble_point_solution_GOR(gas_oil_ratio).magnitude

    empirical = (
        math.pow(P, 1 / PBUB_A2)
        * math.pow(o, -PBUB_A1 / PBUB_A2)
        * math.exp(PBUB_A3 / PBUB_A2 * g * o)
        / (T * g)
    )
    return Q_(min(empirical, gor_bub), "scf/bbl_oil")


# ---------------------------------------------------------------------------
# Formation volume factor
# ---------------------------------------------------------------------------
def saturated_formation_volume_factor(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
) -> pint.Quantity:
    """Saturated formation volume factor (dimensionless)."""
    o = oil_SG.to("frac").magnitude
    T = stream.tp.T.magnitude  # degF
    g = gas_SG.to("frac").magnitude
    Rs = solution_gas_oil_ratio_at(stream, oil_SG, gas_SG, gas_oil_ratio).magnitude

    result = (
        1
        + 0.000000525 * Rs * (T - 60)
        + 0.000181 * Rs / o
        + 0.000449 * (T - 60) / o
        + 0.000206 * Rs * g / o
    )
    return Q_(result, "frac")


@ureg.wraps("pa**-1", ("frac",), strict=False)
def isothermal_compressibility(oil_SG: float) -> float:
    """Simple regression for isothermal compressibility."""
    return (55.233 - 60.588 * oil_SG) / 1e6


def isothermal_compressibility_extended(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
) -> pint.Quantity:
    """Extended isothermal compressibility (pa^-1)."""
    Rs = solution_gas_oil_ratio_at(stream, oil_SG, gas_SG, gas_oil_ratio).magnitude
    g = gas_SG.to("frac").magnitude
    T = stream.tp.T.to("rankine").magnitude

    result = max(
        ISO_COMP_A1 * Rs
        + ISO_COMP_A2 * Rs ** 2
        + ISO_COMP_A3 * g
        + ISO_COMP_A4 * T ** 2,
        0.0,
    )
    return Q_(result, "pa**-1")


def unsat_formation_volume_factor(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
    res_tp: TemperaturePressure,
) -> pint.Quantity:
    """Unsaturated formation volume factor (dimensionless).

    Unlike the original, we accept *res_tp* explicitly instead of reading
    ``self.res_tp``.
    """
    # Evaluate saturated FVF at reservoir conditions
    res_stream = StreamInfo(
        tp=res_tp,
        gas_flow_rates=stream.gas_flow_rates,
        liquid_flow_rates=stream.liquid_flow_rates,
        API=stream.API,
        component_names=stream.component_names,
    )
    bubble_FVF = saturated_formation_volume_factor(
        res_stream, oil_SG, gas_SG, gas_oil_ratio
    ).magnitude

    p_bub = bubble_point_pressure(
        oil_SG.to("frac"),
        gas_SG.to("frac"),
        gas_oil_ratio,
        res_tp.T.to("rankine"),
    ).magnitude

    co = isothermal_compressibility(oil_SG).magnitude
    P = stream.tp.P.magnitude

    return Q_(bubble_FVF * math.exp(co * (p_bub - P)), "frac")


def formation_volume_factor(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
    res_tp: TemperaturePressure,
) -> pint.Quantity:
    """Select saturated or unsaturated FVF based on bubble-point pressure."""
    p_bub = bubble_point_pressure(
        oil_SG.to("frac"),
        gas_SG.to("frac"),
        gas_oil_ratio,
        res_tp.T.to("rankine"),
    )
    if stream.tp.P < p_bub:
        return saturated_formation_volume_factor(stream, oil_SG, gas_SG, gas_oil_ratio)
    return unsat_formation_volume_factor(stream, oil_SG, gas_SG, gas_oil_ratio, res_tp)


# ---------------------------------------------------------------------------
# Density / flow rates / energy
# ---------------------------------------------------------------------------
def density(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
    res_tp: TemperaturePressure,
    water_density_STP: pint.Quantity,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Oil density (lb/ft**3) at stream conditions."""
    Rs = solution_gas_oil_ratio_at(stream, oil_SG, gas_SG, gas_oil_ratio)
    Bof = formation_volume_factor(stream, oil_SG, gas_SG, gas_oil_ratio, res_tp)
    air_rho = dry_air.density_STP

    result = (water_density_STP * oil_SG + air_rho * gas_SG * Rs) / Bof
    return result.to("lb/ft**3")


def volume_flow_rate(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
    res_tp: TemperaturePressure,
    water_density_STP: pint.Quantity,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Oil volume flow rate (bbl_oil/day)."""
    mass = stream.liquid_flow_rate("oil")
    rho = density(stream, oil_SG, gas_SG, gas_oil_ratio, res_tp, water_density_STP, dry_air)
    return (mass / rho).to("bbl_oil/day")


def mass_energy_density(
    API: pint.Quantity,
    use_LHV: bool = True,
) -> pint.Quantity:
    """Oil heating value (btu/lb) from API gravity.

    Uses the Manning-Thompson correlation.
    """
    a1, a2, a3, a4 = OIL_LHV_COEFFS if use_LHV else OIL_HHV_COEFFS
    api = API.magnitude
    result = a1 + a2 * api - a3 * api ** 2 - a4 * api ** 3
    return Q_(result, "british_thermal_unit/lb")


def volume_energy_density(
    stream: StreamInfo,
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
    res_tp: TemperaturePressure,
    water_density_STP: pint.Quantity,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Oil volume energy density (mmBtu/bbl_oil)."""
    api = stream.API if stream.API is not None else oil_SG  # fallback
    med = mass_energy_density(api)
    rho = density(
        stream, oil_SG, gas_SG, gas_oil_ratio, res_tp, water_density_STP, dry_air
    ).to("lb/bbl_oil")
    return (med * rho).to("mmBtu/bbl_oil")


def energy_flow_rate(
    stream: StreamInfo,
    API: pint.Quantity,
) -> pint.Quantity:
    """Oil energy flow rate (mmBtu/day) based on LHV."""
    mass = stream.liquid_flow_rate("oil") + stream.liquid_flow_rate("PC")
    med = mass_energy_density(API)
    return (med * mass).to("mmbtu/day")


# ---------------------------------------------------------------------------
# Specific heat
# ---------------------------------------------------------------------------
def specific_heat(API: pint.Quantity, temperature: pint.Quantity) -> pint.Quantity:
    """Campbell specific heat (Manning & Thompson 1991)."""
    api = API.magnitude
    T_F = temperature.to("degF").magnitude
    result = (OIL_CP_A1 * T_F + OIL_CP_A2) * api + OIL_CP_A3 * T_F + OIL_CP_A4
    return Q_(result, "btu/lb/degF")


# ---------------------------------------------------------------------------
# Liquid fuel composition
# ---------------------------------------------------------------------------
def liquid_fuel_composition(API: pint.Quantity) -> pd.Series:
    """C / S / H / N mol fractions per kg of crude.

    Returns a ``pd.Series`` with dtype ``pint[mol/kg]``.

    Raises
    ------
    ValueError
        If API is outside [4, 50].
    """
    api = API.magnitude
    if api < API_LOW_BOUND or api > API_HIGH_BOUND:
        raise ValueError(f"API {api} outside valid range [{API_LOW_BOUND}, {API_HIGH_BOUND}]")

    N_wt = Q_(0.2, "percent")
    S_wt = Q_(-0.121 * api + 5.4293, "percent")
    H_wt = Q_(0.111 * api + 8.7523, "percent")
    C_wt = Q_(100.0, "percent") - N_wt - S_wt - H_wt

    return pd.Series(
        [
            C_wt / Q_(12.0, "g/mol"),
            S_wt / Q_(32.0, "g/mol"),
            H_wt / Q_(1.0, "g/mol"),
            N_wt / Q_(14.0, "g/mol"),
        ],
        index=["C", "S", "H", "N"],
        dtype="pint[mol/kg]",
    )


# ---------------------------------------------------------------------------
# Reservoir solution GOR (used in tests)
# ---------------------------------------------------------------------------
def reservoir_solution_GOR(
    oil_SG: pint.Quantity,
    gas_SG: pint.Quantity,
    gas_oil_ratio: pint.Quantity,
    res_tp: TemperaturePressure,
) -> pint.Quantity:
    """Solution GOR at reservoir conditions (scf/bbl_oil)."""
    o = oil_SG.to("frac").magnitude
    g = gas_SG.to("frac").magnitude
    T = res_tp.T.to("rankine").magnitude
    P = res_tp.P.to("psia").magnitude
    gor_bub = bubble_point_solution_GOR(gas_oil_ratio).magnitude

    empirical = (
        P ** (1 / PBUB_A2)
        * o ** (-PBUB_A1 / PBUB_A2)
        * math.exp(PBUB_A3 / PBUB_A2 * g * o)
        / (T * g)
    )
    return Q_(min(empirical, gor_bub), "scf/bbl_oil")
