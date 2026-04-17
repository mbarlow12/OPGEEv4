"""Tests for opgee.chemistry — shared component chemistry constants."""
from opgee.chemistry import (
    PHASE_GAS, PHASE_LIQUID, PHASE_SOLID,
    COMPONENT_NAMES, CARBON_NUMBER, VOCS, HYDROCARBONS,
    R_GAS,
)


def test_phase_constants():
    assert PHASE_GAS == "gas"
    assert PHASE_LIQUID == "liquid"
    assert PHASE_SOLID == "solid"


def test_component_names_populated():
    assert len(COMPONENT_NAMES) > 20
    assert "CO2" in COMPONENT_NAMES
    assert "CH4" in COMPONENT_NAMES or "C1" in COMPONENT_NAMES  # C1 is the carbon-number form of methane
    assert "C1" in COMPONENT_NAMES


def test_carbon_numbers():
    assert CARBON_NUMBER["C1"] == 1
    assert CARBON_NUMBER["C5"] == 5
    assert len(CARBON_NUMBER) > 0


def test_vocs():
    assert isinstance(VOCS, list)
    assert len(VOCS) > 0


def test_hydrocarbons():
    assert isinstance(HYDROCARBONS, list)
    assert len(HYDROCARBONS) > 0


def test_r_gas():
    # Universal gas constant in J/(mol·K)
    assert abs(R_GAS.magnitude - 8.31446) < 0.001
    assert str(R_GAS.units) == "joule / kelvin / mole"
