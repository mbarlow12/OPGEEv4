"""
Gas thermodynamic calculations — purely functional.

Every function that formerly lived as a method on ``Gas`` is now a free
function.  Stream data is passed via :class:`~thermo_funcs.types.StreamInfo`
and component look-up tables via
:class:`~thermo_funcs.types.ComponentProperties`.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pint
from pyXSteam.XSteam import XSteam

from .chemical_info import Cp as chem_Cp, enthalpy as chem_enthalpy, mol_weights as chem_mol_weights
from .constants import (
    PHASE_GAS,
    RK_A,
    RK_B,
    STD_PRESSURE,
    STD_TEMPERATURE,
    STEAM_TBL_DIGITS,
    UNIVERSAL_GAS_CONSTANT,
)
from .types import AirProperties, ComponentProperties, StreamInfo
from .units import ureg, Q_


# ---------------------------------------------------------------------------
# Molar flow helpers
# ---------------------------------------------------------------------------
def total_molar_flow_rate(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Total molar flow rate (mol/day) of all gas components in *stream*."""
    mass = stream.total_gases_rates()
    return (mass / props.MW[mass.index]).sum().to("mol/day")


def molar_flow_rate(
    stream: StreamInfo,
    name: str,
    props: ComponentProperties,
) -> pint.Quantity:
    """Molar flow rate (mol/day) of a single gas component *name*."""
    mass = stream.gas_flow_rate(name)
    return (mass / props.MW[name]).to("mol/day")


def molar_flow_rates(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pd.Series:
    """Per-component molar flow rates (mol/day)."""
    names = stream.component_names or list(stream.gas_flow_rates.index)
    return pd.Series({n: molar_flow_rate(stream, n, props) for n in names})


# ---------------------------------------------------------------------------
# Molar fractions
# ---------------------------------------------------------------------------
def component_molar_fraction(
    name: str,
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Molar fraction of a single component *name* in the gas phase."""
    total = total_molar_flow_rate(stream, props)
    mass = stream.gas_flow_rate(name)
    mw = chem_mol_weights()[name]
    molar = mass.to("g/day") / mw
    return (molar / total).to("frac")


def component_molar_fractions(
    stream: StreamInfo,
    props: ComponentProperties,
    index: list[str] | None = None,
) -> pd.Series:
    """Molar fractions of all (or selected) gas components.

    Returns a ``pd.Series`` with dtype ``pint[fraction]``.

    Raises
    ------
    ValueError
        If the stream has no gas flow rates.
    """
    total = total_molar_flow_rate(stream, props)
    rates = stream.positive_gas_flow_rates(index)

    if len(rates) == 0:
        raise ValueError("Cannot compute molar fractions on an empty stream")

    idx = rates.index if index is None else index
    molar = rates / props.MW[idx]
    result = molar / total
    return pd.Series(result, dtype="pint[fraction]")


def component_mass_fractions(
    molar_fracs: pd.Series,
    props: ComponentProperties,
) -> pd.Series:
    """Mass fractions from molar fractions."""
    mw_mix = molar_weight_from_molar_fracs(molar_fracs, props)
    return molar_fracs * props.MW[molar_fracs.index] / mw_mix


# ---------------------------------------------------------------------------
# Specific gravity / molar weight
# ---------------------------------------------------------------------------
def specific_gravity(
    stream: StreamInfo,
    props: ComponentProperties,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Gas specific gravity (dimensionless)."""
    mol_fracs = component_molar_fractions(stream, props)
    sg = (mol_fracs * props.MW[mol_fracs.index]).sum()
    return sg / dry_air.mol_weight


def molar_weight_from_molar_fracs(
    molar_fracs: pd.Series,
    props: ComponentProperties,
) -> pint.Quantity:
    """Mixture molar weight from molar fractions (g/mol)."""
    return (props.MW[molar_fracs.index] * molar_fracs).sum().to("g/mol")


def molar_weight(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Mixture molar weight of the gas phase in *stream* (g/mol)."""
    fracs = component_molar_fractions(stream, props)
    return molar_weight_from_molar_fracs(fracs, props)


# ---------------------------------------------------------------------------
# Ratio of specific heats (Cp/Cv)
# ---------------------------------------------------------------------------
def ratio_of_specific_heat(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Ratio of specific heats k = Cp / Cv (dimensionless)."""
    mass = stream.positive_gas_flow_rates()
    mw = props.MW[mass.index]
    cp = props.Cp_STP[mass.index]
    R_spec = UNIVERSAL_GAS_CONSTANT / mw  # J/(g·K)
    cv = cp - R_spec
    return ((mass * cp).sum() / (mass * cv).sum()).to("frac")


# ---------------------------------------------------------------------------
# Heat capacity of gas stream
# ---------------------------------------------------------------------------
def heat_capacity(
    stream: StreamInfo,
) -> pint.Quantity:
    """Gas heat capacity (btu/degF/day) at stream temperature."""
    mass = stream.positive_gas_flow_rates()
    if mass.empty:
        return Q_(0.0, "btu/degF/day")

    T_K = stream.tp.T.to("kelvin").magnitude
    cp_series = pd.Series(
        {n: chem_Cp(n, Q_(T_K, "kelvin")).magnitude for n in mass.index},
        dtype="pint[joule/g/kelvin]",
    )
    return (mass * cp_series).sum().to("btu/degF/day")


# ---------------------------------------------------------------------------
# Pseudo-critical properties
# ---------------------------------------------------------------------------
def uncorrected_pseudocritical_temperature_and_pressure(
    stream: StreamInfo,
    props: ComponentProperties,
) -> tuple[pint.Quantity, pint.Quantity]:
    """Return ``(T_pc, P_pc)`` in Rankine / psia (uncorrected)."""
    mass = stream.positive_gas_flow_rates()
    mol_frac = component_molar_fractions(stream, props).pint.m
    Tc_R = props.Tc[mass.index].pint.to("rankine").pint.m
    Pc_psia = props.Pc[mass.index].pint.to("psia").pint.m

    t1 = (mol_frac * Tc_R / Pc_psia ** 0.5).sum()
    t2 = (mol_frac * Tc_R / Pc_psia).sum()
    t3 = (mol_frac * (Tc_R / Pc_psia) ** 0.5).sum()

    t1_sq = t1 ** 2
    denom = (1 / 3) * t2 + (2 / 3) * t3 ** 2

    T_pc = Q_(t1_sq / denom, "rankine")
    P_pc = Q_(t1_sq / denom ** 2, "psia")
    return T_pc, P_pc


def corrected_pseudocritical_temperature(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Corrected pseudo-critical temperature (rankine)."""
    T_pc, _ = uncorrected_pseudocritical_temperature_and_pressure(stream, props)
    T_pc_m = T_pc.magnitude
    y_O2 = component_molar_fraction("O2", stream, props).magnitude
    y_H2S = component_molar_fraction("H2S", stream, props).magnitude

    result = (
        T_pc_m
        - 120 * ((y_O2 + y_H2S) ** 0.9 - (y_O2 + y_H2S) ** 1.6)
        + 15 * (y_H2S ** 0.5 - y_H2S ** 4)
    )
    return Q_(result, "rankine")


def corrected_pseudocritical_pressure(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Corrected pseudo-critical pressure (psia)."""
    T_pc, P_pc = uncorrected_pseudocritical_temperature_and_pressure(stream, props)
    T_pc_corr = corrected_pseudocritical_temperature(stream, props)
    y_H2S = component_molar_fraction("H2S", stream, props)

    return (
        P_pc * T_pc_corr
        / (T_pc - y_H2S * (1 - y_H2S) * (T_pc - T_pc_corr))
    )


# ---------------------------------------------------------------------------
# Reduced properties
# ---------------------------------------------------------------------------
def reduced_temperature(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Reduced temperature T_r = T / T_pc (dimensionless)."""
    T_pc = corrected_pseudocritical_temperature(stream, props)
    return (stream.tp.T.to("rankine") / T_pc).to("frac")


def reduced_pressure(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Reduced pressure P_r = P / P_pc (dimensionless)."""
    P_pc = corrected_pseudocritical_pressure(stream, props)
    return (stream.tp.P / P_pc).to("frac")


# ---------------------------------------------------------------------------
# Compressibility factor — Redlich-Kwong EOS
# ---------------------------------------------------------------------------
@ureg.wraps("frac", ("frac", "frac"))
def Z_factor(
    reduced_temperature: float,
    reduced_pressure: float,
) -> float:
    """Compressibility factor via Redlich-Kwong cubic EOS.

    Solves for the highest real root of the cubic in Z.
    """
    Tr = reduced_temperature
    Pr = reduced_pressure
    a = RK_A * (Pr / Tr ** 2.5)
    b = RK_B * (Pr / Tr)

    alpha = (1 / 3) * (3 * (a - b - b ** 2) - 1)
    beta = (1 / 27) * (-2 + 9 * (a - b - b ** 2) - 27 * a * b)
    d = (beta ** 2 / 4) + (alpha ** 3 / 27)

    if d < 0:
        theta = math.acos(
            -np.sign(beta) * math.sqrt((beta ** 2 / 4) / (-alpha ** 3 / 27))
        )
        z_roots = [
            2 * math.sqrt(-alpha / 3) * math.cos(theta / 3 + i * 2 * math.pi / 3) + 1 / 3
            for i in range(3)
        ]
    else:
        a_star = np.cbrt((-beta / 2) + np.sqrt(d))
        b_star = np.cbrt((-beta / 2) - np.sqrt(d))
        if d > 0:
            z_roots = [a_star + b_star + 1 / 3]
        else:
            z_roots = [
                a_star + b_star + 1 / 3,
                -(1 / 2) * (a_star + b_star) + 1 / 3,
                -(1 / 2) * (a_star + b_star) + 1 / 3,
            ]

    return Q_(max(z_roots), "frac")


# ---------------------------------------------------------------------------
# Volume factor / density / viscosity
# ---------------------------------------------------------------------------
def volume_factor(
    stream: StreamInfo,
    props: ComponentProperties,
    std_T: pint.Quantity | None = None,
    std_P: pint.Quantity | None = None,
) -> pint.Quantity:
    """Gas volume factor (dimensionless)."""
    std_T = std_T if std_T is not None else STD_TEMPERATURE
    std_P = std_P if std_P is not None else STD_PRESSURE

    Tr = reduced_temperature(stream, props)
    Pr = reduced_pressure(stream, props)
    z = Z_factor(Tr, Pr)

    T_s = stream.tp.T.to("rankine")
    P_s = stream.tp.P
    T_a = std_T.to("rankine")
    P_a = std_P

    return (P_a * z * T_s / (P_s * T_a)).to("frac")


def gas_density(
    stream: StreamInfo,
    props: ComponentProperties,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Gas density (tonne/m**3) at stream conditions."""
    vf = volume_factor(stream, props)
    sg = specific_gravity(stream, props, dry_air)
    return (dry_air.density_STP.to("tonne/m**3") * sg / vf)


def viscosity(
    stream: StreamInfo,
    props: ComponentProperties,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Natural gas viscosity via Lee et al. (1966) correlation (cP)."""
    mw = molar_weight(stream, props).magnitude
    rho = gas_density(stream, props, dry_air).to("lb/ft**3").magnitude
    T = stream.tp.T.to("rankine").magnitude

    K = (9.4 + 0.02 * mw) * T ** 1.5 / (209 + 19 * mw + T)
    X = 3.5 + 986 / T + 0.01 * mw
    Y = 2.4 - 0.2 * X

    mu = 1.10e-4 * K * math.exp(X * (rho / 62.4) ** Y)
    return Q_(mu, "centipoise")


# ---------------------------------------------------------------------------
# Volume / mass flow rates
# ---------------------------------------------------------------------------
def gas_volume_flow_rate(
    stream: StreamInfo,
    props: ComponentProperties,
    dry_air: AirProperties,
) -> pint.Quantity:
    """Total gas volume flow rate (m**3/day) at stream conditions."""
    total_mass = stream.total_gas_rate()
    rho = gas_density(stream, props, dry_air)
    return total_mass / rho


def gas_volume_flow_rate_STP(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Total gas volume flow rate at STP (m**3/day)."""
    return gas_volume_flow_rates_STP(stream, props).sum()


def gas_volume_flow_rates_STP(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pd.Series:
    """Per-component gas volume flow rates at STP (m**3/day)."""
    rates = stream.positive_gas_flow_rates()
    return rates / props.gas_rho_STP[rates.index]


# ---------------------------------------------------------------------------
# Energy density / flow rate
# ---------------------------------------------------------------------------
def mass_energy_density(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Gas mass energy density (MJ/kg) based on LHV."""
    mass = stream.positive_gas_flow_rates()
    if len(mass) == 0:
        return Q_(0.0, "MJ/kg")

    total = stream.total_gas_rate()
    hv = props.LHV_molar[mass.index]
    mw = props.MW[mass.index]
    return (mass / total * hv / mw).sum().to("MJ/kg")


def mass_energy_density_from_molar_fracs(
    molar_fracs: pd.Series,
    props: ComponentProperties,
) -> pint.Quantity:
    """Gas mass energy density from molar fractions (MJ/kg)."""
    hv = props.LHV_molar[molar_fracs.index]
    mw = props.MW[molar_fracs.index]
    return (hv * molar_fracs / mw).sum().to("MJ/kg")


def volume_energy_density(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Gas volume energy density (btu/ft**3)."""
    mass = stream.positive_gas_flow_rates()
    lhv = props.LHV_molar[mass.index]
    mw = props.MW[mass.index]
    rho = props.gas_rho_STP[mass.index]
    mol_frac = component_molar_fractions(stream, props)
    return (mol_frac * rho * lhv / mw).sum().to("Btu/ft**3")


def energy_flow_rate(
    stream: StreamInfo,
    props: ComponentProperties,
) -> pint.Quantity:
    """Gas energy flow rate (mmBtu/day) based on LHV."""
    total = stream.total_gas_rate()
    med = mass_energy_density(stream, props)
    return (total * med).to("mmBtu/day")


# ---------------------------------------------------------------------------
# Combustion enthalpy (for OTSG / HRSG)
# ---------------------------------------------------------------------------
def combustion_enthalpy(
    molar_fracs: pd.Series,
    temperature: pint.Quantity,
    phase: str,
) -> pd.Series:
    """Per-component enthalpy Series (joule/mol) for combustion calculations.

    For H2O in gas phase, uses steam-table corrections.
    """
    T_K = temperature.to("kelvin").magnitude

    enth = pd.Series(
        {n: chem_enthalpy(n, Q_(T_K, "kelvin"), phase).magnitude for n in molar_fracs.index},
        dtype="pint[joule/mole]",
    )

    if "H2O" in molar_fracs and phase == PHASE_GAS:
        steam = XSteam(XSteam.UNIT_SYSTEM_FLS)
        T_F = temperature.to("degF").magnitude
        mw_h2o = chem_mol_weights()["H2O"]

        vapor_h = Q_(steam.hV_t(T_F), "btu/lb") * mw_h2o

        ref_T_F = Q_(30, "degC").to("degF").magnitude
        latent = Q_(steam.hV_t(ref_T_F) - steam.hL_t(ref_T_F), "btu/lb") * mw_h2o

        enth["H2O"] = max(vapor_h - latent, Q_(0.0, "joule/mole"))

    return enth
