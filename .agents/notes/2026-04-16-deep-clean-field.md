# Deep Clean: field.py

Field becomes the top-level simulation object. No Model/Analysis parent, no XML, no Container hierarchy, no ProcessChoice/ProcessGroup, no SmartDefaults, no config dependencies. Boundary is a graph-edge-cut concept deferred to later; CI calculation also deferred. Existence = enabled (no enabled checks). Processes and Streams receive a `FieldContext` dataclass instead of a back-reference to Field.

---

## Module-Level

### Retain
- `_logger` — switch to `import logging; _logger = logging.getLogger(__name__)`

### Drop
- `total_emissions(proc, gwp)` — free function, only caller is `energy_and_emissions` which is deferred

## Imports

### Drop
- `from .attributes import AttributeMixin`
- `from .config import getParamAsList`
- `from .core import XmlInstantiable, elt_name, instantiate_subelts` — XML hierarchy
- `from .process_groups import ProcessChoice`
- `from .smart_defaults import SmartDefault`
- `from .utils import getBooleanXML, roundup` — `getBooleanXML` is XML-only; `roundup` only used in SmartDefault methods
- `from .bfs import bfs` — replaced by networkx
- `from .log import getLogger` — replaced by stdlib logging
- `from .process import decache_subclasses` — subclass registry dropped

### Retain
- `networkx`, `pint`, `pandas`
- `from .core import dict_from_list, STP, TemperaturePressure`
- `from .units import ureg`
- `from .emissions import Emissions`
- `from .energy import Energy`
- `from .error import ...` — keep relevant exceptions
- `from .import_export import ImportExport`
- `from .process import Process, Reservoir`
- `from .stream import Stream`
- `from .thermodynamics import Oil, Gas, Water`
- `from .combine_streams import combine_streams`
- `from .processes.steam_generator import SteamGenerator` — direct process access
- `from .processes.transport_energy import TransportEnergy` — direct process access

## Class: `Field`

### Drop base classes
- `AttributeMixin` — replaced by plain dict/dataclass attributes
- `XmlInstantiable` — entire hierarchy removed

---

## `Field.__init__` — RETAIN (heavy rewrite)

Current signature: `__init__(self, name, attr_dict=None, parent=None, group_names=None)`

New signature takes explicit parameters. Field attributes are plain instance vars, not XML-backed.

**Drop from constructor:**
- `parent` parameter and `XmlInstantiable.__init__` call
- `AttributeMixin.__init__` call
- `self.model = self.find_container("Model")`
- `self.group_names`, `self.process_choice_dict` — ProcessGroup/Choice removed
- `self.known_boundaries` — config dependency removed
- `self.extend`, `self.modifies` — XML merge features
- `self.enabled` / all enabled-state tracking
- `self.boundary_dict` — Boundary class dropped; boundary concept deferred
- `self.procs_beyond_boundary` — boundary concept deferred
- `self.carbon_intensity` — CI calculation deferred
- Copies from Model: `self.upstream_CI`, `self.grid_mix_EF`, etc. — refactored (see FieldContext / data tables below)

**Retain from constructor (with changes):**
- `self.name`
- `self.stream_dict`, `self.process_dict` — populated via `add_children`
- `self.reservoir`
- `self.energy_output`, `self.total_emissions` — aggregated results
- `self.graph`, `self.cycles` — process graph + cycle detection
- `self.process_data` — bulletin board for inter-process communication (23+ call sites)
- `self.wellhead_tp` — set by DownholePump, read by Separation
- `self.stp = STP`
- `self.component_fugitive_table`, `self.loss_mat_gas_ave_df` — computed at init
- `self.emissions`, `self.energy`, `self.import_export` — tracking objects
- `self.oil`, `self.gas`, `self.water` — thermodynamic objects; constructors refactored to take explicit params
- All ~60 cached field attributes (API, depth, GOR, etc.) — plain instance vars from a dict
- `self.transport_energy`, `self.steam_generator` — direct process references

**New additions:**
- `self.gwp` — pandas Series of GWP values (from former Analysis)
- `self.maximum_iterations` — int (from former Model)
- `self.maximum_change` — convergence threshold (from former Model)
- Data tables (upstream_CI, loss matrices, drill tables, etc.) — owned by Field or accessed via TableManager on FieldContext

## `Field.cache_attributes` — DROP

XML attribute caching layer. Replaced by direct dict-based initialization in `__init__`.

## `Field.add_children` — RETAIN (rewrite)

Keep: Reservoir creation, process_dict/stream_dict population, fugitive table computation, `finalize_process_graph` call.

Drop: `self.adopt(...)`, `self.check_attr_constraints(...)`, `process_choice_dict` parameter, `boundary_dict` population, enabled-state filtering.

New signature accepts lists of Process and Stream objects directly. Creates FieldContext and injects it into each Process/Stream.

## `Field.finalize_process_graph` — RETAIN (simplify)

Keep: `self.graph = self._connect_processes()`, `self.cycles = list(nx.simple_cycles(g))`.

Drop: `SmartDefault.apply_defaults(self)`, `self.cache_attributes()`, `self.resolve_process_choices()`.

## `Field._check_run_after_procs` — RETAIN

Process ordering validation. Remove enabled checks.

## `Field.__str__` — RETAIN

Remove `enabled` from repr.

## `Field._impute` — RETAIN

Stream imputation traversal. Note: `impute_start` metadata moves to Field/graph layer per process.py decisions.

## `Field.run` — RETAIN (simplify)

Current: `run(self, analysis, compute_ci=True, trial_num=None)`
New: `run(self)`

**Drop:**
- `analysis` parameter — Field owns GWP
- `compute_ci` parameter — CI calculation deferred
- `trial_num` parameter — MCS removed
- `self.is_enabled()` guard — existence = enabled
- `self.check_enabled_processes()` — enabled concept dropped
- `boundary_proc = self.boundary_process(analysis)` — boundary deferred
- `self.procs_beyond_boundary = ...` — boundary deferred
- `self.compute_carbon_intensity(analysis)` — deferred
- `procs_to_exclude` in `get_emission_rates` — boundary deferred

**Keep (simplified flow):**
```
self.reset()
self._impute()
self.reset_iteration()
self.run_processes()
self.check_balances()
self.get_energy_rates()
self.get_emission_rates()
```

## `Field.reset` — RETAIN (simplify)

Keep: `reset_streams()`, `reset_processes()`.

Drop: `SmartDefault.decache()`, `decache_subclasses()`.

## `Field.reset_iteration` — RETAIN

No changes needed.

## `Field.reset_processes` — RETAIN

Remove enabled filtering if present.

## `Field.reset_streams` — RETAIN

Remove enabled filtering if present.

## `Field.check_balances` — RETAIN

No changes needed.

## `Field.get_energy_rates` — RETAIN

No changes needed.

## `Field.get_emission_rates` — RETAIN (modify)

Remove `analysis` parameter — use `self.gwp`.
Remove `procs_to_exclude` parameter — boundary deferred; compute for all processes.

## `Field.get_net_imported_product` — RETAIN

No changes needed.

## `Field.get_imported_emissions` — RETAIN

References data tables (upstream_CI, grid_mix_EF, grid_mix_feed) that move to Field ownership.

---

## Boundary-Related — ALL DEFERRED

These methods depend on the Boundary process class and boundary-as-process-node concept. Boundary is being redesigned as graph edge cuts. All deferred to later implementation from legacy reference.

- `Field.boundary_processes`
- `Field.boundary_process`
- `Field.boundary_energy_flow_rate`
- `Field.compute_carbon_intensity`
- `Field.partial_ci_values` — also no external callers (dead code)
- `Field.energy_and_emissions` — only caller is `results.py` (dropped)
- `Field.get_carbon_credit` — dead code (commented out at call site)
- `Field.defined_boundaries` — config wrapper, not needed

---

## Graph & Scheduling — RETAIN

- `Field._is_cycle_member`
- `Field._depends_on_cycle`
- `Field._compute_graph_sections`
- `Field._connect_processes` — core graph construction; remove enabled filtering from edge creation
- `Field.run_processes` — replace `self.model.maximum_iterations` with `self.maximum_iterations`; replace custom `bfs()` with networkx; remove `run_if_enabled` (call `run` directly)

## Lookup — RETAIN

- `Field.find_stream`
- `Field.find_process`
- `Field.find_start_streams`
- `Field.streams` — remove enabled filtering (return all streams)
- `Field.processes` — remove enabled filtering (return all processes)
- `Field.all_processes`

## Inter-Process Communication — RETAIN

- `Field.save_process_data` — 23+ call sites across processes
- `Field.get_process_data` — 23+ call sites

## Fugitives — RETAIN (modify)

- `Field.comp_fugitive_productivity` (static) — pure computation
- `Field.comp_fugitive_loss` (static) — pure computation
- `Field.get_component_fugitive` — replace `self.model.*` with field-owned table references
- `Field.get_completion_and_workover_C1_rate` — same

## Validation — RETAIN (simplify)

- `Field.validate` — drop `self.model.attr("skip_validation")`. Drop boundary cycle check. Keep process validation loop and SOR/steam_flooding consistency check.

## Debug — RETAIN

- `Field.report`
- `Field.dump`
- `Field.print_process_list`

## Enabled-Related — ALL DROP

- `Field.check_enabled_processes` — enabled concept eliminated
- All `is_enabled()` / `enabled` / `set_enabled()` checks throughout

---

## DROP (other)

- `Field.from_xml` (classmethod)
- `Field.set_extend`
- `Field.set_modifies`
- `Field.resolve_process_choices`
- `Field.sum_process_energy` — no callers
- `Field.instances_by_class` — Container introspection
- All 20 `@SmartDefault.register` methods (WOR_default through num_gas_inj_wells_default)

---

## Instance Variables Summary

### Field-Owned Data (retain)
- `name`, `stream_dict`, `process_dict`, `reservoir`
- `energy_output`, `total_emissions`
- `graph`, `cycles`
- `process_data`, `wellhead_tp`, `stp`
- `component_fugitive_table`, `loss_mat_gas_ave_df`
- `emissions`, `energy`, `import_export`
- `oil`, `gas`, `water`
- `transport_energy`, `steam_generator`
- All ~60 field attributes (API, GOR, depth, etc.) — plain dict-sourced instance vars

### Absorbed from Analysis
- `gwp` (pandas Series)

### Absorbed from Model
- `maximum_iterations` (int)
- `maximum_change` (float) — convergence threshold
- Data tables: `upstream_CI`, `grid_mix_EF`, `grid_mix_feed`, `vertical_drill_df`, `horizontal_drill_df`, `imported_gas_comp`, `LNG_temp`, `loss_matrix_gas`, `loss_matrix_oil`, `productivity_gas`, `productivity_oil`, `well_completion_and_workover_C1_rate`

### Drop
- `model` — no Model parent
- `group_names` — ProcessGroup removed
- `process_choice_dict` — ProcessChoice removed
- `known_boundaries` — config dependency removed
- `extend`, `modifies` — XML merge
- `enabled` — existence = enabled
- `boundary_dict` — Boundary class dropped
- `procs_beyond_boundary` — boundary deferred
- `carbon_intensity` — CI deferred

---

## FieldContext Design

Field constructs a `FieldContext` and injects it into Process/Stream instances. This replaces `self.field` back-references.

**Contents (mutable shared context):**
- `stp: TemperaturePressure` — standard conditions
- `table_manager: TableManager` — CSV data access
- `gwp: pd.Series` — GWP values
- `process_data: dict` — **mutable** bulletin board for inter-process communication (23+ call sites). Processes read/write via `ctx.process_data`. This is shared mutable state by design.
- Field attributes that processes commonly need (to be determined during implementation)

Field constructs FieldContext from its owned data and passes it during `add_children`. FieldContext is not frozen — `process_data` is the primary mutable element.

## ModelConfig / Simulation Settings

The user noted that Model mixed simulation settings with data. A lightweight config concept may be useful:
- `maximum_iterations: int`
- `maximum_change: float` (convergence threshold)

This can be a simple dataclass passed to Field's constructor, or just direct constructor parameters. To be finalized during implementation planning.
