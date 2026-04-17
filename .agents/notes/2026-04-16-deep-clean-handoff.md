# OPGEE Deep Clean — Hand-Off Document

**Date**: 2026-04-16
**Branch**: `refactor/v5-deep-clean`
**Purpose**: Strip OPGEE to a minimal pure-library package for running LCA simulations on single oil/gas fields. No XML, no CLI, no MCS, no GUI, no plugins, no settings/config, no process groups/choices, no smart defaults.

---

## 1. Guiding Principles

- **Pure library**: Classes & functions a user constructs and calls from a Python script
- **Explicit over implicit**: No parent-awareness, no magic attribute lookup, no hidden config
- **Children don't know their parent**: Data flows downward via constructor injection / FieldContext
- **Frozen dataclasses preferred**: For Field attributes and Process subclass attributes
- **Boundaries are graph edge cuts**: Not process nodes. Results/CI analysis is deferred

---

## 2. File-Level Decisions

### EXCLUDE (delete entirely)

| Category | Files |
|---|---|
| CLI | `tool.py`, `main.py`, `subcommand.py` |
| XML | `model_file.py`, `XMLFile.py`, `xml_utils.py` |
| Config | `config.py` |
| Attribute system | `attributes.py` |
| XML-dependent | `smart_defaults.py`, `audit.py`, `process_groups.py` |
| Orchestration | `manager.py`, `post_processor.py` |
| Visualization | `graph.py` |
| Containers | `model.py`, `analysis.py` |
| Logging wrapper | `log.py` (→ stdlib `logging.getLogger(__name__)`) |
| Results container | `results.py` (→ read state directly) |
| Graph algorithms | `bfs.py` (→ networkx) |
| Resource utils | `pkg_utils.py` (→ inline `importlib.resources`) |
| Misc | `constants.py`, `table_update.py`, `version.py`, `version.sh` |
| Plugins | `built_ins/` (all 9 files) |
| Scripts | `bin/` (all 7 files) |
| Config/XML data | `etc/` (all except `units.txt`) |

### INCLUDE (retain with refactoring)

| File | Key Changes |
|---|---|
| `__init__.py` | Minimal |
| `core.py` | Strip to `OpgeeObject` (name only) + `TemperaturePressure` + `STP` + `dict_from_list`. Drop enabled/parent/adopt/find_container/XmlInstantiable/A |
| `field.py` | Top-level simulation object. Drop Container/XML/SmartDefaults/ProcessChoice. Own boundary (as graph cut) and GWP. Inject FieldContext to children |
| `process.py` | Strip XML. Drop Boundary class. Move graph metadata to Field. Inject FieldContext. Keep IntermediateValues + stream validation |
| `stream.py` | Strip XML. Inject FieldContext instead of self.field. Rename xml_data → initial_data |
| `thermodynamics.py` | Decouple constructors from field object. Inline model.const() values. Drop WetAir. Drop OpgeeObject base |
| `units.py` | Drop Qty alias. Switch to importlib.resources + stdlib logging |
| `energy.py` | Drop OpgeeObject + dead logger |
| `emissions.py` | Drop OpgeeObject. Move VOCs to shared constants |
| `import_export.py` | Drop OpgeeObject + dead logger |
| `combine_streams.py` | Minimal — fix log import + header comment |
| `table_manager.py` | Absorb pkg_utils. Drop OpgeeObject + XML updates. Keep add_table() |
| `utils.py` | Strip to ~8 general utilities. Rename getBooleanXML → parse_boolean |
| `error.py` | Drop 8 exceptions (MCS/CLI/config/XML + custom AttributeError). Keep 8 |
| `etc/units.txt` | Keep as-is |
| `processes/` (51 files) | Each needs self.attr() → explicit attrs, self.field → FieldContext |
| `processes/shared.py` | Refactor predict_blower_energy_use signature |
| `tables/` (35 CSVs) | Keep all as-is |

### NEW (to be created)

| Module/Concept | Purpose |
|---|---|
| `FieldContext` | Mutable shared context (STP, tables, GWP, process_data dict) injected into Process/Stream instead of full Field reference. `process_data` is intentionally mutable shared state for inter-process communication. |
| `opgee/chemistry.py` | Component chemistry data extracted from Stream class-level: VOC names, component names, phase constants (PHASE_GAS etc.), carbon numbers, pubchem data. Also physical constants (R_GAS). Both stream.py and emissions.py import from here. |

---

## 3. Key Architectural Decisions

### 3a. No Parent Awareness, No Enabled State
- `OpgeeObject` has only `name` + `__str__`. No `parent`, `enabled`, `find_container()`, `adopt()`, `set_parent()`, `is_enabled()`, `set_enabled()`
- If an object exists in the field/graph/runtime, it's enabled — no checks needed
- All `is_enabled()` / `check_enabled()` / `run_if_enabled()` guards removed throughout
- Field constructs a `FieldContext` and passes it to Process/Stream instances
- `FieldContext` contains: STP, TableManager, GWP data, process_data dict (mutable), and other shared field-level state
- `process_data` on FieldContext is intentionally mutable — it's the inter-process communication bulletin board (23+ call sites)

### 3a-bis. New `opgee/chemistry.py` Module
- Extracts component chemistry data from Stream class-level: VOC names, component names, phase constants (PHASE_GAS, PHASE_LIQUID, PHASE_SOLID), carbon numbers, pubchem data
- Also houses physical constants like R_GAS (universal gas constant)
- Both `stream.py` and `emissions.py` import from here, breaking the stream→emissions coupling

### 3b. Model/Analysis → Dropped
- `Model` and `Analysis` are eliminated as classes
- Simulation config (max iterations, convergence thresholds) passed directly to `Field`
- GWP data owned by `Field` or passed to emissions methods
- Table data accessed via `TableManager` (on FieldContext)

### 3c. Boundary = Graph Edge Cut
- `Boundary` process class dropped entirely
- "Boundary" is a set of stream/edge crossings in the process graph
- CI calculation and boundary analysis are results concerns — deferred to later implementation
- Field methods related to boundary (compute_carbon_intensity, boundary_process, boundary_energy_flow_rate) deferred

### 3d. Graph Metadata on Field, Not Process
- `cycle_start`, `impute_start`, `run_after`, `impute()` move from Process to Field's graph layer
- Process is pure computation; Field manages execution ordering
- Replace custom `bfs.py` with networkx for cycle detection and topological sort

### 3e. Explicit Attributes (No XML Attribute System)
- `attributes.py`, `attributes.xml`, `AttrDef`, `ClassAttrs`, `A()` — all dropped
- Field/Process attributes become explicit instance variables
- Transition to frozen dataclasses preferred for Field attributes and Process subclass attributes
- ~145 `self.attr()` calls across 33 process subclasses must become direct attribute access
- ~60 cached field attributes populated from plain dict at construction

### 3f. Thermodynamic Class Decoupling
- Oil, Gas, Water, Air constructors accept explicit typed parameters instead of `field` object
- 3 `model.const()` calls replaced with inline constants or STP values
- OpgeeObject base removed from all thermodynamic classes

---

## 4. Migration Scope Summary

| Area | Estimated Effort |
|---|---|
| Delete excluded files | Low — bulk removal |
| Strip XML from core/field/process/stream | Medium — surgical removal of from_xml, Container, attributes |
| Create FieldContext | Medium — new dataclass + injection plumbing |
| Migrate 145 self.attr() calls in 33 processes | High — each subclass needs explicit attribute declarations |
| Decouple thermodynamics constructors | Low-Medium — straightforward parameter extraction |
| Move graph metadata to Field | Medium — restructure execution ordering logic |
| Create shared chemistry constants | Low — extract from Stream class data |
| Drop Boundary, defer CI calculation | Low — removal only, no replacement needed now |
| Replace bfs.py with networkx | Low — direct API substitution |
| Update all logging to stdlib | Low — mechanical find-replace |

---

## 5. Detailed Proposals

Per-module symbol-level analysis is in `.agents/notes/2026-04-16-deep-clean-<module>.md`:

- `core.md` — OpgeeObject + TemperaturePressure retention, parent hierarchy dropped
- `field.md` — 35 methods retained, 27 dropped, boundary deferred
- `process.md` — 34 methods retained, 18 dropped, Boundary class dropped, Reservoir kept
- `stream.md` — ~35 methods retained, 4 dropped (from_xml, children, validate, extend_components)
- `thermodynamics.md` — ~58 methods retained, 1 class dropped (WetAir), constructor refactoring
- `units.md` — 4 symbols retained, 3 dropped (Qty, log, pkg_utils imports)
- `energy.md` — All functional symbols retained, drop OpgeeObject + dead logger
- `emissions.md` — All retained, VOCs move to shared constants
- `import_export.md` — All retained, drop OpgeeObject + dead logger
- `combine_streams.md` — Everything retained
- `table_manager.md` — Core retained, absorb pkg_utils, drop XML updates
- `utils.md` — 8 retained, 11 dropped, rename getBooleanXML
- `error.md` — 8 exceptions retained, 8 dropped (including custom AttributeError)
- `processes_shared.md` — All retained, refactor predict_blower_energy_use signature

---

## 6. Next Steps

1. **Add legacy worktree**: `git worktree add _legacy_main main` for reference
2. **Brainstorm implementation strategy**: Sequencing, test strategy, incremental validation
3. **Plan implementation**: Detailed step-by-step plan with verification checkpoints
4. **Execute in phases**: Delete → Strip → Restructure → Verify
