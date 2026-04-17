# OPGEE v5 Deep Clean — Progress Handoff

**Branch:** `refactor/v5-deep-clean`
**Plan:** `.agents/docs/plans/2026-04-16-deep-clean-plan.md`
**Spec:** `.agents/docs/specs/2026-04-16-deep-clean-design.md`
**Execution mode:** `superpowers:subagent-driven-development` — TaskList + dispatched implementer / spec-reviewer / code-quality-reviewer subagents per task.
**Handoff convention:** This single file is overwritten at every phase gate. Prior dated handoffs (`2026-04-16-…`, `2026-04-17-…`) remain in `.agents/notes/` as historical reference only.

---

## 1. Status at this handoff

**Just completed:** Phase 3 — all four tasks (3.1 core, 3.2 thermodynamics, 3.3 stream, 3.4 gate).
**Tag:** `phase-3-gate` at `2e4d322`.
**Next resume point:** Task 4.1 — restructure `opgee/process.py` base class.

### What landed in this phase

| Task | Commit(s) | Summary |
|---|---|---|
| 3.1 core.py | `1509b6a` | Stripped to `OpgeeObject` + `TemperaturePressure` (with set/get/copy_from) + `STP` + `dict_from_list` + `Timer`. 335→91 lines. |
| 3.2 thermodynamics.py | `83978ff` | Dropped `OpgeeObject` base from `ChemicalInfo`/`Air`/`AbstractSubstance`; deleted `WetAir`; new explicit constructors for Air/DryAir/AbstractSubstance/Oil/Gas/Water (no `field` arg); `R_GAS`/`STP.T`/`STP.P` replace `model.const(...)`. |
| 3.3 stream.py (initial) | `a5df80f` | Dropped `AttributeMixin` + `XmlInstantiable` bases, deleted `from_xml`/`children`/`validate`/`extend_components`, deleted class-level component data (imported from `opgee.chemistry`), deleted module-level helper duplicates. New `__init__` with `ctx: FieldContext | None = None`, `xml_data`→`initial_data`, dropped `enabled`/`parent`/`field`/`has_exogenous_data`. 747→546 lines. |
| 3.3 stream.py (review fixes) | `2e4d322` | Code-quality-review follow-ups: new `test_combustion_math` smoke test covering copy/multiply/reset/non_zero/voc_flow_rates/add_combustion_CO2_from; `TODO(phase 6.1)` marker on unused `ctx` param; relocated `_carbon_number_series` → `chemistry.CARBON_NUMBER_SERIES`. |

### Gate verification (run at `2e4d322`)

- `uv run ruff check` on all cleaned modules (chemistry, context, core, emissions, energy, error, import_export, stream, table_manager, thermodynamics, units, utils, combine_streams): **All checks passed!**
- `uv run pytest tests/test_chemistry.py tests/test_context.py tests/test_core.py tests/test_energy.py tests/test_import_export.py tests/test_molecule_names.py tests/test_stream.py tests/test_table_manager.py tests/test_thermofunction.py tests/test_utils.py tests/test_emissions.py -v`:
  **116 passed, 6 errors.**
  - All 55 `test_thermofunction.py` tests green (first activation in the new regime).
  - 6 errors: `test_emissions.py::test_gwp[5 variants]` + `test_use_GWP_error`. All are fixture-dependent on the deleted `test_model` / `Analysis.use_GWP` infrastructure. **Phase 6.2 scope** — these tests will be adapted or deleted when Field/Analysis is rewritten.
- Full `uv run pytest` is **not yet runnable** — `opgee/process.py` and `opgee/field.py` still import deleted modules (`attributes`, `smart_defaults`, etc.). Phase 4+ fixes those.

### What changed vs. the plan

No scope deviations in Phase 3. Two minor implementer deviations, both spec-reviewer-approved:

- **`tests/test_thermofunction.py::test_gas_volume_flow_rate_STP`** — one-line `.to("mmscf/day")` + `rel=10e-3` tolerance. Pre-existing latent bug (sibling test already had this fix); exposed only because `test_thermofunction.py` couldn't run until stream.py's `attributes` import was dropped.
- **`tests/test_chemistry.py::test_r_gas`** — `str(R_GAS.units) == "joule / kelvin / mole"` → `R_GAS.units == ureg.Unit("joule / kelvin / mole")`. `thermosteam` (transitively imported) mutates `ureg.default_format = '~P'` at load, so the string-based assertion failed once thermofunction could collect. Unit-value comparison is cleaner anyway.

Carried forward open items from prior handoffs (none blocking):
- `DryAir` singleton (unchanged since 3.2) — candidate for `@functools.cache` classmethod.
- `Oil.__init__` internally constructs `Water(...)` — candidate for constructor injection in Phase 6.1.
- Duplicate `test_tp = 1556.0 psia` vs `RES_PRESS = 1556.6` in `test_thermofunction.py` — intentional historical divergence; a clarifying comment is low-priority polish.
- `thermosteam` globally mutating `ureg.default_format` is a latent risk for any future string-based unit assertion — consider an isolation fixture in `conftest.py` as Phase 6.2 polish.

---

## 2. TaskList state

| TaskList ID | Status | Subject |
|---|---|---|
| #1 | ✅ completed | Phase 3.3: Strip stream.py |
| #2 | 🔄 in_progress | **Phase 3.4: Verification gate — Phase 3** ← finalizing now (tag + this handoff doc) |
| #3 | pending | Phase 4.1: Restructure Process base class |
| #4 | pending | Phase 4.2: Verification gate — Phase 4 |
| #5 | pending | Phase 5.1: Tier 1 — 12 simple processes (parallel) |
| #6 | pending | Phase 5.2: Tier 2 — 20 medium processes (3 parallel batches) |
| #7 | pending | Phase 5.3: Tier 3 — 19 complex processes |
| #8 | pending | Phase 5.4: Refactor `predict_blower_energy_use` |
| #9 | pending | Phase 5.5: Verification gate — Phase 5 |
| #10 | pending | Phase 6.1: Restructure Field class |
| #11 | pending | Phase 6.2: Adapt remaining test files |
| #12 | pending | Phase 6.3: Final cleanup — public API + dependencies |
| #13 | pending | Phase 6.4: Final verification gate |
| #14 | pending | Final code-reviewer dispatch for the whole refactor |

---

## 3. Resume point — Task 4.1: Restructure `opgee/process.py`

### Authoritative references
- Plan: `.agents/docs/plans/2026-04-16-deep-clean-plan.md` Task 4.1
- Symbol-level retain/drop: `.agents/notes/2026-04-16-deep-clean-process.md` (read in full — it enumerates every method)
- Transformation patterns (for Phase 5 and for internal `self.field` removal): plan Appendix B
- `opgee/context.py` — for the `FieldContext` type the new `__init__` takes

### Core instruction (summary — full detail in proposal doc)

New `Process.__init__`:
```python
def __init__(self, name: str, ctx: FieldContext):
    self.name = name
    self.ctx = ctx
    self.emissions = Emissions()
    self.energy = Energy()
    self.import_export = ImportExport()
    self.intermediate_results = IntermediateValues()
    self.inputs = []
    self.outputs = []
    # + iteration-state ivars (visit_count, iteration_count, ...)
```

Drop: `AttributeMixin` / `XmlInstantiable` bases, `from_xml`, `validate`/`validate_proc`/`validate_streams`, `children`/`run_if_enabled`/`check_enabled`, `find_stream`, `get_reservoir`, `impute`, `venting_fugitive_rate`, `get_process_EF`, `within_boundary`/`beyond_boundary`, `check_balances`, class-level subclass registry (`get_subclasses`, `_subclass_dict`, `decache_subclasses`, `_get_subclass`, `reload_subclass_dict`), `clear_iterating_process_list`, `set_run_after`/`set_extend`, `Boundary` class entirely.

Keep ~35 retained methods (`reset`, `add_emission_rate`/s, `add_energy_rate`/s, `set_combustion_emissions`, `compute_emission_combustion`, `set_import_from_energy`, `set_gas_fugitives`, `get_compressor_and_well_loss_rate`, stream lookup engine, `visit`/`visited`, `predecessors`/`successors`, `set_iteration_value`, `register_iterating_process`/`check_iterator_convergence`/`reset_all_iteration`/`reset_iteration`/`_reset_before_iteration`, `run` abstract, `print_running_msg`, `all_streams_ready`, `sum_intermediate_results`/`init_intermediate_results`/`get_intermediate_results`). Several need modification where they currently reach through `self.field` or `self.model` — use `self.ctx.*` instead per Appendix B.

Keep simplified `Reservoir` (minimal source-node Process subclass). Keep `IntermediateValues` inner class. Keep module-level `run_corr_eqns` helper.

**Expected consequence**: most `processes/*.py` subclass tests will break at collection time. That's OK — Phase 5.1–5.3 fixes them.

### Pre-flight for Task 4.1 dispatch
- Verify `opgee.context.FieldContext` exports fields the new Process needs (stp, tables, gwp, process_data) — done in 2.2, confirmed.
- Verify `opgee.core.STP` + `opgee.chemistry.R_GAS` importable — done.
- Confirm no surviving call-sites for the class-registry functions outside of `opgee/process.py` itself: grep pending (should be clean — those were XML-plumbing only).
- Decide whether `self.ctx.process_data` becomes the new home for `self.field.save_process_data(k, v)` / `self.field.get_process_data(k)` — per Appendix B, yes: `self.field.save_process_data(k, v)` → `self.ctx.process_data[k] = v`; `self.field.get_process_data(k)` → `self.ctx.process_data[k]`. Callers migrate in Phase 5.

### Suggested model
**opus** — 1092-line class with many interlocking methods and subtle dependencies (iteration state, graph traversal hooks). Mechanical migration alone would be sonnet-scale, but the design decisions on what to keep vs. prune want opus judgment.

---

## 4. Tags and recent commits (newest first)

```
2e4d322 phase 3: address 3.3 code-quality review (tests + ctx TODO + CARBON_NUMBER_SERIES move)  ← phase-3-gate
a5df80f phase 3: strip stream.py — remove XML, add FieldContext, extract chemistry
7f7e664 docs: add progress handoff for phase 3.2 completion
83978ff phase 3: decouple thermodynamics constructors from field/model
1509b6a phase 3: strip core.py to OpgeeObject + TP + STP + dict_from_list + Timer
9938f37 phase 2: create FieldContext with frozen GWPData and SimulationParams  ← phase-2-gate
17e806e phase 2: create chemistry.py with extracted component data
f544f0f phase 1: fix remaining imports of deleted modules                       ← phase-1-gate
…
a73fb4f phase 0: bulk delete excluded files, tests, and dependencies           ← phase-0-gate
```

Tag list (chronological): `phase-0-gate` → `phase-1-gate` → `phase-2-gate` → **`phase-3-gate`**.

---

## 5. Still-broken-as-expected files (pre-Phase 4)

- `opgee/process.py` — imports `AttributeMixin`, `XmlInstantiable`, XML decorators, config/smart_defaults helpers. Fixed by 4.1.
- `opgee/field.py` — many deleted-module imports; also has 28 `@SmartDefault.register`-stripped bare methods from Phase 1.9 that are dead code until 6.1.
- Any test that uses `utils_for_tests.load_test_model` or `configure_logging_for_tests` — still broken. Phase 6.2 cleans up.
- `test_emissions.py::test_gwp*` + `test_use_GWP_error` — fixture-dependent. Phase 6.2 scope. 6 errors at gate, accepted.

---

## 6. Files to read at session start (for the next session)

1. **This file** — the handoff.
2. `.agents/docs/plans/2026-04-16-deep-clean-plan.md` — skim, then read Phase 4 Task 4.1 in detail.
3. `.agents/notes/2026-04-16-deep-clean-process.md` — authoritative symbol-level proposal for `process.py`.
4. `opgee/process.py` — read in full (1092 lines; heavy file).
5. `opgee/context.py` — know the `FieldContext` surface.
6. Plan Appendix B — transformation patterns that will also govern Phase 5.

Historical reference (unchanged, only skim if needed):
- `.agents/notes/2026-04-16-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-17-deep-clean-progress-handoff.md`

---

## 7. Process tips carried forward

1. **Always use `superpowers:subagent-driven-development`** — implementer → spec-compliance review → code-quality review → fix-up as needed → mark complete. Don't skip either review.
2. **Use `opus` for complex tasks** (process.py restructure, gas_partition.py, steam_generator.py, field.py). Use `sonnet` for mechanical migrations (Tier 1 processes, lint fixes).
3. **Respect the critical rule** — no re-adding, re-importing, or restoring DELETE/DROP/REMOVE symbols. Every implementer prompt must restate this.
4. **Flag plan discrepancies proactively** — the plan has several small inconsistencies; when an agent hits one, STOP and escalate.
5. **Parallel dispatch authorized for Phase 5** — Tier 1 runs 12 subagents in parallel, Tier 2 runs in batches of 5–7, Tier 3 in batches of 2–3. Single-subagent dispatches for `gas_partition.py` and `steam_generator.py`.
6. **Every verification-gate task overwrites this file** — single stable name, not dated. Prior dated handoffs remain as history.
