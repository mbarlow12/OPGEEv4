# Deep Clean Proposal: `opgee/combine_streams.py`

**Status**: INCLUDED (minimal changes)

## Purpose

Thermodynamically combines multiple `Stream` objects into a single stream by summing
component matrices, computing weighted-average temperature (by specific heat capacity),
and computing combined API gravity from a weighted-average specific gravity.

## Symbol Inventory

### Module-level imports

| Symbol | Source | Verdict | Notes |
|---|---|---|---|
| `pd` | `pandas` | RETAIN | Used for `pd.Series` in temperature/heat calculations |
| `ureg` | `.units` | RETAIN | Used in `mixture_specific_heat_capacity` |
| `STP` | `.core` | RETAIN | Fallback temperature/pressure |
| `TemperaturePressure` | `.core` | RETAIN | Constructing TP for new streams |
| `getLogger` | `.log` | DROP | Replace with stdlib `logging.getLogger(__name__)` |
| `Stream` | `.stream` | RETAIN | Core dependency |
| `Oil, Gas, Water` | `.thermodynamics` | RETAIN | Heat capacity and API calculations |

### Module-level variables

| Symbol | Verdict | Notes |
|---|---|---|
| `_logger` | DROP | Unused; if logging added later, use stdlib `logging.getLogger(__name__)` |

### Functions

| Symbol | Verdict | Notes |
|---|---|---|
| `combine_streams(streams)` | RETAIN | Core function. Called from `field.py`, `process.py`, and 3 process implementations (`downhole_pump`, `gas_partition`, `separation`). Also tested in `test_intermediate_boundary.py`. |
| `mixture_specific_heat_capacity(stream)` | RETAIN | Helper for `combine_streams`. Only used internally within this module. Computes cp_mix as mass-weighted sum of oil/water/gas heat capacities. |

### Nested functions (inside `combine_streams`)

| Symbol | Verdict | Notes |
|---|---|---|
| `calculated_combined_API_using_weighted_average(streams)` | RETAIN | Local helper. Computes combined API via mass-weighted specific gravity average using `Oil.specific_gravity()` and `Oil.API_from_SG()`. |

## Retain

All symbols are retained. This module is a pure-calculation utility with no XML, CLI,
config, or I/O dependencies.

- `combine_streams(streams)` -- core public function
- `mixture_specific_heat_capacity(stream)` -- supporting calculation
- `calculated_combined_API_using_weighted_average(streams)` -- nested helper
- All imports (`pd`, `ureg`, `STP`, `TemperaturePressure`, `getLogger`, `Stream`, `Oil`, `Gas`, `Water`)
- `_logger`

## Drop

Nothing.

## Uncertain

Nothing.

## Refactoring Notes

1. The module header comment says "OPGEE Attribute and related classes" -- this is a copy-paste error and should be corrected to describe stream combination.
2. The `TODO` comment on line 20 (`# TODO: improve this to use temp and press`) can be reviewed for relevance.
3. `_logger` is instantiated but never used in the module. Could be removed for cleanliness or kept as conventional boilerplate.
4. No XML, config, or CLI dependencies exist -- the module is already a clean pure-library component.
