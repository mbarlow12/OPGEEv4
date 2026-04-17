# OPGEE v5 Deep Clean — Progress Handoff

**Branch:** `refactor/v5-deep-clean`
**Plan:** `.agents/docs/plans/2026-04-16-deep-clean-plan.md`
**Spec:** `.agents/docs/specs/2026-04-16-deep-clean-design.md`
**Execution mode:** `superpowers:subagent-driven-development` — TaskList + dispatched implementer / spec-reviewer / code-quality-reviewer subagents per task.
**Handoff convention:** This single file is overwritten at every phase gate.

---

## 1. Status at this handoff

**Just completed:** Phase 5 in full. All 51 Process subclasses + helper classes migrated to the new `Process(name, ctx)` + `run(self)` constructor shape. `TransportEnergy` and `predict_blower_energy_use` helpers fully refactored to pure-param APIs. `SteamGenerator` helper class decoupled from `Field`. The `phase-5-gate` tag marks the gate commit; the `STOP` tag marks the session-stop / resume point (both land on the same commit — this doc).
**Next resume point:** Task 6.1 — restructure `opgee/field.py` (remove AttributeMixin / XmlInstantiable / from_xml / SmartDefault / Boundary / compute_carbon_intensity; introduce new explicit-param constructor; move bfs → networkx; move graph metadata from Process to Field). **Opus** model recommended for this task.

### What landed since the previous handoff (phase-5-tier-2-complete `4b28c9c`)

| Commit | Subject |
|---|---|
| `c6cc513` | phase 5: migrate Tier 3 singles gas_partition.py + steam_generator.py (closes Task 5.3) |
| `b9a53c0` | phase 5: migrate Tier 3 Batch I (2 files, 30-32 refs) + exploration TransportEnergy rewire |
| `7bf2a46` | phase 5: migrate Tier 3 Batch H (3 files, 24-28 refs) |
| `ea46dfb` | phase 5: migrate Tier 3 Batch G (3 files, 17-22 refs) + heavy_oil_dilution TransportEnergy rewire |
| `bc5bdee` | phase 5: migrate Tier 3 Batch F + refactor predict_blower_energy_use (4 files) |
| `69c2a82` | phase 5: migrate Tier 3 Batch E (3 files, 14-15 refs) |
| `449ca38` | phase 5: migrate Tier 3 Batch D (3 files, 12-13 refs) |

**Count:** 19 Tier 3 files migrated in the session (Batches D–I + 2 singles), plus the atomic `predict_blower_energy_use` refactor (Task 5.4 — rolled into Batch F as an atomic rewire like TransportEnergy before it).

### Helper-class API shapes after Phase 5

**`TransportEnergy`** (in `opgee/processes/transport_energy.py`):
```python
TransportEnergy(residual_oil_LHV, residual_oil_density, ocean_tanker_size)

get_transport_energy_dict(parameter_table, transport_share_fuel,
                          transport_by_mode, LHV_rate, prod_type, denominator)
```
Callers: `crude_oil_transport.py`, `LNG_transport.py`, `petrocoke_transport.py`, `heavy_oil_dilution.py`, `exploration.py`.

**`predict_blower_energy_use`** (in `opgee/processes/shared.py`):
```python
predict_blower_energy_use(thermal_load, air_cooler_delta_T, water_press,
                          air_cooler_fan_eff, air_cooler_speed_reducer_eff,
                          air_elevation_const, air_density_ratio)
```
Callers: `acid_gas_removal.py`, `gas_dehydration.py`, `demethanizer.py`. No more `proc.field.model.const(...)` inside.

**`SteamGenerator`** (in `opgee/processes/steam_generator.py`): NO LONGER a subclass of `OpgeeObject`; plain class. Constructor takes `ctx: FieldContext, gas, oil, water` + ~40 explicit scalar params + 8 pre-built Series/DataFrames. Caller (in Phase 6.1 wiring) will build these from the Field. Ivar typo `self.gas_turbine_tlb` preserved for internal stability.

### Verification at `phase-5-gate` (commit `c6cc513`)

- `find opgee/processes -maxdepth 1 -name "*.py" ! -name "__init__.py" | xargs uv run ruff check` — **All checks passed!**
- Forbidden-symbol grep (`self.field`, `self.attr(`, `self.model.`, `cache_attributes`, `def check_enabled`, `set_enabled\b`, `venting_fugitive_rate\b`, `component_fugitive_table` in live code, `"Quantity[float]"`, `pint.Quantity` annotation, `field.transport_energy`, `field.save_process_data`, `field.get_process_data`, `field.import_export`, `field.stp`, `predict_blower_energy_use(self,`) over `opgee/processes/*.py` — **zero hits in live code** across all 51 files (only occasional references inside docstring/comment text that are historical context, not live code).
- `uv run pytest tests/test_chemistry.py tests/test_context.py tests/test_core.py tests/test_energy.py tests/test_import_export.py tests/test_molecule_names.py tests/test_stream.py tests/test_table_manager.py tests/test_thermofunction.py tests/test_utils.py tests/test_emissions.py -q` — **116 passed, 6 errors** (exact Phase 4 baseline; the 6 errors are the expected `test_gwp*` and `test_use_GWP_error` fixture-blocked tests, scheduled for Phase 6.2).
- Full `uv run pytest` remains **not runnable** — `opgee/field.py` still imports deleted modules (`smart_defaults`, etc.). This is the Phase 6.1 fix.
- `uv run ruff check opgee/processes/__init__.py` — still produces 46 F401 errors (explicit re-exports without `__all__` or alias form). This is **pre-existing** (`phase-4-gate` had 47) and out of scope for Phase 5; Phase 6.3 (final cleanup) should address it via `__all__`.

### Phase 5 deviations / breadcrumbs for future sessions

- **Pre-existing latent bugs preserved faithfully** (not migration regressions):
  - `heavy_oil_dilution.py:72` — `TemperaturePressure(diluent_temp, diluent_temp)` (both args are T; no `diluent_press` param ever existed). Ivar is written but never read.
  - `water_treatment.py` — the `makeup_water_table` selection at line ~161 uses `self.water_treatment_table` when `makeup_water_treatment_tbl` is truthy (rather than using the supplied makeup table). Fall-through fidelity only.
  - `bitumen_mining.py` — `downhole_pump`, `upgrader_type`, `gas_comp`, `mined_bitumen_t`, `mined_bitumen_p` constructor params are stored but never read in `run()`. Dead stores faithfully preserved.
  - `reservoir_well_interface.py` — `oil_volume_rate` param stored but not read.
  - `acid_gas_removal.py` — `mol_frac_CO2 == 0.0` (pint comparison vs. `.m == 0.0` for H2S on the same line). Works but inconsistent.
  - `gas_partition.py:316` (inside `gas_flooding_setup` NG-else branch) — local rebind of `reinjected_gas_stream` to `imported_NG_stream` leaves caller's reinjected_gas_stream untouched, so `ctx.process_data["gas_flooding_stream"]` in that path stores the empty original; only the direct `find_output_stream("gas")` write carries actual data.
  - `steam_generator.py:~98` — `self.OTSG_exhaust_temp_outlet_before_economizer` ivar stored but never read (the pre-built `OTSG_exhaust_temp_series` encodes it).

  All of the above predate the deep-clean and would be out-of-scope cleanup for a future correctness pass.

- **Controller-side fix-ups applied on top of implementer output:** import consolidation (`from ..X import a, b` unification), stdlib-first import reordering in a couple of files (downhole_pump, exploration), dead-code removal (`variables = []` double-init in drilling, orphan `# stream.set` comment in downhole_pump, redundant `set_tp` after `Stream(..., tp=...)` in crude_oil_storage), docstring update for crude_oil_storage loss_rate param, missing class docstring added to heavy_oil_upgrading. Full review loop per batch: spec-compliance reviewer + code-quality reviewer in parallel.

- **Bare `except:` tightened to `except KeyError:`** in four files (ruff E722): bitumen_mining, crude_oil_dewatering, gas_dehydration. Pre-existing; fixed during migration to satisfy the ruff gate.

- **`f`-prefix stripped from f-strings with no placeholders** in a few files (ruff F541): pre-existing lint issues, one-line fixes during migration. Also unused `_water_output` in gas_dehydration (renamed with leading underscore; F841), unused `steam_injection_volume_rate` removed in steam_generation, `# noqa: F841` added to steam_generator's duct_firing else-branch tuple unpacking (preserves original variable-name fidelity).

- **demethanizer.py header comment** said `# CrudeOilTransport class` (copy-paste artifact) — fixed during migration review.

---

## 2. TaskList state

| TaskList ID | Status | Subject |
|---|---|---|
| #1 | ✅ completed | Phase 5.3: Tier 3 — 19 complex processes (batches D–I + 2 single) |
| #2 | ✅ completed | Phase 5.4: Refactor predict_blower_energy_use (atomic, rolled into Batch F commit) |
| #3 | ✅ completed | Phase 5.5: Verification gate — Phase 5 (closed by this commit) |
| #4 | 🔄 pending (next) | **Phase 6.1: Restructure Field class** ← resume here |
| #5 | pending | Phase 6.2: Adapt remaining test files |
| #6 | pending | Phase 6.3: Final cleanup — public API + dependencies |
| #7 | pending | Phase 6.4: Final verification gate |
| #8 | pending | Final code-reviewer dispatch for whole refactor |

(IDs #1–#8 in this table are TaskCreate IDs from the current session.)

---

## 3. Resume point — Task 6.1: Restructure Field class

### Authoritative references
- Plan: `.agents/docs/plans/2026-04-16-deep-clean-plan.md` Task 6.1 (lines ~1527-1614)
- Spec: `.agents/docs/specs/2026-04-16-deep-clean-design.md`
- Field reference notes: `.agents/notes/2026-04-16-deep-clean-field.md` (historical analysis)
- Field attribute traces: `.agents/notes/field-attr-*.md`, `.agents/notes/field-property-trace-processes.md`
- Current `opgee/field.py` (1825 lines — do NOT read fully; use offset/limit or targeted grep)
- Test file to rewrite: `tests/test_field.py`

### What Phase 6.1 must do

The current `opgee/field.py` still imports deleted modules and can't even be imported. Phase 6.1 is the biggest single-file refactor of the deep-clean:

1. **Remove from Field:**
   - `AttributeMixin`, `XmlInstantiable` base classes
   - `from_xml()`, `cache_attributes()`, `set_extend()`, `set_modifies()` class methods
   - `resolve_process_choices()`, all `@SmartDefault.register`-decorated methods
   - All Boundary-related methods (Boundary is deferred to post-v5)
   - `compute_carbon_intensity()` (deferred — CI analysis comes later)
   - `energy_and_emissions()`, `check_enabled_processes()`
   - All imports of deleted modules (`smart_defaults`, `audit`, `attributes`, `xml_utils`, `model`, `analysis`, `graph`, `bfs`, `process_groups`, etc.)

2. **Add a new explicit-param constructor** taking:
   - `name: str`
   - `simulation: SimulationParams`, `gwp: GWPData`, `tables: TableManager` (all via FieldContext)
   - `processes: list[Process]`, `streams: list[Stream]`
   - ~7 field-internal physical attrs (`num_prod_wells`, `oil_sands_mine`, `field_production_lifetime`, `res_press`, `res_temp`, `has_grid_mix`, ...)
   - Constructs `FieldContext` internally; binds processes/streams to a `networkx.DiGraph`.

3. **Replace `bfs.py` with networkx**: `nx.topological_sort`, `nx.simple_cycles`, `nx.ancestors`/`descendants` as needed.

4. **Move graph metadata from Process to Field**: `cycle_starts`, `impute_starts`, `run_after` become Field instance attrs, populated during graph construction (not read off individual processes).

5. **Simplify `run()`**: no `analysis` arg, no `trial_num`. GWP comes from `self.ctx.gwp`.

6. **Rewrite `tests/test_field.py`**: construct Field directly (no XML); keep assertion logic for energy/emission calculations.

### Field-facing callsites in Process subclasses that Phase 6.1 must satisfy

Every migrated Process expects a `FieldContext` (`ctx`), typed thermodynamic helpers (`gas: Gas` / `oil: Oil` / `water: Water`), and explicit scalar/DataFrame params. Field.__init__ (or a helper factory) must build all of these from its own physical state + `TableManager` lookups + `imported_gas_comp` slices and pass them in. Key requirements:

- `SteamGenerator` is constructed ONCE on Field (or just before `SteamGeneration`) with the full 40+ param list. Threaded into `SteamGeneration.__init__` via `steam_generator: "SteamGenerator"`.
- `TransportEnergy` is constructed ONCE on Field with `(residual_oil_LHV, residual_oil_density, ocean_tanker_size)`. Threaded into each of the 5 TransportEnergy callers.
- `loss_rate` for fugitive processes: Field (or construction code) looks up `component_fugitive_table[process.name]` once per process and passes the scalar in.
- `completion_and_workover_C1_rate`: computed once by Field (logic currently in `Field.get_completion_and_workover_C1_rate`, lines 951+ of field.py), passed to `downhole_pump.py` and `exploration.py`.
- `air_elevation_const`, `air_density_ratio`, `gravitational_acceleration`, `diesel_LHV`, `NG_heating_value`, `petrocoke_heating_value`, `mol_per_scf`, `days_per_year`: these are all `model.const("...")` lookups. Field must look them up once from its `TableManager.constants` and pass to each subprocess that needs them.
- `imported_gas_comp["<slot>"]` for each gas-composition slot: Field must slice from `imported_gas_comp` and pass the pd.Series to each consumer.
- `processing_unit_loss_rate_df` (from `gas_gathering.py`) is written to `ctx.process_data["processing_unit_loss_rate_df"]` at run time; three processes (acid_gas_removal, gas_dehydration, demethanizer) read it back.
- `gas_comp_H2S`: constructor param (was `field.attr("gas_comp_H2S")`), passed to `acid_gas_removal.py`.
- `WOR`, `API`, `GLIR`, `GFIR`, `FOR`, `SOR`, `oil_volume_rate`, `res_press`, `res_temp`, `wellhead_t`, `wellhead_p`, `stab_gas_press`, `gas_oil_ratio`, `gas_comp`, `depth`, `friction_factor`, `num_prod_wells`, `productivity_index`, `fraction_*`, `frac_*`, `eta_*`, and all the physical scalars: every caller expects these as explicit typed params.

The heaviest wiring work is inside `SteamGenerator` construction — ~50 values to source from Field.

### Dispatch strategy for Task 6.1

- **Single opus implementer** (not parallel): field restructure is architectural. Step 1 of the opus prompt should be to read `.agents/notes/2026-04-16-deep-clean-field.md` plus the plan Task 6.1 verbatim, then `opgee/field.py` in chunks.
- After opus returns, run spec-reviewer + code-quality reviewer (both on sonnet).
- Expect the diff to be very large (~1500 deleted lines, ~400 added).
- After commit, the scoped pytest subset stays at 116 passed / 6 errors; the 6 errors unblock in Phase 6.2 once the remaining test fixtures are rewritten.

---

## 4. Tags and recent commits (newest first)

```
(HEAD)  docs: phase 5 gate handoff                                                                  ← phase-5-gate, STOP
9f91c28 docs: phase 5 gate handoff (superseded by HEAD for tag resolution)
c6cc513 phase 5: migrate Tier 3 singles gas_partition.py + steam_generator.py (closes Task 5.3)
b9a53c0 phase 5: migrate Tier 3 Batch I (2 files, 30-32 refs) + exploration TransportEnergy rewire
7bf2a46 phase 5: migrate Tier 3 Batch H (3 files, 24-28 refs)
ea46dfb phase 5: migrate Tier 3 Batch G (3 files, 17-22 refs) + heavy_oil_dilution TransportEnergy rewire
bc5bdee phase 5: migrate Tier 3 Batch F + refactor predict_blower_energy_use (4 files)
69c2a82 phase 5: migrate Tier 3 Batch E (3 files, 14-15 refs)
449ca38 phase 5: migrate Tier 3 Batch D (3 files, 12-13 refs)
4b28c9c docs: mid-phase-5 handoff after Tier 1+2 completion (final revision)                        ← phase-5-tier-2-complete
cf3a438 phase 5: migrate Tier 2 Batch C (6 files, 8-11 field refs) + rewire 3 transport callers
4a269cf phase 5: migrate Tier 2 Batch B (7 files, 4-8 field refs)
f5f9344 phase 5: migrate Tier 2 Batch A (7 files, 3-5 field refs)
6a20b23 phase 5: migrate Tier 1 processes (12 files, 0-2 field refs)
5aabd26 phase 4: address 4.1 code-quality review                                                    ← phase-4-gate
```

Tag list (chronological): `phase-0-gate` → `phase-1-gate` → `phase-2-gate` → `phase-3-gate` → `phase-4-gate` → `phase-5-tier-2-complete` (mid-phase) → **`phase-5-gate`** + **`STOP`** (both on this commit). Next gate tag will be `phase-6-gate` after Task 6.4. The `STOP` tag marks the resume point for the next session.

---

## 5. Still-broken-as-expected files (entering Phase 6)

- `opgee/field.py` — imports deleted modules (`smart_defaults`, `audit`, `attributes`, etc.). Fixed by Task 6.1.
- `opgee/processes/shared.py::predict_blower_energy_use` — **NO**, already refactored in Phase 5.4 (Batch F atomic rewire).
- `tests/test_processes.py::test_get_reservoir` — references deleted `process.get_reservoir()`. Phase 6.2.
- `test_emissions.py::test_gwp*` + `test_use_GWP_error` — 6 errors at gate, accepted. Phase 6.2.
- Any test using `utils_for_tests.load_test_model` or the deleted `test_model`/`test_model_with_change`/`test_model2` fixtures. Phase 6.2.
- `opgee/processes/__init__.py` — 46 pre-existing F401 errors (explicit re-exports without `__all__`). Phase 6.3 (final cleanup).

---

## 6. Files to read at session start (for the next session)

1. **This file** — the handoff.
2. `.agents/docs/plans/2026-04-16-deep-clean-plan.md` — skim; read Phase 6 Task 6.1 in detail (lines ~1527-1614).
3. `.agents/notes/2026-04-16-deep-clean-field.md` — the historical Field analysis; the Task 6.1 implementer should read this.
4. `opgee/process.py` at `phase-5-gate` — confirm new `Process(name, ctx)` shape is unchanged since Phase 4.
5. `opgee/context.py` — confirm FieldContext interface (the contract Field must satisfy).
6. `opgee/processes/transport_energy.py` and `opgee/processes/steam_generator.py` — helper-class shapes Field must wire up.
7. (Optional) 2–3 migrated process files (e.g. `heavy_oil_upgrading.py`, `gas_partition.py`, `steam_generation.py`) — to understand the constructor parameter shapes Field must satisfy.

Historical reference (skim only if specifically needed):
- `.agents/notes/2026-04-16-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-17-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-16-deep-clean-process.md`
- `.agents/notes/field-attr-internal-vs-passthrough.md`

---

## 7. Process tips carried forward

1. **Always use `superpowers:subagent-driven-development`** — implementer → spec-compliance review → code-quality review → fix-up as needed → mark complete.
2. **Model selection for the remaining phases**:
   - Phase 6.1 (Field restructure) → **opus** (architectural).
   - Phase 6.2 (test adaptations) → **sonnet** per test file; some may be pure deletes.
   - Phase 6.3 (public API + pyproject cleanup) → **sonnet**.
   - Phase 6.4 (final gate) → **sonnet** for the run-and-report pattern.
   - Final code-review dispatch → **opus** via the `superpowers:code-reviewer` agent subtype.
3. **Critical rule**: no re-adding/restoring DELETED symbols. Every implementer prompt restates this and lists the specific forbidden symbols.
4. **Annotation style**: `from pint.facets.plain import PlainQuantity as Quantity` + bare `Quantity[float]`. NOT string-quoted, NOT `pint.Quantity`.
5. **Subagent prompt guardrails** (per `feedback_subagent_guardrails` memory): every implementer/fix-up prompt MUST wrap with OFF-TOPIC LOCKDOWN preamble + structured Fix Report footer. Reviewer prompts are exempt.
6. **Parallel dispatch strategy for Phase 6**: largely serial — each Phase 6 task is a single-file focus. Run spec + code-quality reviewers in parallel.
7. **Gate checks**: use the scoped pytest subset + targeted ruff. The full `pytest` and the full `ruff check .` both remain non-runnable until Phase 6.1 and 6.3 respectively.
8. **Every verification-gate task overwrites this file** — single stable name, not dated.
9. **Trust the diff, not the subagent report.** Verify directly when the report is ambiguous.

---

## 8. Phase 5 summary statistics

- **Files migrated in Phase 5:** 51 process subclasses + 2 helper classes (`transport_energy.py`, `steam_generator.py`) + 1 helper function (`predict_blower_energy_use` in `shared.py`).
- **Commits in Phase 5:** 11 (6 tier/batch commits in prior session `4b28c9c`, 7 Tier 3 commits + handoff revision in this session; one atomic rewire merged Task 5.4 into Batch F).
- **Lines changed (Phase 5 diff):** roughly +1800 / −1600 across the 51 process files (explicit param lists + docstring updates vs. removed cache_attributes / check_enabled / field-access chains).
- **Session TaskList turnover**: Phase 5.1 Tier 1 and Phase 5.2 Tier 2 completed in a prior session (`4b28c9c`); this session completed Phase 5.3 Tier 3, Phase 5.4 (atomic), and Phase 5.5 (this gate).
- **Ruff state at gate:** every migrated file individually clean. `opgee/processes/__init__.py` retains its 46 pre-existing F401s (Phase 4 baseline). Full `ruff check .` still fails on `opgee/field.py` (deleted-module imports) — Phase 6.1 fix.
- **Pytest state at gate:** 116 passed / 6 errors in the Phase 4 baseline subset (exact parity). Full `pytest` still non-runnable until Phase 6.1 + 6.2.
