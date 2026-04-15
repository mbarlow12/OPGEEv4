# Thermodynamics Module Analysis

**File**: `opgee/thermodynamics.py`
**Lines**: 1,359
**Author**: Wennan Long

## Overview

The thermodynamics module provides physical property calculations for oil, gas, water, and air. It uses the `thermosteam` and `pyXSteam` libraries for chemical property lookups and steam table calculations.

## Key Classes

### ChemicalInfo (Singleton)

Central registry for chemical component properties:

```python
class ChemicalInfo(OpgeeObject):
    instance = None

    @classmethod
    def chemical(cls, component_name):
        """Get Chemical object for a component"""

    @classmethod
    def mol_weight(cls, component, with_units=True):
        """Get molecular weight (g/mol)"""

    @classmethod
    def mol_weights(cls):
        """Get all molecular weights as pd.Series"""
```

Components include:
- Hydrocarbons: C1 (methane) through C10+
- Non-hydrocarbons: N2, CO2, H2S, H2O, O2, Ar, He, H2

### AbstractSubstance

Base class for Oil, Gas, and Water with common properties:

```python
class AbstractSubstance(OpgeeObject):
    def __init__(self, field):
        self.res_tp = TemperaturePressure(field.attr("res_temp"), field.attr("res_press"))
        self.dry_air = DryAir(field)

        # Pre-computed property series for all components
        self.component_MW = ChemicalInfo.mol_weights()
        self.component_LHV_molar = pd.Series(...)   # joule/mole
        self.component_LHV_mass = ...               # joule/gram
        self.component_HHV_molar = pd.Series(...)
        self.component_Cp_STP = pd.Series(...)      # joule/g/kelvin
        self.component_Tc = pd.Series(...)          # kelvin
        self.component_Pc = pd.Series(...)          # Pa
        self.component_gas_rho_STP = pd.Series(...) # kg/m³

        self.steam_table = XSteam(XSteam.UNIT_SYSTEM_FLS)
```

### Oil

Crude oil thermodynamic properties:

```python
class Oil(AbstractSubstance):
    def __init__(self, field):
        self.API = field.attr("API")
        self.oil_specific_gravity = ureg.Quantity(141.5 / (131.5 + API.m), "frac")
        self.gas_specific_gravity = self._gas_specific_gravity()

    def bubble_point_pressure(self, oil_sg, gas_sg, gor):
        """Calculate bubble point pressure (psia)"""

    def solution_gas_oil_ratio(self, stream, oil_sg, gas_sg, gor):
        """Calculate GOR at stream conditions (scf/bbl)"""

    def saturated_formation_volume_factor(self, stream, oil_sg, gas_sg, gor):
        """Calculate oil formation volume factor"""

    def mass_energy_density(self):
        """Calculate oil LHV (MJ/kg)"""

    def energy_flow_rate(self, stream):
        """Calculate energy flow in stream (mmbtu/day)"""

    def volume_flow_rate(self, stream, temperature, pressure):
        """Calculate volumetric flow at T,P conditions"""
```

Key oil correlations:
- Bubble point from Valco and McCain (2002)
- Formation volume factor
- Oil density vs temperature/pressure
- API gravity conversions

### Gas

Natural gas thermodynamic properties:

```python
class Gas(AbstractSubstance):
    def __init__(self, field):
        self.gas_comp = field.attrs_with_prefix('gas_comp_')
        self.total_molar_weight = (gas_comp * component_MW).sum()
        self.gas_specific_gravity = self.total_molar_weight / air_MW

    def energy_flow_rate(self, stream):
        """Calculate gas energy flow (mmbtu/day)"""

    def volume_flow_rate_STP(self, stream):
        """Calculate gas volume at STP (scf/day)"""

    def component_mass_fractions(self, stream):
        """Get mass fractions of each component"""

    def specific_heat(self, stream):
        """Calculate Cp of gas mixture"""

    def Z_factor(self, stream):
        """Calculate gas compressibility factor"""
```

### Water

Water and steam properties using XSteam:

```python
class Water(AbstractSubstance):
    def __init__(self, field):
        self.steam = XSteam(XSteam.UNIT_SYSTEM_FLS)

    def saturated_temperature(self, pressure):
        """Get saturation temperature at pressure"""

    def saturated_pressure(self, temperature):
        """Get saturation pressure at temperature"""

    def specific_heat(self, temperature, pressure):
        """Get Cp at conditions"""

    def steam_enthalpy(self, temperature, pressure):
        """Get steam enthalpy (BTU/lb)"""

    def liquid_enthalpy(self, temperature, pressure):
        """Get liquid water enthalpy"""

    def latent_heat(self, temperature, pressure):
        """Get latent heat of vaporization"""
```

### Air Classes

```python
class Air(OpgeeObject):
    def __init__(self, field, composition):
        self.mixture = IdealMixture.from_chemicals(self.components)
        self.mol_weight = mixture.MW(mol_fraction)

    def density(self):
        """Calculate air density at STP (kg/m³)"""

class DryAir(Air):
    # N2: 78%, O2: 21%, Ar: 1%, trace gases
    pass

class WetAir(Air):  # Deprecated
    # Includes 2% H2O
    pass
```

## Standalone Functions

### Component Properties

```python
def rho(component, temperature, pressure, phase):
    """Calculate density at T, P for given phase (kg/m³)"""

def heating_value(component, use_LHV=True, with_units=True):
    """Get LHV or HHV (joule/mol)"""

def LHV(component, with_units=True):
    """Convenience function for lower heating value"""

def Cp(component, kelvin, with_units=True):
    """Specific heat capacity (joule/g/kelvin)"""

def Enthalpy(component, kelvin, phase=PHASE_GAS, with_units=True):
    """Calculate enthalpy (joule/mol)"""

def Tc(component, with_units=True):
    """Critical temperature (kelvin)"""

def Pc(component, with_units=True):
    """Critical pressure (Pa)"""

def Tsat(component, Psat, with_units=True):
    """Saturation temperature at pressure"""
```

## Key Correlations

### Oil Properties

| Property | Method | Reference |
|----------|--------|-----------|
| Bubble Point | `bubble_point_pressure()` | Valco & McCain 2002 |
| Solution GOR | `solution_gas_oil_ratio()` | Empirical |
| FVF | `saturated_formation_volume_factor()` | Standing correlation |
| Density | `density()` | API gravity correlation |
| Viscosity | `viscosity()` | Temperature correlation |

### Gas Properties

| Property | Method | Notes |
|----------|--------|-------|
| Z-factor | `Z_factor()` | Dranchuk & Abou-Kassem |
| Specific Gravity | `gas_specific_gravity` | MW ratio to air |
| Cp | `specific_heat()` | Molar mixing |
| Energy Content | `energy_flow_rate()` | Component LHV sum |

## Usage Patterns

### Getting Oil Energy Flow

```python
oil = field.oil
stream = process.find_input_stream("oil")
energy = oil.energy_flow_rate(stream)  # mmbtu/day
```

### Getting Gas Volume at STP

```python
gas = field.gas
stream = process.find_input_stream("gas")
volume = gas.volume_flow_rate_STP(stream)  # scf/day
```

### Steam Calculations

```python
water = field.water
T_sat = water.saturated_temperature(pressure)
h_steam = water.steam_enthalpy(temperature, pressure)
h_latent = water.latent_heat(temperature, pressure)
```

## Key Dependencies

- `thermosteam`: Chemical property database
- `pyXSteam`: Steam table calculations
- `pint`: Unit handling
- `pandas`: Property series
- `numpy`: Numerical calculations

## Units Convention

All properties use `pint` for unit safety:

| Property | Typical Unit |
|----------|-------------|
| Temperature | kelvin, degF, degC |
| Pressure | psia, Pa, bar |
| Density | kg/m³, lb/ft³ |
| Energy | joule/mol, mmbtu, MJ |
| Volume | scf, m³, bbl |
| Mass | kg, tonne, lb |

## Performance Notes

- `ChemicalInfo` is a singleton - initialized once
- Component property series pre-computed at field initialization
- Use `with_units=False` for performance-critical calculations
- Large property tables cached in `AbstractSubstance.__init__`
