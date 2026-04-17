# Deep Clean: process.py

## Summary

1093 lines. Contains the `Process` base class (core of the LCA system), plus `Boundary`, `Reservoir`, `IntermediateValues`, module-level subclass registry functions, and `run_corr_eqns`. Heavy entanglement with XML/config/attribute system in `__init__` and `from_xml`, but the runtime API (streams, energy, emissions, iteration) is heavily used across all 51 process subclasses.

---

## Module-Level Symbols

### Drop

- `_logger` — Replace with standard logging if needed; the `opgee.log.getLogger` wrapper is being dropped
- `get_subclasses(cls)` — XML subclass discovery mechanism; not needed when processes are explicitly registered
- `_subclass_dict(superclass)` — Builds class registry from `__subclasses__()` with config-dependent `AllowProcessRedefinition`; XML/config machinery
- `_Subclass_dict` — Cache for above
- `decache_subclasses()` — Used only in `field.py` cleanup; drops with registry
- `_get_subclass(cls, subclass_name, reload)` — Used only in `from_xml`; drops with XML instantiation
- `reload_subclass_dict()` — Used only in `model_file.py` and `_get_subclass`; drops with XML instantiation

### Retain (modify)

- `run_corr_eqns(x1, x2, x3, x4, x5, coef_df)` — Pure math function, used by `acid_gas_removal`, `demethanizer`, `gas_dehydration`. Keep as-is; consider moving to a `math_utils` module

### Uncertain

- `IntermediateValues` — Used only by `water_treatment.py` (via `init_intermediate_results` / `sum_intermediate_results`). Inherits `OpgeeObject`. The class stores named (Energy, Emissions) pairs in a DataFrame for sub-process accounting. Question: is this worth keeping as a general mechanism, or should `water_treatment` just manage its own local state?

---

## Process Class

### Class Variables

#### Retain (modify)

- `INPUT = 'input'` / `OUTPUT = 'output'` — Simple constants used in stream finding; keep
- `iterating_processes = []` — Class-level mutable list tracking processes with iteration values. Heavily used by convergence logic. **Modify**: move to field-level state instead of class variable to avoid global mutable state

#### Drop

- `_required_inputs = []` / `_required_outputs = []` — Stream validation declarations used by `validate_streams`. Part of the XML validation system. Many subclasses override these. See Uncertain section for `validate_streams`

### `__init__`

#### Drop (from current signature / body)

- `attr_dict` parameter and `AttributeMixin.__init__` call — Attribute system being dropped
- `parent` parameter and `XmlInstantiable.__init__` call — Parent references being dropped
- `self.model = self.find_container('Model')` — Parent traversal; model ref will be passed explicitly or removed
- `self.field = field = self.find_container('Field')` — Parent traversal; field ref will be passed explicitly or injected
- `self.gas = field.gas` / `self.oil = field.oil` / `self.water = field.water` — Convenience refs set via parent traversal; processes should receive these explicitly
- `self.attr_defs = AttrDefs.get_instance()` — Attribute system
- `self.check_attr_constraints(self.attr_dict)` — Attribute validation
- `self.boundary = boundary` — Boundary system being rethought (see `Boundary` class)
- `self.process_EF = self.get_process_EF()` — Depends on `self.model.process_EF_df`; needs redesign (see `get_process_EF`)
- `self.impute_start = getBooleanXML(impute_start)` — XML boolean parsing; `impute_start` concept used in field graph traversal. See Uncertain
- `self.cycle_start = getBooleanXML(cycle_start)` — XML boolean parsing; cycle detection used in field graph. See Uncertain

#### Retain (modify)

- `self.name` — Keep; set directly (no XML)
- `self.desc` — Keep; optional description
- `self.run_after = False` — Used in field run loop to defer certain processes; retain if field run logic is retained
- `self.extend = False` — Used in field processing; likely drops with XML `extend` attribute
- `self.inputs = []` / `self.outputs = []` — Core stream connection lists; keep
- `self.energy = Energy()` — Core energy tracking; keep
- `self.emissions = Emissions()` — Core emissions tracking; keep
- `self.import_export = ImportExport()` — Used by ~25+ subclasses for energy import accounting; keep
- `self.intermediate_results = None` — See `IntermediateValues` uncertain entry
- Cycle support ivars (`visit_count`, `iteration_count`, `iteration_value`, `iteration_converged`, `iteration_registered`, `in_cycle`) — All used by the convergence system; retain

### Methods

#### Retain

- `__str__(self)` — Useful repr. Modify: remove `self.enabled` reference (enabled concept dropped)
- `reset(self)` — Resets energy/emissions/iteration between runs. Core lifecycle method
- `add_emission_rate(self, category, gas, rate)` — Pass-through to `self.emissions`; used pervasively
- `add_emission_rates(self, category, **kwargs)` — Same
- `get_emission_rates(self, analysis, procs_to_exclude)` — Returns emission rates with GWP. **Modify**: `analysis.gwp` dependency needs rethinking; GWP could be passed directly
- `compute_emission_combustion(self)` — Pure computation from `self.energy` and `self.process_EF`; used by `set_combustion_emissions`
- `set_combustion_emissions(self)` — Called by 29+ subclasses; keep
- `add_energy_rate(self, carrier, rate)` — Pass-through to `self.energy`; used pervasively
- `add_energy_rates(self, dictionary)` — Same
- `get_energy_rates(self)` — Same
- `get_net_imported_product(self)` — Delegates to `self.import_export`
- `set_import_from_energy(self, energy_use)` — Used by 20+ subclasses. **Modify**: currently accesses `self.field.import_export`; needs field ref rethought
- `set_gas_fugitives(self, stream, loss_rate)` — Used by 15+ subclasses. **Modify**: currently uses `self.field.stp`; needs explicit TP parameter
- `get_compressor_and_well_loss_rate(self, inlet_stream)` — Used by `sour_gas_injection`, `gas_lifting_compressor`, `gas_reinjection_well`, `CO2_injection_well`. **Modify**: accesses `self.field` attributes and `self.name`; field data should be passed in
- `visit(self)` / `visited(self)` — Cycle detection support; simple counter methods; keep
- `_find_streams_by_type(self, direction, stream_type, ...)` — Core stream lookup engine. Keep as-is
- `find_input_streams(self, ...)` / `find_output_streams(self, ...)` — Convenience wrappers; keep
- `find_input_stream(self, ...)` / `find_output_stream(self, ...)` — Single-stream convenience; keep
- `add_output_stream(self, stream)` / `add_input_stream(self, stream)` — Stream connection; keep
- `predecessors(self)` / `successors(self)` — Graph traversal; used by `bfs.py`, `within_boundary`, `beyond_boundary`, and field graph logic; keep
- `set_iteration_value(self, value)` — Core convergence logic; used by 28+ subclasses. **Modify**: accesses `self.model.maximum_change`; that threshold should be passed in or stored locally
- `register_iterating_process(cls, process)` — Class method for convergence; keep but move to field-level
- `check_iterator_convergence(cls)` — Same
- `reset_all_iteration(cls)` — Same (note: currently unused outside process.py itself, but logically part of convergence system)
- `reset_iteration(self)` — Instance-level reset; keep
- `_reset_before_iteration(self)` — Hook for subclass override; no current overrides but pattern is sound; keep
- `run(self, analysis)` — Abstract method; core interface. **Modify**: `analysis` parameter type/content will change
- `run_if_enabled(self, analysis)` — **DROP**. Enabled concept removed. Field calls `process.run()` directly
- `print_running_msg(self)` — Used by all 46 subclasses; keep (could simplify to use standard logging)
- `all_streams_ready(self, input_stream_contents)` — Used by 6 subclasses for cycle-aware readiness checks; keep
- `sum_intermediate_results(self)` — Used by `water_treatment`; keep if `IntermediateValues` is kept
- `init_intermediate_results(self, names)` — Same
- `get_intermediate_results(self)` — Same

#### Drop

- `check_enabled(self)` — Empty method; enabled concept dropped entirely
- `clear_iterating_process_list(cls)` / `clear(cls)` — Class-level clearing; replace with field-level state management
- `set_run_after(self, value)` — Setter for `run_after`; trivial, set directly if needed
- `set_extend(self, extend)` — XML extend attribute setter; drops with XML
- `find_stream(self, name, raiseError)` — Delegates to `self.field.find_stream`; unused by any subclass. Drop (callers can use field directly)
- `get_reservoir(self)` — Delegates to `self.field.reservoir`; unused by any subclass. Drop
- `children(self)` / `run_children(self, **kwargs)` — No-ops on Process; exist only for Aggregator polymorphism. Aggregator is removed
- `impute(self)` — No-op base; only override is in `downhole_pump`. See Uncertain
- `venting_fugitive_rate(self)` — Calls `self.attr('leak_rate')`; depends on attribute system. Used by ~5 subclasses. **Redesign**: the leak_rate value should be an explicit field on the process dataclass
- `get_process_EF(self)` — Looks up emission factors from `self.model.process_EF_df` by name/classname. **Redesign**: EF data should be injected, not looked up from model at init time. The method itself drops; the data provisioning changes
- `from_xml(cls, elt, parent)` — XML instantiation; drops entirely
- `validate(self)` — Orchestrates `validate_streams` + `validate_proc`; part of XML validation chain
- `validate_proc(self)` — Empty hook for subclass validation; XML validation system
- `valdict(pattern, min, max)` — Helper for `_required_inputs/_required_outputs` declarations
- `validate_streams(self)` — Stream connection validation at model load time; drops with XML validation
- `within_boundary(self)` / `beyond_boundary(self)` — Boundary graph traversal; drops if Boundary class is removed (see below)
- `check_balances(self)` — Stub (TODO: implement mass balance check); currently a no-op

#### FINALIZED UNCERTAIN

- `required_inputs(self)` / `required_outputs(self)` — **RETAIN**. Keep for runtime sanity checks. `_required_inputs` / `_required_outputs` class variables also retained.
- `impute(self)` — **MOVE to Field/graph layer**. Graph traversal metadata moves out of Process.
- `cycle_start` / `impute_start` instance vars — **MOVE to Field/graph layer**. All graph ordering metadata (cycle_start, impute_start, run_after) becomes field-level graph data.
- `IntermediateValues` — **RETAIN**. Useful sub-process accounting pattern.

---

## Boundary Class — FINALIZED: DROP

Dropped entirely. Boundaries become graph edge cuts — a set of stream/edge crossings in the process graph. Analyzing metrics/flows/emissions at a boundary is a results concern, to be implemented later from the legacy reference.

---

## Reservoir Class

### Retain (simplify)

`Reservoir` is a minimal Process subclass representing the subsurface resource. Each Field has exactly one. Its `run()` is a no-op (just prints a debug message). It exists primarily as a source node in the process graph (has outputs only).

**Modify**: Keep as a simple sentinel/source node. Remove `parent=parent` from `__init__`. Its role is structural (graph entry point), not computational.

---

## Imports to Drop

- `from .attributes import AttrDefs, AttributeMixin` — Attribute system
- `from .config import getParamAsBoolean` — Config system
- `from .core import XmlInstantiable, elt_name` — XML instantiation (`OpgeeObject` may be retained or replaced)
- `from .utils import getBooleanXML` — XML utility

## Imports to Retain

- `from typing import Union, Optional`
- `import pandas as pd`
- `import pint`
- `from .units import ureg, magnitude`
- `from .combine_streams import combine_streams`
- `from .emissions import Emissions, EM_COMBUSTION`
- `from .energy import EN_ELECTRICITY, Energy`
- `from .error import OpgeeException, AbstractMethodError, OpgeeIterationConverged, ModelValidationError`
- `from .import_export import ImportExport`
- `from .stream import Stream`

---

## Key Refactoring Notes

1. **Base classes**: `Process` currently inherits `(AttributeMixin, XmlInstantiable)`. Both drop. Process becomes a standalone class (or frozen dataclass base). It needs only `name` from XmlInstantiable; `enabled` is dropped (existence = enabled).

2. **Parent references**: `self.field`, `self.model`, `self.gas/oil/water` are all set via parent traversal in `__init__`. These must be provided explicitly (constructor injection or set by field during graph assembly).

3. **`self.attr()` calls**: 145 occurrences across 33 process subclasses. Each `self.attr('x')` call pulls from the XML attribute dict. In the dataclass model, these become direct instance attributes on each subclass.

4. **Class-level mutable state**: `iterating_processes` is a class variable list that accumulates across all Process instances. This is a global state problem. Move to field-level tracking.

5. **`process_EF` initialization**: Currently happens in `__init__` via `self.model.process_EF_df` lookup. This is a data dependency that should be injected or resolved at field setup time, not in the Process constructor.

6. **Estimated post-clean size**: ~450-550 lines (dropping ~50% of current code).
