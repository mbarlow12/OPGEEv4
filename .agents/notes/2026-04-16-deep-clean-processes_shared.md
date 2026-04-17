# Deep Clean Analysis: `opgee/processes/shared.py`

## Overview

Shared constants, lookup dictionaries, and helper functions used across the 51 process implementations. This is a small, focused utility module (151 lines). It imports from `opgee.units`, `opgee.energy`, `opgee.error`, and `opgee.stream`.

---

## Consumers

Imported by 25 process modules and 1 test file (`tests/test_shared.py`). This is a heavily-used foundation module.

---

## Symbol Inventory

### Module-level Constants / Dictionaries

| Symbol | Type | Description |
|---|---|---|
| `_slope` | `dict` | Heat-rate regression slopes for NG_engine/NG_turbine |
| `_intercept` | `dict` | Heat-rate regression intercepts for NG_engine/NG_turbine |
| `_maxBHP` | `dict` | Max brake horsepower caps per prime-mover type |

### Functions

| Symbol | Signature | Consumers |
|---|---|---|
| `get_efficiency` | `(prime_mover_type, brake_horsepower) -> Quantity` | Called by `get_energy_consumption`, `get_energy_consumption_stages` |
| `get_init_lifting_stream` | `(gas, lifting_gas_stream, gas_lifting_vol_rate) -> Stream` | `gas_partition.py` |
| `predict_blower_energy_use` | `(proc, thermal_load, ...) -> Quantity` | `acid_gas_removal.py`, `demethanizer.py`, `gas_dehydration.py` |
| `get_energy_carrier` | `(prime_mover_type) -> str` | 20 process modules |
| `get_energy_consumption_stages` | `(prime_mover_type, brake_horsepower_of_stages) -> list` | `separation.py`, `downhole_pump.py` |
| `get_energy_consumption` | `(prime_mover_type, brake_horsepower) -> Quantity` | `acid_gas_removal.py`, `water_injection.py`, `steam_generation.py`, `compressor.py`, `LNG_regasification.py` |
| `get_bounded_value` | `(value, name, variable_bound_dict) -> float` | `acid_gas_removal.py`, `demethanizer.py`, `gas_dehydration.py` |

---

## Retain

All domain-pure engineering calculations and constants. No XML/config/CLI dependency.

### Constants

- **`_slope`** -- Empirical regression coefficients for prime-mover heat rates. Pure domain data.
- **`_intercept`** -- Empirical regression coefficients for prime-mover heat rates. Pure domain data.
- **`_maxBHP`** -- Engineering caps on brake horsepower per prime-mover type. Pure domain data.

### Functions

- **`get_efficiency(prime_mover_type, brake_horsepower)`** -- Pure engineering calculation. Returns heat rate (btu/hp/hr) from empirical correlations. Depends only on `ureg` and the module-level dicts. No infrastructure coupling.

- **`get_init_lifting_stream(gas, lifting_gas_stream, gas_lifting_vol_rate)`** -- Constructs a gas-lifting Stream from thermodynamic properties. Depends on `Stream` and `PHASE_GAS` from `opgee.stream`, plus the `Gas` domain object. Pure domain logic, no XML/config.

- **`get_energy_carrier(prime_mover_type)`** -- Maps prime-mover type string to energy carrier constant (`EN_NATURAL_GAS`, etc.). Used by 20 processes. Pure string-to-constant mapping with no infrastructure dependency.

- **`get_energy_consumption_stages(prime_mover_type, brake_horsepower_of_stages)`** -- Iterates over compressor stages, computing energy consumption per stage via `get_efficiency`. Pure domain calculation.

- **`get_energy_consumption(prime_mover_type, brake_horsepower)`** -- Single-stage version of the above. Pure domain calculation.

- **`get_bounded_value(value, name, variable_bound_dict)`** -- Generic numeric clamping utility. The bounds dict is passed in by the caller; the function itself is pure. No infrastructure dependency.

---

## Retain with Refactoring

- **`predict_blower_energy_use(proc, thermal_load, ...)`** -- The calculation itself is pure engineering (blower sizing from thermal load). However, its current signature couples it to the process object graph in two ways:
  1. It reads default parameter values from `proc.air_cooler_delta_T`, `proc.water_press`, `proc.air_cooler_fan_eff`, `proc.air_cooler_speed_reducer_eff` -- these are XML-attribute-derived instance variables set via `self.attr(...)` in each calling process.
  2. It accesses `proc.field.model.const("air-elevation-corr")` and `proc.field.model.const("air-density-ratio")` -- physical constants looked up from `tables/constants.csv` through the Model object.

  **Proposed refactoring**: Make all parameters explicit (no `proc` argument). Callers would pass the four air-cooler parameters and the two physical constants directly. This eliminates the hidden `proc -> field -> model -> const()` traversal and the attribute-system dependency.

  Refactored signature:
  ```python
  def predict_blower_energy_use(
      thermal_load,
      air_cooler_delta_T,
      water_press,
      air_cooler_fan_eff,
      air_cooler_speed_reducer_eff,
      air_elevation_corr,
      air_density_ratio,
  ):
  ```

---

## Drop

**Nothing to drop.** Every symbol in this file is a domain-relevant engineering calculation or constant. There are no XML parsers, no config readers, no CLI artifacts, no attribute-system definitions, and no logging infrastructure in this module.

---

## Uncertain

**None.** The file is cleanly domain-focused. The only action item is the signature refactoring of `predict_blower_energy_use` described above.

---

## Import Dependencies

| Import | Status |
|---|---|
| `opgee.units.ureg` | RETAIN -- core unit system |
| `opgee.energy.EN_NATURAL_GAS, EN_ELECTRICITY, EN_DIESEL, EN_RESID` | RETAIN -- energy carrier constants |
| `opgee.error.OpgeeException` | RETAIN -- domain error type |
| `opgee.stream.Stream, PHASE_GAS` | RETAIN -- core domain classes |

All four imports are from modules that will survive the deep clean.

---

## Summary

This is one of the cleanest modules in the codebase. All 7 functions and 3 constant dicts are pure domain logic. The single refactoring action is to decouple `predict_blower_energy_use` from the `proc` object graph by making its six implicit parameters explicit.
