# Deep Clean Proposal: `opgee/emissions.py`

**Date**: 2026-04-16
**Branch**: refactor/v5-deep-clean
**Goal**: Strip to minimal pure-library package; no XML, no CLI, no config system.

---

## Current Structure

### Imports
- `pandas` (pd)
- `pint`
- `.units.magnitude`, `.units.ureg`
- `.core.OpgeeObject`
- `.error.OpgeeException`
- `.stream.Stream`

### Module-level Constants
| Symbol | Type | Line |
|---|---|---|
| `EM_COMBUSTION` | str constant | 17 |
| `EM_LAND_USE` | str constant | 18 |
| `EM_VENTING` | str constant | 19 |
| `EM_FLARING` | str constant | 20 |
| `EM_FUGITIVES` | str constant | 21 |
| `EM_OTHER` | str constant | 22 |
| `EM_VOC` | str constant | 24 |
| `EM_CO` | str constant | 25 |
| `EM_CH4` | str constant | 26 |
| `EM_C1` | str constant | 27 |
| `EM_N2O` | str constant | 28 |
| `EM_CO2` | str constant | 29 |
| `EM_GHG` | str constant | 30 |

### Class: `EmissionsError(OpgeeException)`

| Member | Kind | Line |
|---|---|---|
| `__init__(self, func_name, category, gas)` | method | 33 |
| `__str__(self)` | method | 38 |

### Class: `Emissions(OpgeeObject)`

| Member | Kind | Line |
|---|---|---|
| `emissions` | class var (list) | 55 |
| `indices` | class var (list) | 57 |
| `_emissions_set` | class var (set) | 60 |
| `categories` | class var (list) | 62 |
| `_categories_set` | class var (set) | 63 |
| `_units` | class var (pint.Unit) | 65 |
| `create_emissions_matrix()` | classmethod | 68 |
| `__init__(self)` | instance method | 76 |
| `units()` | classmethod | 80 |
| `reset(self)` | method | 83 |
| `rates(self, gwp=None)` | method | 89 |
| `compute_GHG(self, gwp)` | method | 105 |
| `reset_GHG(self)` | method | 116 |
| `_check_loc(self, func_name, gas, category)` | method | 124 |
| `set_rate(self, category, gas, rate)` | method | 128 |
| `set_rates(self, category, **kwargs)` | method | 141 |
| `add_rate(self, category, gas, rate)` | method | 153 |
| `add_rates(self, category, **kwargs)` | method | 166 |
| `add_from_stream(self, category, stream)` | method | 179 |
| `set_from_stream(self, category, stream)` | method | 197 |
| `add_from_series(self, category, series)` | method | 215 |
| `set_from_series(self, category, series)` | method | 234 |
| `add_rates_from(self, emissions)` | method | 253 |

---

## RETAIN

These are core emissions tracking functionality.

| Symbol | Rationale |
|---|---|
| `EM_COMBUSTION` | Emission category constant, used by processes |
| `EM_LAND_USE` | Emission category constant |
| `EM_VENTING` | Emission category constant |
| `EM_FLARING` | Emission category constant |
| `EM_FUGITIVES` | Emission category constant |
| `EM_OTHER` | Emission category constant |
| `EM_VOC` | Gas species constant |
| `EM_CO` | Gas species constant |
| `EM_CH4` | Gas species constant |
| `EM_C1` | Alias for CH4 in stream contexts |
| `EM_N2O` | Gas species constant |
| `EM_CO2` | Gas species constant |
| `EM_GHG` | Aggregated GHG row label |
| `EmissionsError` | Custom error class for emission operations (retain but re-base from `OpgeeException` to `ValueError` or keep as-is) |
| `Emissions` (class) | Core emissions-by-source DataFrame wrapper |
| `Emissions.emissions` | List of tracked gas species |
| `Emissions.indices` | Species list + GHG aggregate |
| `Emissions._emissions_set` | Fast membership test |
| `Emissions.categories` | List of emission categories |
| `Emissions._categories_set` | Fast membership test |
| `Emissions._units` | Unit definition |
| `Emissions.create_emissions_matrix()` | Factory for zero-filled DataFrame |
| `Emissions.__init__()` | Constructor |
| `Emissions.units()` | Unit accessor |
| `Emissions.reset()` | Zero out all rates |
| `Emissions.rates(gwp=None)` | Return DataFrame, optionally computing GHG row |
| `Emissions.compute_GHG(gwp)` | Compute CO2-eq using GWP series |
| `Emissions.reset_GHG()` | Zero the GHG row |
| `Emissions._check_loc()` | Validation helper |
| `Emissions.set_rate()` | Set single (category, gas) rate |
| `Emissions.set_rates()` | Batch set from kwargs |
| `Emissions.add_rate()` | Accumulate single (category, gas) rate |
| `Emissions.add_rates()` | Batch accumulate from kwargs |
| `Emissions.add_from_stream()` | Add emission rates extracted from a Stream |
| `Emissions.set_from_stream()` | Set emission rates extracted from a Stream |
| `Emissions.add_from_series()` | Add emission rates from a pandas Series |
| `Emissions.set_from_series()` | Set emission rates from a pandas Series |
| `Emissions.add_rates_from()` | Accumulate from another Emissions instance |

## DROP

| Symbol | Rationale |
|---|---|
| `from .core import OpgeeObject` | `OpgeeObject` provides only a no-op `clear()` classmethod. Remove inheritance; `Emissions` can be a plain class. |

## FINALIZED UNCERTAIN → `opgee/chemistry.py`

| Symbol | Decision |
|---|---|
| `from .stream import Stream` (for `Stream.VOCs`) | **Move VOC names to new `opgee/chemistry.py` module.** Component chemistry data (VOC species list, component names, phase constants, carbon numbers) and physical constants (R_GAS) will live in `chemistry.py`. Both `stream.py` and `emissions.py` import from there. Breaks the coupling. |

---

## Recommended Changes

1. **Drop `OpgeeObject` inheritance**: Change `class Emissions(OpgeeObject):` to `class Emissions:`.
2. **GWP integration**: The refactoring context notes that GWP will be pushed to emissions or Field methods. `compute_GHG(gwp)` already accepts a `gwp` Series as a parameter -- this is the right shape. No structural change needed; just ensure callers pass GWP directly rather than obtaining it from `Analysis`.
3. **Decouple from `Stream` class variable**: The `Stream.VOCs` reference in `add_from_series()` (line 231) and `set_from_series()` (line 250) could be replaced by a local constant or a shared constants module. This would remove the `from .stream import Stream` import entirely.
4. **`EmissionsError` base class**: Currently extends `OpgeeException`. If `OpgeeException` is retained as a base exception, keep as-is. Otherwise, re-base on `ValueError`.
5. **Keep `from .units import magnitude, ureg`**: Both are used -- `ureg` for unit definition, `magnitude` for stripping pint quantities in `set_rate`/`add_rate`.
