"""
Fixtures for opgee_thermo tests.

These replicate the data that the original opgee test suite obtained by
loading test_model.xml and reading field.oil / field.gas / field.water.
All values are hard-coded here so the tests are self-contained and
independent of the opgee package.
"""
import pandas as pd
import pytest

from opgee_thermo.air import dry_air_properties
from opgee_thermo.chemical_info import build_component_properties, mol_weights, heating_value
from opgee_thermo.types import (
    AirProperties,
    ComponentProperties,
    StreamInfo,
    TemperaturePressure,
)
from opgee_thermo.units import ureg, Q_

# ---------------------------------------------------------------------------
# Test-model parameters  (from tests/files/test_model.xml, field "test")
# ---------------------------------------------------------------------------
TEST_API = Q_(32.8, "degAPI")
TEST_GOR = Q_(2429.30, "scf/bbl_oil")
TEST_RES_TEMP = Q_(200.0, "degF")
TEST_RES_PRESS = Q_(1556.6, "psia")
TEST_TDS = Q_(5000.0, "mg/L")

# Gas composition (mole fractions summing to ~1)
TEST_GAS_COMP = pd.Series(
    {
        "N2": 0.0286,
        "CO2": 0.0033,
        "C1": 0.8918,
        "C2": 0.053,
        "C3": 0.0162,
        "C4": 0.0071,
        "H2S": 0.0,
    },
    dtype="pint[frac]",
)

# Stream T/P used in many gas/oil tests
TEST_TP = TemperaturePressure(Q_(200.0, "degF"), Q_(1556.0, "psia"))
TEST_RES_TP = TemperaturePressure(TEST_RES_TEMP, TEST_RES_PRESS)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def props() -> ComponentProperties:
    """Component properties built once per test session."""
    return build_component_properties()


@pytest.fixture(scope="session")
def dry_air() -> AirProperties:
    return dry_air_properties()


@pytest.fixture(scope="session")
def oil_SG() -> "pint.Quantity":
    """Oil specific gravity from API = 32.8."""
    return Q_(141.5 / (131.5 + TEST_API.magnitude), "frac")


@pytest.fixture(scope="session")
def gas_SG(dry_air) -> "pint.Quantity":
    """Gas specific gravity for the test-model gas composition."""
    from opgee_thermo.oil import gas_specific_gravity
    mw = mol_weights()
    return gas_specific_gravity(TEST_GAS_COMP, mw, dry_air)


@pytest.fixture(scope="session")
def oil_LHV_mass() -> "pint.Quantity":
    from opgee_thermo.oil import mass_energy_density
    return mass_energy_density(TEST_API, use_LHV=True)


@pytest.fixture
def gas_stream(props) -> StreamInfo:
    """A StreamInfo matching the gas fixture in the original test suite."""
    gas_rates = pd.Series(
        {
            "N2": 4.90497,
            "CO2": 0.889247,
            "C1": 87.59032,
            "C2": 9.75715,
            "C3": 4.37353,
            "C4": 2.52654,
        },
        dtype="pint[tonne/day]",
    )
    return StreamInfo(
        tp=TEST_TP,
        gas_flow_rates=gas_rates,
        liquid_flow_rates={},
        API=TEST_API,
        component_names=list(gas_rates.index),
    )
