# OPGEE v5 Deep Clean — Design Specification

**Date**: 2026-04-16
**Branch**: `refactor/v5-deep-clean`
**Status**: Draft — attribute traces complete, pending review

---

## 1. Goal

Strip OPGEE to a minimal pure-library package for running LCA simulations on single oil/gas fields. No XML, no CLI, no MCS, no GUI, no plugins, no settings/config, no process groups/choices, no smart defaults. Users construct and run simulations from Python scripts.

---

## 2. Guiding Principles

- **Pure library**: Classes and functions a user constructs and calls from Python
- **Explicit over implicit**: No parent awareness, no magic attribute lookup, no hidden config
- **Children don't know their parent**: Data flows downward via constructor injection (FieldContext)
- **Frozen dataclasses for immutable config**: ReservoirParams, GWPData, SimulationParams
- **Plain classes for stateful runtime objects**: Process, Stream, Field
- **Typed constructors**: All public classes use explicit typed parameters with `pint.Quantity[float]` generics
- **Existence = enabled**: No enabled/disabled state checks

---

## 3. New Modules

### 3.1 FieldContext

Mutable shared context injected into Process and Stream instances. Composed of frozen sub-parts for immutable data, with a single mutable dict for inter-process communication.

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class GWPData:
    """Immutable global warming potentials."""
    values: pd.Series     # keyed by gas name
    horizon: int          # 20 or 100

@dataclass(frozen=True)
class SimulationParams:
    """Immutable iteration/convergence settings."""
    maximum_iterations: int
    maximum_change: float

@dataclass
class FieldContext:
    """Injected into Process and Stream instances.
    
    Contains ONLY shared infrastructure and mutable state — no physical
    parameters. Physical params (api, gor, res_press, etc.) are passed
    directly to the Process constructors that need them.
    
    Not frozen because process_data is intentionally mutable —
    it's the inter-process communication bulletin board (23+ call sites).
    """
    stp: TemperaturePressure
    tables: TableManager
    gwp: GWPData
    simulation: SimulationParams
    process_data: dict[str, Any] = field(default_factory=dict)
```

### 3.2 chemistry.py

Shared component chemistry data extracted from Stream class-level variables. Breaks the stream-emissions coupling.

```python
# opgee/chemistry.py
"""Component chemistry data and physical constants."""

# Phase constants
PHASE_GAS: str = "gas"
PHASE_LIQUID: str = "liquid"
PHASE_SOLID: str = "solid"

# Component data (extracted from Stream class vars)
COMPONENT_NAMES: list[str] = [...]       # ~30 components
CARBON_NUMBER: dict[str, int] = {...}
VOCS: list[str] = [...]
HYDROCARBONS: list[str] = [...]

# PubChem CID data (loaded at module level from CSV)
PUBCHEM_CIDS: pd.DataFrame = pd.read_csv(...)

# Physical constants
R_GAS: Quantity[float] = ureg.Quantity(8.31446, "J/mol/K")
```

Consumers: `stream.py`, `emissions.py`, `thermodynamics.py`, some process subclasses.

---

## 4. Module Designs

### 4.1 Process (base class)

Plain class, no dataclass, no OpgeeObject. Class-level type annotations for all attributes.

```python
class Process:
    # Config (set at construction)
    name: str
    ctx: FieldContext

    # Runtime state
    emissions: Emissions
    energy: Energy
    import_export: ImportExport
    intermediate_results: IntermediateValues
    input_streams: list[Stream]
    output_streams: list[Stream]

    def __init__(self, name: str, ctx: FieldContext):
        self.name = name
        self.ctx = ctx
        self.emissions = Emissions()
        self.energy = Energy()
        self.import_export = ImportExport()
        self.intermediate_results = IntermediateValues()
        self.input_streams = []
        self.output_streams = []

    def __str__(self) -> str:
        return self.name
```

**Retained methods** (~35): Stream finding, emission/energy rate methods, fugitive methods,
iteration/convergence, intermediate results, visit tracking, reset.

**Dropped methods** (~18): from_xml, validate*, children, run_if_enabled, check_enabled,
set_run_after, set_extend, find_stream, get_reservoir, impute, venting_fugitive_rate,
get_process_EF, within/beyond_boundary, check_balances stub, class-registry functions.

**Moved to Field**: cycle_start, impute_start, run_after, iterating_processes.

**Reservoir**: Regular Process subclass, no special treatment.

### 4.2 Process Subclasses (51 files)

Each subclass declares its own typed attributes as class-level annotations and explicit
constructor parameters. Uses `Quantity[float]` generics for pint quantities.

```python
class Drilling(Process):
    fraction_wells_horizontal: float
    well_depth: Quantity[float]
    num_wells: int

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        fraction_wells_horizontal: float,
        well_depth: Quantity[float],
        num_wells: int,
    ):
        super().__init__(name, ctx)
        self.fraction_wells_horizontal = fraction_wells_horizontal
        self.well_depth = well_depth
        self.num_wells = num_wells

    def run(self) -> None:
        # self.well_depth instead of self.attr("well_depth")
        # self.ctx.process_data["key"] instead of self.field.process_data["key"]
        # self.ctx.tables.get_table("constants") instead of self.model.table_manager...
        ...
```

**Migration pattern** (145 `self.attr()` calls across 33 files):
- `self.attr("name")` → `self.name_attr` (explicit instance variable)
- `self.field` → `self.ctx` (122 references across 43 files)
- `self.field.process_data` → `self.ctx.process_data`
- `self.model.const(...)` → inline constants or `self.ctx.stp`
- `run(analysis)` → `run()` (GWP is on `self.ctx.gwp`)

**Migration order**: Tiered by complexity — simple processes first (few attrs, no self.field calls)
to validate the pattern, then complex ones (steam_generator, exploration, transmission_compressor).

### 4.3 Stream

Plain class. Retains `contents` labels for stream-type matching. Chemistry constants moved
to `chemistry.py`.

```python
class Stream:
    name: str
    ctx: FieldContext
    contents: list[str]
    flow_rates: pd.DataFrame
    temperature: Quantity[float]
    pressure: Quantity[float]
    initial_data: pd.DataFrame | None

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        contents: list[str] | None = None,
        temperature: Quantity[float] | None = None,
        pressure: Quantity[float] | None = None,
        initial_data: pd.DataFrame | None = None,
    ):
        self.name = name
        self.ctx = ctx
        self.contents = contents or []
        self.temperature = temperature or ctx.stp.T
        self.pressure = pressure or ctx.stp.P
        self.initial_data = initial_data
        self.flow_rates = self._create_flow_rates(initial_data)
```

**Retained**: All flow-rate methods (~20), TP manipulation, arithmetic, combustion,
`contains()`, `to_dataframe()`, `reset()`.

**Dropped**: from_xml, children, validate, extend_components, _extensions, has_exogenous_data.

**Renamed**: `xml_data` → `initial_data`.

**Moved to chemistry.py**: PHASE_* constants, component_names, carbon_number, VOCs,
_hydrocarbons, _solids, _liquids, _gases, _other, PubChem CID loading.

### 4.4 Field

Top-level simulation object. Absorbs Model/Analysis responsibilities. Constructs FieldContext
and injects it into processes and streams. Manages process graph via networkx.

```python
class Field:
    name: str
    ctx: FieldContext
    graph: nx.DiGraph
    processes: dict[str, Process]
    streams: dict[str, Stream]

    # Graph scheduling (moved from Process)
    cycle_starts: dict[str, str]
    impute_starts: dict[str, str]
    run_after: dict[str, list[str]]

    # Thermo models
    oil: Oil
    gas: Gas
    water: Water

    # Accumulated results
    total_emissions: Emissions
    total_energy: Energy
    total_import_export: ImportExport

    def __init__(
        self,
        name: str,
        simulation: SimulationParams,
        gwp: GWPData,
        tables: TableManager,
        processes: list[Process],
        streams: list[Stream],
        # Only attributes Field uses in its own methods (~7 total)
        num_prod_wells: int = 0,
        oil_sands_mine: str = "",
        field_production_lifetime: Quantity[float] = ...,
        res_press: Quantity[float] = ...,
        res_temp: Quantity[float] = ...,
        has_grid_mix: bool = False,
    ):
        # Build FieldContext — infrastructure only, no physical params
        self.ctx = FieldContext(
            stp=STP, tables=tables, gwp=gwp, simulation=simulation,
        )
        ...
```

**Retained** (~35 methods): Graph building, run/reset, balance checking,
energy/emission/import-export aggregation, fugitive/loss-matrix methods, inter-process
communication, debug output.

**Dropped** (~25 methods): from_xml, cache_attributes, set_extend, set_modifies,
resolve_process_choices, SmartDefault methods, Boundary methods,
compute_carbon_intensity, energy_and_emissions, check_enabled_processes.

**Key changes**:
- networkx DiGraph replaces bfs.py for topological sort + cycle detection
- `run()` takes no params — GWP on ctx, no analysis/trial_num
- Boundary/CI calculation deferred entirely

### 4.5 Thermodynamics (Oil, Gas, Water, Air)

Explicit typed constructor params, no `field` reference, no OpgeeObject base.

```python
class Oil:
    def __init__(self, api: Quantity[float], gas_comp: pd.Series, gas_sg: float,
                 res_temp: Quantity[float], res_press: Quantity[float],
                 gor: Quantity[float], stp: TemperaturePressure = STP): ...

class Gas:
    def __init__(self, gas_comp: pd.Series, stp: TemperaturePressure = STP): ...

class Water:
    def __init__(self, tds: Quantity[float], stp: TemperaturePressure = STP): ...
```

**Retained**: All ~90 property calculation methods unchanged.
**Dropped**: WetAir class, OpgeeObject base.
**Inlined**: `model.const()` calls → `R_GAS` from chemistry.py, `STP.T`, `STP.P`.

### 4.6 Leaf Modules (mechanical changes)

| Module | Change |
|--------|--------|
| `core.py` | Strip to `OpgeeObject` (name + `__str__` only) + `TemperaturePressure` + `STP` + `dict_from_list`. Drop XmlInstantiable, A, parent hierarchy. |
| `energy.py` | Drop OpgeeObject base + dead logger |
| `emissions.py` | Drop OpgeeObject base. VOCs → chemistry.py |
| `import_export.py` | Drop OpgeeObject base + dead logger |
| `units.py` | Drop Qty alias. `importlib.resources` for units.txt. stdlib logging. |
| `table_manager.py` | Drop OpgeeObject. Absorb pkg_utils. Drop XML table updates. |
| `combine_streams.py` | stdlib logging. Fix header comment. |
| `utils.py` | Strip to ~8 utilities. Rename getBooleanXML → parse_boolean. |
| `error.py` | Drop 8 exceptions (MCS/CLI/config/XML). Keep 8. |
| `processes/shared.py` | Refactor predict_blower_energy_use — explicit params, no `proc` arg. |

---

## 5. Deleted Modules

### Files (bulk removal)

| Category | Files |
|----------|-------|
| CLI | tool.py, main.py, subcommand.py |
| XML | model_file.py, XMLFile.py, xml_utils.py |
| Config | config.py |
| Attributes | attributes.py |
| XML-dependent | smart_defaults.py, audit.py, process_groups.py |
| Orchestration | manager.py, post_processor.py |
| Visualization | graph.py |
| Containers | model.py, analysis.py |
| Logging wrapper | log.py |
| Results container | results.py |
| Graph algorithms | bfs.py |
| Resource utils | pkg_utils.py |
| Misc | constants.py, table_update.py, version.py, version.sh |
| Plugins | built_ins/ (all 9 files) |
| Scripts | bin/ (all 7 files) |
| Config/XML data | etc/ (all except units.txt) |

---

## 6. Execution Plan

### 6.1 Phasing

Seven phases, each ending with a green `pytest` and a tagged commit on `refactor/v5-deep-clean`:

| Phase | Name | Scope |
|-------|------|-------|
| **0** | Bulk delete | Remove excluded files/dirs + their tests |
| **1** | Clean leaves | Strip OpgeeObject/logger from energy, emissions, import_export, error, utils, units, table_manager, combine_streams |
| **2** | New foundations | Create chemistry.py + FieldContext (with frozen sub-parts) + unit tests |
| **3** | Strip core classes | Clean core.py, thermodynamics.py, stream.py — remove XML/parent/enabled |
| **4** | Restructure Process base | New init signature, drop Boundary, move graph metadata to Field |
| **5** | Migrate process subclasses | Tiered by complexity: simple → complex. Typed constructors + new unit tests |
| **6** | Restructure Field | New constructor, FieldContext injection, networkx graph, absorb Model/Analysis data |

### 6.2 Verification Gates

Each phase must pass before advancing:
- `uv run pytest -x -q` passes (on the surviving test subset)
- `uv run ruff check .` passes
- Tagged commit: `git tag phase-N-gate`

### 6.3 Process Subclass Migration Order (Phase 5)

**Tier 1 — Simple** (few attrs, minimal self.field):
Validate the constructor pattern on the easiest cases first.

**Tier 2 — Medium** (moderate attrs and self.field usage):
Apply the validated pattern at scale.

**Tier 3 — Complex** (heavy self.field usage: steam_generator, exploration, transmission_compressor):
Handle the most coupled processes last, with full understanding of the pattern.

Exact tier assignments determined during Phase 4 when the base class is ready.

---

## 7. Test Strategy

### 7.1 Approach

Adapt incrementally. Delete tests for deleted modules. Rewrite construction in surviving tests
to use direct instantiation. Preserve assertion logic (encodes domain knowledge).

### 7.2 Phase-by-Phase

| Phase | Test Changes |
|-------|-------------|
| 0 | Delete ~16 test files for removed modules |
| 1-3 | Adapt leaf module tests, add chemistry.py + FieldContext tests |
| 4-5 | Rewrite process test setup: direct construction instead of XML model load. New unit tests per process with typed args + test FieldContext fixture. |
| 6 | Rewrite Field test construction, keep assertion logic |

### 7.3 Test Fixture

```python
@pytest.fixture
def test_ctx() -> FieldContext:
    """Minimal FieldContext for unit testing.
    
    Contains only infrastructure — no physical params.
    Each process test passes its own physical params directly.
    """
    return FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=default_gwp_series(), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
```

---

## 8. Attribute Routing (resolved)

Trace analysis complete. See `.agents/notes/field-attr-*.md` for full data.

### 8.1 Headline: 85.5% of Field attributes are pure pass-through

Of 69 cached Field attributes, only 7 are used by Field's own logic. The rest exist
solely for process consumption — an artifact of XML coupling.

### 8.2 Attribute Routing Rules

No physical parameters live on FieldContext. ALL physical params are routed to
the constructors of the objects that actually use them.

| Destination | Count | Rule | Examples |
|-------------|-------|------|----------|
| **Field instance** | ~7 | Used by Field's own methods | has_grid_mix, num_prod_wells, oil_sands_mine, field_production_lifetime, res_press, res_temp |
| **Process constructor args** | ~60+ | Used by processes (any count) | api, gor, oil_volume_rate, res_press, AGR_feedin_press, reflux_ratio, well_size |
| **SteamGenerator constructor** | ~40 | Uncached steam config attrs | OTSG/HRSG efficiencies, temperatures, fuel splits |
| **Eliminated** | ~20 | Potentially dead | sync_attr_1/2, country, age, liquids_unloading, etc. |

Note: Widely-shared params (oil_volume_rate used by 10 processes, res_press by 8)
appear as constructor args on each process that needs them. The caller passes them
explicitly — no intermediate bundle or pass-through layer.

### 8.3 Other Routing: model.const() and field.model

`field.model` is accessed by 12 process files, mostly for:
- **Constants** (`model.const(...)`) → inline in `chemistry.py` or process code
- **Data tables** (`model.<table>`) → `ctx.tables.get_table(...)`
- **Specific tables** (fracture_energy, land_use_EF, ryan_holmes) → `ctx.tables`

### 8.4 Other Routing: field.import_export

Accessed by 10 process files. Stays on Field as an accumulated result object.
Processes that need to set imports/exports receive it via FieldContext or method call.

### 8.5 Duplicates to Eliminate

- `GOR` and `gas_oil_ratio` both cache the same attr → keep only `gor`
- `WOR` cached but also accessed via `field.attr("WOR")` → standardize to cached

---

## 9. Open Items

### 9.1 TableManager Access Pattern

TableManager is on FieldContext (`self.ctx.tables`). Verify during implementation that this
is sufficient for all process table access patterns, including the 12 `field.model.<table>`
accesses. Consider singleton if needed.

### 9.2 import_export Routing

10 processes access `field.import_export`. Needs to be reachable — either on FieldContext
or passed to processes that need it. Resolve during Phase 4-5.

### 9.3 Thermo Model Access

Process base currently copies `field.gas/oil/water` to `self.gas/oil/water`. In the new
design, these could live on FieldContext or be injected as process constructor args.
11 processes access `field.gas`, 8 access `field.oil`, 9 access `field.water`.

### 9.4 Deferred Work

- **Boundary / CI calculation**: Graph edge cuts, carbon intensity — not implemented in this refactoring
- **Builder/factory**: Convenience construction from dicts/dataframes/JSON — deferred
- **Results layer**: Structured results extraction — deferred

---

## 10. Reference

Per-module symbol-level proposals: `.agents/notes/2026-04-16-deep-clean-<module>.md`

Field attribute traces:
- `.agents/notes/field-attr-trace-processes.md` — all `field.attr()` calls in process files
- `.agents/notes/field-property-trace-processes.md` — all `field.<property>` accesses in process files
- `.agents/notes/field-attr-internal-vs-passthrough.md` — internal vs. pass-through classification
