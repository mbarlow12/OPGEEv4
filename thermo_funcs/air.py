"""
Air mixture calculations (dry and wet).

All functions are pure and return :class:`pint.Quantity` values.
"""
from __future__ import annotations

import pint
from thermosteam import IdealMixture

from .constants import STD_PRESSURE, STD_TEMPERATURE
from .types import AirProperties
from .units import ureg, Q_

# ---------------------------------------------------------------------------
# Standard compositions
# ---------------------------------------------------------------------------
DRY_AIR_COMPOSITION: list[tuple[str, float]] = [
    ("Nitrogen", 0.78084),
    ("Oxygen", 0.20946),
    ("Argon", 0.00934),
    ("Carbon dioxide", 0.000412),
    ("Neon", 0.00001818),
    ("Helium", 0.00000524),
    ("Methane", 0.00000179),
    ("Krypton", 0.0000010),
    ("Hydrogen", 0.0000005),
    ("Xenon", 0.00000009),
]

WET_AIR_COMPOSITION: list[tuple[str, float]] = [
    ("N2", 0.774396),
    ("O2", 0.20531),
    ("CO2", 0.000294),
    ("H2O", 0.02),
]


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------
def compute_air_properties(
    composition: list[tuple[str, float]],
    std_T: pint.Quantity | None = None,
    std_P: pint.Quantity | None = None,
) -> AirProperties:
    """Build an :class:`AirProperties` from a composition list.

    Parameters
    ----------
    composition
        Sequence of ``(chemical_name, mol_fraction)`` pairs.
    std_T, std_P
        Temperature / pressure at which to evaluate the density.
        Default to the module :data:`STD_TEMPERATURE` / :data:`STD_PRESSURE`.
    """
    std_T = std_T if std_T is not None else STD_TEMPERATURE
    std_P = std_P if std_P is not None else STD_PRESSURE

    names = [n for n, _ in composition]
    fracs = [f for _, f in composition]
    mixture = IdealMixture.from_chemicals(names)

    mw = Q_(mixture.MW(fracs), "g/mol")

    T_K = std_T.to("kelvin").magnitude
    P_Pa = std_P.to("Pa").magnitude
    density = Q_(mixture.rho("g", fracs, T_K, P_Pa), "kg/m**3")

    return AirProperties(mol_weight=mw, density_STP=density)


def dry_air_properties(
    std_T: pint.Quantity | None = None,
    std_P: pint.Quantity | None = None,
) -> AirProperties:
    """Pre-built :class:`AirProperties` for standard dry air."""
    return compute_air_properties(DRY_AIR_COMPOSITION, std_T, std_P)


def wet_air_properties(
    std_T: pint.Quantity | None = None,
    std_P: pint.Quantity | None = None,
) -> AirProperties:
    """Pre-built :class:`AirProperties` for standard wet air."""
    return compute_air_properties(WET_AIR_COMPOSITION, std_T, std_P)
