"""
Physical and model constants used by the thermodynamic calculations.

All values that were previously fetched via ``model.const(...)`` or defined
as class-level attributes are collected here as module-level constants.
"""
from __future__ import annotations

import pint

from .units import ureg, Q_

# ---------------------------------------------------------------------------
# Standard conditions
# ---------------------------------------------------------------------------
STD_TEMPERATURE: pint.Quantity = Q_(60.0, "degF")
"""Standard temperature (60 degF)."""

STD_PRESSURE: pint.Quantity = Q_(14.676, "psia")
"""Standard pressure (14.676 psia)."""

# ---------------------------------------------------------------------------
# Universal / physical constants
# ---------------------------------------------------------------------------
UNIVERSAL_GAS_CONSTANT: pint.Quantity = Q_(8.31446261815324, "joule/mol/kelvin")
"""Universal gas constant R."""

GRAVITATIONAL_ACCELERATION: pint.Quantity = Q_(9.8, "m/s**2")

# ---------------------------------------------------------------------------
# Oil correlation constants  (bubble-point, compressibility)
# ---------------------------------------------------------------------------
PBUB_A1: float = 5.527215
PBUB_A2: float = 0.783716
PBUB_A3: float = 1.841408

# Isothermal-compressibility (extended) constants
ISO_COMP_A1: float = -0.000013668
ISO_COMP_A2: float = -0.00000001925682
ISO_COMP_A3: float = 0.02408026
ISO_COMP_A4: float = -0.0000000926091

# Oil LHV / HHV correlation coefficients  (mass_energy_density)
OIL_LHV_COEFFS: tuple[float, float, float, float] = (16796.0, 54.4, 0.217, 0.0019)
OIL_HHV_COEFFS: tuple[float, float, float, float] = (17672.0, 66.6, 0.316, 0.0014)

# Campbell specific-heat constants
OIL_CP_A1: float = -1.39e-6
OIL_CP_A2: float = 1.847e-3
OIL_CP_A3: float = 6.32e-4
OIL_CP_A4: float = 3.52e-1

# Liquid-fuel composition bounds
API_LOW_BOUND: float = 4.0
API_HIGH_BOUND: float = 50.0

# Redlich-Kwong EOS constants
RK_A: float = 0.42748
RK_B: float = 0.08664

# ---------------------------------------------------------------------------
# Phase labels (matching opgee.stream constants)
# ---------------------------------------------------------------------------
PHASE_GAS: str = "gas"
PHASE_LIQUID: str = "liquid"
PHASE_SOLID: str = "solid"

# ---------------------------------------------------------------------------
# Water
# ---------------------------------------------------------------------------
STEAM_TBL_DIGITS: int = 2
"""Required decimal places for pyXSteam table look-ups."""
