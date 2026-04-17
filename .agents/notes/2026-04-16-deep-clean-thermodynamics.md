# Deep Clean: thermodynamics.py Symbol-Level Proposal

**File**: `opgee/thermodynamics.py` (1,359 lines)
**Branch**: `refactor/v5-deep-clean`

## Imports

| Import | Action | Notes |
|--------|--------|-------|
| `math`, `pandas`, `numpy`, `pint` | RETAIN | Standard libs |
| `pyXSteam.XSteam` | RETAIN | Steam table lookups |
| `thermosteam.Chemical`, `thermosteam.IdealMixture` | RETAIN | PubChem data |
| `from .units import ureg` | RETAIN | Pint unit registry |
| `from .core import OpgeeObject, STP, TemperaturePressure` | MODIFY | Drop `OpgeeObject` inheritance; keep `STP` and `TemperaturePressure` (pure data, no XML) |
| `from .error import ModelValidationError` | RETAIN | Used at lines 733, 831; plain exception class |
| `from .stream import PHASE_GAS, PHASE_LIQUID, PHASE_SOLID, Stream` | RETAIN | Core domain types |

## Module-Level Functions

All RETAIN -- pure thermodynamic lookups, no XML/config deps.

| Symbol | Lines | Notes |
|--------|-------|-------|
| `rho()` | 63-85 | Density at T,P,phase |
| `heating_value()` | 88-106 | LHV/HHV from thermosteam |
| `LHV()` | 109-118 | Convenience wrapper |
| `Cp()` | 121-135 | Specific heat |
| `Enthalpy()` | 143-166 | Component enthalpy |
| `Tsat()` | 170-186 | Saturation temperature |
| `Tc()` | 190-204 | Critical temperature |
| `Pc()` | 208-222 | Critical pressure |

## ChemicalInfo (lines 23-60) -- RETAIN

Singleton registry for chemical properties via PubChem. No XML/config deps.

| Member | Action |
|--------|--------|
| `instance` (class var) | RETAIN |
| `__init__()` | RETAIN -- depends on `Stream.non_hydrocarbon_gases`, `Stream.pubchem_cid_df` |
| `get_instance()` | RETAIN |
| `chemical()` | RETAIN |
| `mol_weight()` | RETAIN |
| `mol_weights()` | RETAIN |
| `names()` | RETAIN |

**Modification**: Remove `OpgeeObject` base class (provides only a no-op `clear()` classmethod).

## Air (lines 225-253) -- RETAIN

| Member | Action | Notes |
|--------|--------|-------|
| `__init__(field, composition)` | MODIFY | Currently stores `self.field` but never uses it after init. Accept explicit composition params instead of `field`. |
| `density()` | RETAIN | |

**Modification**: Remove `OpgeeObject` base; decouple from `field` -- accept composition directly or take only what's needed.

## WetAir (lines 257-272) -- DROP

Marked "Deprecated? Currently unused" in source.

## DryAir (lines 275-297) -- RETAIN

| Member | Action | Notes |
|--------|--------|-------|
| `__init__(field)` | MODIFY | Only uses `field` to pass to `Air.__init__` which stores but never reads it. Remove `field` param. |

## AbstractSubstance (lines 300-342) -- RETAIN with modifications

Base class for Oil, Gas, Water. Core pre-computed property tables.

| Member | Action | Notes |
|--------|--------|-------|
| `__init__(field)` | MODIFY | See below |
| `self.res_tp` | RETAIN | Needs `field.attr("res_temp")`, `field.attr("res_press")` -- accept as explicit args |
| `self.model` | DROP | Only used for `self.model.const()` in Gas and Water (3 call sites) |
| `self.dry_air` | RETAIN | Remove field param from DryAir |
| `self.component_MW` | RETAIN | |
| `self.component_LHV_molar` | RETAIN | |
| `self.component_LHV_mass` | RETAIN | |
| `self.component_HHV_molar` | RETAIN | |
| `self.component_HHV_mass` | RETAIN | |
| `self.component_Cp_STP` | RETAIN | |
| `self.component_Tc` | RETAIN | |
| `self.component_Pc` | RETAIN | |
| `self.component_gas_rho_STP` | MODIFY | Uses `field.stp.T/P` -- pass STP directly |
| `self.steam_table` | RETAIN | |

**Modifications**:
1. Remove `OpgeeObject` base class.
2. Replace `field` param with explicit values: `res_temp`, `res_press`, `stp` (or use module-level `STP`).
3. Eliminate `self.model` -- the 3 `model.const()` calls must be replaced:
   - `"universal-gas-constants"` (Gas.ratio_of_specific_heat, line 875) -- import `R_GAS` from new `opgee/chemistry.py` module.
   - `"std-temperature"` / `"std-pressure"` (Water.density defaults, lines 1254-1255) -- use `STP.T` / `STP.P`.

## Oil (lines 345-748) -- RETAIN all methods

| Member | Action | Notes |
|--------|--------|-------|
| `pbub_a1/a2/a3` (class constants) | RETAIN | |
| `__init__(field)` | MODIFY | Replace `field.attr()` / `field.attrs_with_prefix()` with explicit params: `API`, `gas_comp`, `GOR`, `res_temp`, `res_press` |
| `_gas_specific_gravity()` | RETAIN | |
| `bubble_point_solution_GOR()` (static) | RETAIN | |
| `specific_gravity()` (static) | RETAIN | |
| `API_from_SG()` (static) | RETAIN | |
| `reservoir_solution_GOR()` | RETAIN | TODO says "used only in tests" but keep for coverage |
| `bubble_point_pressure()` | RETAIN | |
| `solution_gas_oil_ratio()` | RETAIN | |
| `saturated_formation_volume_factor()` | RETAIN | |
| `unsat_formation_volume_factor()` | RETAIN | Creates `Stream("test_stream", ...)` internally -- acceptable |
| `isothermal_compressibility_X()` | RETAIN | TODO: "used only in tests" |
| `isothermal_compressibility()` (static) | RETAIN | |
| `formation_volume_factor()` | RETAIN | |
| `density()` | RETAIN | |
| `volume_flow_rate()` | RETAIN | |
| `mass_energy_density()` (static-like) | RETAIN | |
| `volume_energy_density()` | RETAIN | |
| `energy_flow_rate()` | RETAIN | |
| `specific_heat()` (static) | RETAIN | |
| `liquid_fuel_composition()` (static) | RETAIN | |

## Gas (lines 751-1229) -- RETAIN all methods

| Member | Action | Notes |
|--------|--------|-------|
| `__init__(field)` | MODIFY | Decouple from field (same as AbstractSubstance) |
| `total_molar_flow_rate()` | RETAIN | |
| `molar_flow_rate()` | RETAIN | |
| `molar_flow_rates()` | RETAIN | |
| `component_molar_fraction()` | RETAIN | |
| `component_molar_fractions()` | RETAIN | |
| `component_mass_fractions()` | RETAIN | |
| `specific_gravity()` | RETAIN | |
| `ratio_of_specific_heat()` | MODIFY | Replace `self.model.const("universal-gas-constants")` with constant value |
| `heat_capacity()` (static) | RETAIN | |
| `uncorrected_pseudocritical_temperature_and_pressure()` | RETAIN | |
| `corrected_pseudocritical_temperature()` | RETAIN | |
| `corrected_pseudocritical_pressure()` | RETAIN | |
| `reduced_temperature()` | RETAIN | |
| `reduced_pressure()` | RETAIN | |
| `Z_factor()` (static) | RETAIN | Redlich-Kwong EOS |
| `volume_factor()` | RETAIN | |
| `density()` | RETAIN | |
| `viscosity()` | RETAIN | |
| `molar_weight_from_molar_fracs()` | RETAIN | |
| `molar_weight()` | RETAIN | |
| `volume_flow_rate()` | RETAIN | |
| `volume_flow_rate_STP()` | RETAIN | |
| `volume_flow_rates_STP()` | RETAIN | |
| `mass_energy_density()` | RETAIN | |
| `mass_energy_density_from_molar_fracs()` | RETAIN | |
| `combustion_enthalpy()` (static) | RETAIN | |
| `volume_energy_density()` | RETAIN | |
| `energy_flow_rate()` | RETAIN | |

## Water (lines 1232-1359) -- RETAIN all methods

| Member | Action | Notes |
|--------|--------|-------|
| `steam_tbl_digits` (class var) | RETAIN | |
| `__init__(field)` | MODIFY | Replace `field.attr("total_dissolved_solids")` with explicit param |
| `density()` | MODIFY | Replace `self.model.const("std-temperature"/"std-pressure")` defaults with `STP.T`/`STP.P` |
| `volume_flow_rate()` | RETAIN | |
| `specific_heat()` (static) | RETAIN | |
| `heat_capacity()` (classmethod) | RETAIN | |
| `saturated_temperature()` (static) | RETAIN | |
| `enthalpy_PT()` | RETAIN | |
| `steam_enthalpy()` | RETAIN | |

## Summary

| Category | Count |
|----------|-------|
| RETAIN (as-is) | ~50 methods/functions |
| RETAIN + MODIFY | ~8 (constructor signatures, `model.const` removal) |
| DROP | 1 class (`WetAir`) |

### Key Refactoring Actions

1. **Remove `OpgeeObject` base** from all classes (ChemicalInfo, Air, DryAir, AbstractSubstance, Oil, Gas, Water). It provides nothing (empty `clear()` classmethod).
2. **Decouple constructors from `field`** -- accept explicit typed parameters (`res_temp`, `res_press`, `API`, `gas_comp`, `GOR`, `TDS`, `stp`) instead of reaching into `field.attr()`.
3. **Eliminate `self.model`** reference (3 usages):
   - `model.const("universal-gas-constants")` -> inline `ureg.Quantity(8.31446, "J/mol/K")`
   - `model.const("std-temperature")` -> `STP.T`
   - `model.const("std-pressure")` -> `STP.P`
4. **Drop `WetAir`** -- deprecated/unused.
5. **No XML, no config, no plugin dependencies exist** in this file -- removal is straightforward.
