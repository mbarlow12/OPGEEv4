# Deep Clean Proposal: `opgee/import_export.py`

**Date**: 2026-04-16
**Branch**: refactor/v5-deep-clean
**Goal**: Strip to minimal pure-library package; no XML, no CLI, no config system.

---

## Current Structure

### Imports
- `pandas` (pd)
- `pint`
- `.core.OpgeeObject`
- `.error.OpgeeException`
- `.energy` (all 8 `EN_*` constants)
- `.log.getLogger`

### Module-level Variables / Constants
| Symbol | Type | Line |
|---|---|---|
| `_logger` | Logger instance | 18 |
| `NATURAL_GAS` | str alias for `EN_NATURAL_GAS` | 20 |
| `UPG_PROC_GAS` | str alias for `EN_UPG_PROC_GAS` | 21 |
| `NGL_LPG` | str alias for `EN_NGL` | 22 |
| `CRUDE_OIL` | str alias for `EN_CRUDE_OIL` | 23 |
| `DIESEL` | str alias for `EN_DIESEL` | 24 |
| `RESID` | str alias for `EN_RESID` | 25 |
| `PETCOKE` | str alias for `EN_PETCOKE` | 26 |
| `ELECTRICITY` | str alias for `EN_ELECTRICITY` | 27 |
| `DILUENT` | str constant | 29 |
| `WATER` | str constant | 30 |
| `N2` | str constant | 31 |
| `H2` | str constant | 32 |
| `CO2_Flooding` | str constant | 33 |

### Class: `ImportExport(OpgeeObject)`

| Member | Kind | Line |
|---|---|---|
| `IMPORT` | class var (str) | 37 |
| `EXPORT` | class var (str) | 38 |
| `NET_IMPORTS` | class var (str) | 39 |
| `unit_dict` | class var (dict) | 41 |
| `imports_set` | class var (set) | 55 |
| `_create_dataframe()` | classmethod | 58 |
| `__init__(self)` | instance method | 71 |
| `set_import_export(self, proc_name, imp_exp, item, value)` | method | 75 |
| `set_import(self, proc_name, item, value)` | method | 104 |
| `set_import_from_energy(self, proc_name, energy_use)` | method | 117 |
| `set_export(self, proc_name, item, value)` | method | 128 |
| `importing_processes(self)` | method | 141 |
| `exporting_processes(self)` | method | 147 |
| `imports_exports(self)` | method | 153 |
| `proc_imports(self, proc_name)` | method | 179 |
| `proc_exports(self, proc_name)` | method | 189 |

---

## RETAIN

These are all core import/export tracking functionality used by Field and Process during simulation.

| Symbol | Rationale |
|---|---|
| `NATURAL_GAS` | Import/export item constant (re-exports energy constant) |
| `UPG_PROC_GAS` | Import/export item constant |
| `NGL_LPG` | Import/export item constant |
| `CRUDE_OIL` | Import/export item constant |
| `DIESEL` | Import/export item constant |
| `RESID` | Import/export item constant |
| `PETCOKE` | Import/export item constant |
| `ELECTRICITY` | Import/export item constant |
| `DILUENT` | Import/export item constant (not in energy carriers) |
| `WATER` | Import/export item constant |
| `N2` | Import/export item constant |
| `H2` | Import/export item constant |
| `CO2_Flooding` | Import/export item constant |
| `ImportExport` (class) | Core data tracker for material/energy imports and exports |
| `ImportExport.IMPORT` | Direction constant |
| `ImportExport.EXPORT` | Direction constant |
| `ImportExport.NET_IMPORTS` | Label constant |
| `ImportExport.unit_dict` | Maps items to their pint units |
| `ImportExport.imports_set` | Fast membership test |
| `ImportExport._create_dataframe()` | Factory for typed DataFrame |
| `ImportExport.__init__()` | Constructor |
| `ImportExport.set_import_export()` | Core setter (handles validation, unit conversion, row creation) |
| `ImportExport.set_import()` | Convenience wrapper |
| `ImportExport.set_import_from_energy()` | Bridge from Energy to ImportExport |
| `ImportExport.set_export()` | Convenience wrapper |
| `ImportExport.importing_processes()` | Query: which processes import |
| `ImportExport.exporting_processes()` | Query: which processes export |
| `ImportExport.imports_exports()` | Summary DataFrame of totals and net |
| `ImportExport.proc_imports()` | Per-process import lookup |
| `ImportExport.proc_exports()` | Per-process export lookup |

## DROP

| Symbol | Rationale |
|---|---|
| `from .core import OpgeeObject` | `OpgeeObject` provides only a no-op `clear()`. Remove inheritance; `ImportExport` can be a plain class. |
| `_logger` / `from .log import getLogger` | Logger is imported but never used in this module. Dead code. |

## UNCERTAIN

*None.* This file is clean and self-contained. Every functional symbol is part of the core import/export tracking API.

---

## Recommended Changes

1. **Drop `OpgeeObject` inheritance**: Change `class ImportExport(OpgeeObject):` to `class ImportExport:`.
2. **Remove dead logger import**: Delete `from .log import getLogger` and `_logger = getLogger(__name__)`.
3. **Keep `from .error import OpgeeException`**: Used for validation in `set_import_export()`. Consider migrating to `ValueError` in v5 clean.
4. **Keep `from .energy import ...`**: The 8 `EN_*` constants are re-aliased as module-level names (`NATURAL_GAS`, `NGL_LPP`, etc.) and used as keys in `unit_dict`. This dependency on `energy.py` is appropriate and clean.
5. **Keep `pint` import**: Used for `isinstance(value, pint.Quantity)` check in `set_import_export()`.
6. **Consider deduplicating aliases**: The module re-aliases all 8 energy constants (e.g., `NATURAL_GAS = EN_NATURAL_GAS`). Downstream code could import directly from `energy.py` instead. However, the aliases also serve as the canonical import/export vocabulary for this module and are referenced by `unit_dict`, so retaining them is defensible. Flag for possible future cleanup.
7. **`imports_exports()` has a local import**: Line 162 does `from .units import ureg` inside a nested function `_sum()`. This should be moved to the top-level imports for clarity (it is already available via `.energy` -> `.units`).
