# Deep Clean: stream.py Symbol Analysis

**File**: `opgee/stream.py` (~747 lines)
**Base classes**: `AttributeMixin`, `XmlInstantiable`
**Post-refactor base**: standalone class (no inheritance needed)

---

## DROP

### Imports
- `from .attributes import AttributeMixin` — XML attribute system
- `from .core import XmlInstantiable, elt_name` — XML instantiation
- `from .utils import getBooleanXML, coercible` — XML parsing helpers
- `from .table_manager import TableManager` — only used for class-level pubchem-cid load (replace with direct CSV read)
- `from .log import getLogger` / `_logger` — replace with stdlib `logging`

### Base Classes (from `__init__`)
- `AttributeMixin.__init__(self)` — self-described no-op
- `XmlInstantiable.__init__(self, name, parent=parent)` — sets `self.name`, `self.parent`, `self.enabled`; inline these three attributes directly

### Methods
| Symbol | Lines | Reason |
|---|---|---|
| `from_xml(cls, elt, parent=None)` | 670-743 | XML instantiation; entire method is XML parsing |
| `children()` | 237-238 | Returns `[]`; XmlInstantiable tree-walk artifact |
| `validate()` | 240-241 | Empty pass; XmlInstantiable protocol artifact |
| `extend_components(cls, names)` | 263-290 | Config-driven component extension via `OPGEE.StreamComponents`; only caller is `model_file.py` |

### Class-Level State (config system)
- `_extensions` (dict) — tracks `extend_components` calls; drops with that method

### Instance Attributes
- `self.has_exogenous_data` — XML-specific flag (only external usage: `field.py:1347` filters streams for XML-sourced data)

---

## RETAIN

### Module-Level Constants & Functions
| Symbol | Lines | Notes |
|---|---|---|
| `PHASE_SOLID`, `PHASE_LIQUID`, `PHASE_GAS` | 27-29 | Widely imported across codebase |
| `_carbon_number_prog`, `_hydrocarbon_prog` | 32-33 | Compiled regexes for hydrocarbon naming |
| `is_carbon_number(name)` | 36-37 | Used in tests, general utility |
| `is_hydrocarbon(name)` | 40-41 | Used in `from_xml` but also general chemistry utility |
| `molecule_to_carbon(molecule)` | 44-55 | Used in tests, thermodynamics; chemistry utility |
| `carbon_to_molecule(c_name)` | 58-69 | Used in tests; inverse of above |

### Class-Level Data (all RETAIN)
| Symbol | Notes |
|---|---|
| `_phases` | Core phase list |
| `_hydrocarbons`, `max_carbon_number` | Hydrocarbon component list from pubchem-cid table |
| `_carbon_number_dict`, `carbon_number` | Carbon number series for combustion calcs |
| `VOCs` | VOC component list |
| `_solids`, `_liquids`, `_gases`, `_other` | Component category lists |
| `non_hydrocarbon_gases` | Alias for `_gases` |
| `combustible_components` | Combined list for combustion |
| `component_names` | Master component list |
| `_units` | `ureg.Unit("tonne/day")` |

**Modification needed**: The `TableManager` call to load `pubchem-cid` at class body level needs to be replaced with a direct `pd.read_csv()` of the table file, or a lightweight loader. The table itself is small and static.

### `__init__` — RETAIN with modifications
Current signature:
```python
def __init__(self, name, tp, parent=None, API=None, comp_matrix=None,
             src_name=None, dst_name=None, contents=None, impute=True)
```
**Changes**:
- Remove `parent` param (was `XmlInstantiable.parent`); inline `self.name = name` directly
- Remove `self.enabled` entirely — existence = enabled. Update `__str__` and any `process.py` checks accordingly
- Rename `self.xml_data` to `self.initial_data` (or similar); the reset-to-initial-state pattern is still useful for iterative solvers
- `self.initial_tp` — keep (supports `reset()`)

### Instance Attributes (RETAIN)
- `self.name` — inline (was from XmlInstantiable)
- ~~`self.enabled`~~ — DROPPED (existence = enabled)
- `self.components` — core DataFrame
- `self.tp` — TemperaturePressure
- `self.initial_tp` — for reset
- `self.src_name`, `self.dst_name` — process endpoint names
- `self.src_proc`, `self.dst_proc` — process object refs (set by Field)
- ~~`self.field`~~ — back-ref DROPPED; replaced by injected `FieldContext`
- `self.API` — oil API gravity
- `self.contents` — stream content tags (used by `process.py` `find_input_stream`/`find_output_stream`)
- `self.impute` — used by Field imputation logic
- `self.initialized` — tracks whether stream has data

### Methods (all RETAIN as-is unless noted)
| Method | Lines | Notes |
|---|---|---|
| `__str__` | 192-193 | Keep |
| `to_dataframe()` | 195-235 | Keep; remove `self.parent.name` ref (field name available via FieldContext or passed as param) |
| `reset()` | 243-256 | Keep; rename `self.xml_data` to `self.initial_data` |
| `units()` (classmethod) | 258-260 | Keep |
| `create_component_matrix()` (classmethod) | 293-304 | Keep |
| `is_initialized()` | 306-307 | Keep |
| `is_uninitialized()` | 309-310 | Keep |
| `has_zero_flow()` | 312-313 | Keep |
| `component_phases(name)` | 315-322 | Keep |
| `flow_rate(name, phase)` | 324-333 | Keep |
| `total_flow_rate()` | 335-341 | Keep |
| `hydrocarbons_rates(phase)` | 343-350 | Keep |
| `hydrocarbon_rate(phase)` | 352-359 | Keep |
| `total_gases_rates()` | 361-366 | Keep |
| `total_gas_rate()` | 368-373 | Keep |
| `set_flow_rate(name, phase, rate)` | 375-389 | Keep |
| `set_API(API)` | 391-394 | Keep |
| `gas_flow_rates(index)` | 399-408 | Keep |
| `gas_flow_rate(name)` | 410-417 | Keep |
| `liquid_flow_rate(name)` | 419-426 | Keep |
| `solid_flow_rate(name)` | 428-435 | Keep |
| `voc_flow_rates()` | 437-438 | Keep |
| `non_zero_flow_rates()` | 440-443 | Keep |
| `set_gas_flow_rate(name, rate)` | 445-449 | Keep |
| `set_liquid_flow_rate(name, rate, tp)` | 451-459 | Keep |
| `set_solid_flow_rate(name, rate, tp)` | 461-469 | Keep |
| `set_rates_from_series(series, phase, upper_bound_stream)` | 471-485 | Keep |
| `multiply_factor_from_series(series, phase)` | 487-498 | Keep |
| `set_tp(tp)` | 500-516 | Keep |
| `copy_flow_rates_from(stream, phase, tp, API)` | 518-541 | Keep |
| `copy_gas_rates_from(stream, tp, API)` | 543-563 | Keep |
| `copy_liquid_rates_from(stream)` | 565-576 | Keep |
| `multiply_flow_rates(factor)` | 578-589 | Keep |
| `add_flow_rate(name, phase, rate)` | 591-600 | Keep |
| `add_flow_rates_from(stream)` | 602-613 | Keep |
| `subtract_rates_from(stream, phase)` | 615-628 | Keep |
| `add_combustion_CO2_from(stream)` | 630-654 | Keep |
| `contains(stream_type, regex)` | 656-667 | Keep (used by `process.py`) |
| `hydrocarbons` (property) | 745-747 | Keep |

---

## UNCERTAIN

| Symbol | Reason |
|---|---|
| `self.parent` | DROPPED. Was set by XmlInstantiable. `to_dataframe()` field name available via FieldContext or passed as param. |
| `tp: TemperaturePressure` (type annotation) | Class-level annotation referencing `TemperaturePressure` from `core.py`. If `TemperaturePressure` moves out of `core.py`, update the import. |
| `pubchem_cid_df`, `mgr`, `table_name`, `idx` | Class-level temporaries used only during class body execution to build `_hydrocarbons` and `carbon_number`. Could be moved to a module-level `_init_components()` function to avoid polluting the class namespace. |
| `VOCs`, `_hydrocarbons`, component lists | Per emissions.md decision, VOC names, component names, phase constants, and carbon number data will be extracted to a new `opgee/chemistry.py` module. Both `stream.py` and `emissions.py` will import from there. |

---

## Summary of Required Changes

1. **Remove base classes**: Drop `AttributeMixin` and `XmlInstantiable` inheritance; inline `self.name` in `__init__`; drop `self.enabled` (existence = enabled)
2. **Delete `from_xml`**: Entire XML parsing method (lines 670-743)
3. **Delete `children`, `validate`, `extend_components`**: Dead/XML-only methods
4. **Replace TableManager**: Load pubchem-cid CSV directly at module level
5. **Rename XML artifacts**: `self.xml_data` -> `self.initial_data`; drop `self.has_exogenous_data`
6. **Fix `to_dataframe`**: Replace `self.parent.name` — field name available via FieldContext or passed as param; `self.field` back-ref dropped
7. **Update imports**: Remove `attributes`, `core.XmlInstantiable`, `core.elt_name`, `utils.getBooleanXML`, `utils.coercible`; keep `core.TemperaturePressure` (or move TP to its own module)
8. **Logging**: Replace `opgee.log.getLogger` with stdlib `logging.getLogger`

**Estimated reduction**: ~100 lines removed (from_xml ~75, extend_components ~30, imports/base-class boilerplate ~15). Net file ~640 lines.
