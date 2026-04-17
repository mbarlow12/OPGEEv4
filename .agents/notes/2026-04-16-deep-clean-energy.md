# Deep Clean Proposal: `opgee/energy.py`

**Date**: 2026-04-16
**Branch**: refactor/v5-deep-clean
**Goal**: Strip to minimal pure-library package; no XML, no CLI, no config system.

---

## Current Structure

### Imports
- `pandas` (pd)
- `.units.ureg`
- `.core.OpgeeObject`
- `.error.OpgeeException`
- `.log.getLogger`

### Module-level Variables / Constants
| Symbol | Type | Line |
|---|---|---|
| `_logger` | Logger instance | 16 |
| `EN_NATURAL_GAS` | str constant | 19 |
| `EN_UPG_PROC_GAS` | str constant | 20 |
| `EN_NGL` | str constant | 21 |
| `EN_CRUDE_OIL` | str constant | 22 |
| `EN_DIESEL` | str constant | 23 |
| `EN_RESID` | str constant | 24 |
| `EN_PETCOKE` | str constant | 25 |
| `EN_ELECTRICITY` | str constant | 26 |

### Class: `Energy(OpgeeObject)`

| Member | Kind | Line |
|---|---|---|
| `carriers` | class var (list) | 39 |
| `_carrier_set` | class var (set) | 42 |
| `_units` | class var (pint.Unit) | 44 |
| `create_energy_series()` | classmethod | 47 |
| `__init__(self)` | instance method | 55 |
| `units()` | classmethod | 59 |
| `rates(self)` | method | 62 |
| `get_rate(self, carrier)` | method | 70 |
| `set_rate(self, carrier, rate)` | method | 84 |
| `set_rates(self, dictionary)` | method | 99 |
| `add_rate(self, carrier, rate)` | method | 109 |
| `add_rates(self, dictionary)` | method | 124 |
| `add_rates_from(self, energy)` | method | 134 |
| `reset(self)` | method | 143 |

---

## RETAIN

These are core data-tracking functionality with no XML/config dependencies.

| Symbol | Rationale |
|---|---|
| `EN_NATURAL_GAS` | Energy carrier constant, used throughout processes |
| `EN_UPG_PROC_GAS` | Energy carrier constant |
| `EN_NGL` | Energy carrier constant |
| `EN_CRUDE_OIL` | Energy carrier constant |
| `EN_DIESEL` | Energy carrier constant |
| `EN_RESID` | Energy carrier constant |
| `EN_PETCOKE` | Energy carrier constant |
| `EN_ELECTRICITY` | Energy carrier constant |
| `Energy` (class) | Core data wrapper for energy-by-carrier tracking |
| `Energy.carriers` | Defines the set of tracked energy carriers |
| `Energy._carrier_set` | Fast membership test |
| `Energy._units` | Unit definition for energy rates |
| `Energy.create_energy_series()` | Factory for zero-filled pandas Series |
| `Energy.__init__()` | Constructor |
| `Energy.units()` | Unit accessor |
| `Energy.rates()` | Returns the underlying Series |
| `Energy.get_rate()` | Getter for single carrier rate |
| `Energy.set_rate()` | Setter for single carrier rate |
| `Energy.set_rates()` | Batch setter from dict |
| `Energy.add_rate()` | Accumulate single carrier rate |
| `Energy.add_rates()` | Batch accumulate from dict |
| `Energy.add_rates_from()` | Accumulate from another Energy instance |
| `Energy.reset()` | Zero out all rates |

## DROP

| Symbol | Rationale |
|---|---|
| `from .core import OpgeeObject` | `OpgeeObject` is a near-empty base class (only provides a no-op `clear()` classmethod). Remove the import and the inheritance; `Energy` can be a plain class. |
| `_logger` / `from .log import getLogger` | Logger is imported but never used in this module. Dead code. |

## UNCERTAIN

*None.* This file is clean and self-contained. Every functional symbol is part of the core energy-tracking API.

---

## Recommended Changes

1. **Drop `OpgeeObject` inheritance**: Change `class Energy(OpgeeObject):` to `class Energy:`. The only thing `OpgeeObject` provides is a no-op `clear()` classmethod, which `Energy` does not use or override.
2. **Remove dead logger import**: Delete `from .log import getLogger` and `_logger = getLogger(__name__)`.
3. **Keep `from .units import ureg`**: `ureg` is used for the pint unit registry; this is a core dependency.
4. **Keep `from .error import OpgeeException`**: Used for carrier validation. Consider whether this should migrate to a stdlib `ValueError` in the v5 clean, but functionally it is fine to retain.
5. **No other changes needed**. This module is already clean, purely data-oriented, and free of XML/config/CLI concerns.
