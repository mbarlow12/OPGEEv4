# OPGEE v5 Deep Clean — Progress Handoff

**Branch:** `refactor/v5-deep-clean`
**Plan:** `.agents/docs/plans/2026-04-16-deep-clean-plan.md`
**Spec:** `.agents/docs/specs/2026-04-16-deep-clean-design.md`
**Execution mode:** `superpowers:subagent-driven-development` — TaskList + dispatched implementer / spec-reviewer / code-quality-reviewer subagents per task.
**Handoff convention:** This single file is overwritten at every phase gate. Prior dated handoffs (`2026-04-16-…`, `2026-04-17-…`) remain in `.agents/notes/` as historical reference only.

---

## 1. Status at this handoff

**Just completed:** Phase 4.1 + Phase 4.2 gate.
**Tag:** `phase-4-gate` applied at the docs commit on top of `5aabd26`.
**Next resume point:** Task 5.1 — migrate 12 Tier-1 process subclasses in parallel.

### What landed in Phase 4

| Task | Commit(s) | Summary |
|---|---|---|
| 4.1 process.py restructure | `e9ec51b` | Dropped `AttributeMixin` + `XmlInstantiable` bases; deleted class-registry plumbing (`get_subclasses`, `_subclass_dict`, `_Subclass_dict`, `decache_subclasses`, `_get_subclass`, `reload_subclass_dict`); deleted `Boundary` class; `IntermediateValues` lost its `OpgeeObject` base. New `Process.__init__(self, name: str, ctx: FieldContext)` with minimal instance state (no `model`/`field`/`gas`/`oil`/`water`/`boundary`/`impute_start`/`cycle_start`). Many methods dropped (`run_if_enabled`, `check_enabled`, `find_stream`, `get_reservoir`, `children`, `run_children`, `impute`, `venting_fugitive_rate`, `get_process_EF`, `from_xml`, `validate*`, `valdict`, `within_boundary`, `beyond_boundary`, `check_balances`). Retained methods modified to use `self.ctx.*` in place of `self.field.*` / `self.model.*` per Appendix B. `run(self, analysis)` → `run(self)`. `get_emission_rates(self, gwp)` — direct `gwp` param instead of `analysis.gwp`. `set_gas_fugitives` uses `self.ctx.stp`. `set_iteration_value` uses `self.ctx.simulation.maximum_change`. Class-level `iterating_processes` list moved to module-level `_iterating_processes` (Phase 6.1 will move ownership to Field). `self.process_EF = None` in `__init__`; `compute_emission_combustion` raises `ModelValidationError` if called before a subclass wires it. `Reservoir` kept as a minimal source-node subclass. 1092 → 594 lines (−46%). |
| 4.1 spec-review fix | `ffacaec` | Spec reviewer flagged `tests/test_processes.py:20` still calling `procA.get_emission_rates(analysis)` — fixed to `procA.get_emission_rates(analysis.gwp)` to match the new signature. Latent (test is `test_model`-fixture-blocked) but fix for correctness. |
| 4.1 code-quality-review fixes | `5aabd26` | (i) `register_iterating_process`/`check_iterator_convergence`/`reset_all_iteration` converted `@classmethod` → `@staticmethod` (the `cls` arg was pointless after the class-var → module-list move); (ii) `reset_all_iteration` now calls `_iterating_processes.clear()` after looping so a second field run doesn't duplicate entries; (iii) `get_compressor_and_well_loss_rate` body replaced with a clean `NotImplementedError` + Phase 5 TODO (was carrying a misleading `# noqa: F821` on `self.field`, which ruff wouldn't have flagged anyway); (iv) `intermediate_results` type hint corrected from `IntermediateValues \| None` to `dict \| None` (matches what `init_intermediate_results` actually assigns). Also dropped an unused `ureg` import. |

### Gate verification (run at `5aabd26`)

- `uv run ruff check opgee/process.py tests/test_processes.py` — **All checks passed!**
- AST parse on `opgee/process.py` — OK.
- Import smoke: `from opgee.process import Process, Reservoir, IntermediateValues, run_corr_eqns` — OK.
- `uv run pytest tests/test_chemistry.py tests/test_context.py tests/test_core.py tests/test_energy.py tests/test_import_export.py tests/test_molecule_names.py tests/test_stream.py tests/test_table_manager.py tests/test_thermofunction.py tests/test_utils.py tests/test_emissions.py -q` — **116 passed, 6 errors** (exact Phase 3 baseline; the 6 errors are all `test_emissions.py::test_gwp*` + `test_use_GWP_error`, fixture-blocked on deleted `test_model`, Phase 6.2 scope).
- Full `uv run pytest` is **still not runnable** — `opgee/field.py` still has deleted-module imports (including `decache_subclasses` now gone from `process.py`, adding one more broken import). Phase 6.1 scope.

### Phase 4 deviations / breadcrumbs

- **Scope creep accepted** (reviewer flagged, not a real deviation): implementer dropped the `stream.enabled` filter from `_find_streams_by_type`, `find_output_stream`, and `all_streams_ready` — `Stream.enabled` was already removed in Phase 3.3, so these filters were dead code that'd have raised `AttributeError` if exercised. The code-quality review explicitly endorsed this cleanup.
- **`tests/test_processes.py` import dropped `Process`**: after deleting the 3 `_get_subclass` tests, ruff flagged `Process` as F401. The spec said "keep `Process, Reservoir`" literally, but the pragmatic ruff-clean drop was accepted by both reviewers.
- **`test_get_reservoir` at `tests/test_processes.py:51`** references `process.get_reservoir()` which was deleted from `Process`. Fixture-blocked today so it's latent — **Phase 6.2 breadcrumb**: this test needs adaptation (or deletion) alongside the Field rewrite, not blamed on the fixture reintroduction.
- **`get_compressor_and_well_loss_rate` is now a `NotImplementedError` stub.** Only four callers: `sour_gas_injection`, `gas_lifting_compressor`, `gas_reinjection_well`, `CO2_injection_well` — all in Tier 1 or Tier 2 of Phase 5 migration. The Phase 5 migration for those four files must rebuild this method (or move the logic to explicit constructor params on the subclass) rather than calling the base method.
- **Off-task subagent anecdote (process improvement note)**: the fix-up subagent for the code-quality-review follow-ups applied all the correct file edits but its *text report* was replaced by output from a different, unrelated skill (a permissions analysis). The controller verified the actual filesystem changes matched the prompt exactly, then committed. Lesson: trust the diff, not the report. If a future subagent's report is nonsensical, check the working tree before re-dispatching.

---

## 2. TaskList state

| TaskList ID | Status | Subject |
|---|---|---|
| #1 | ✅ completed | Phase 3.3: Strip stream.py |
| #2 | ✅ completed | Phase 3.4: Verification gate — Phase 3 |
| #3 | ✅ completed | Phase 4.1: Restructure Process base class |
| #4 | ✅ completed | Phase 4.2: Verification gate — Phase 4 |
| #5 | 🔄 pending (next) | **Phase 5.1: Tier 1 — 12 simple processes (parallel dispatch)** ← resume here |
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

## 3. Resume point — Task 5.1: Tier 1 process subclass migration (parallel, 12 files)

### Authoritative references
- Plan: `.agents/docs/plans/2026-04-16-deep-clean-plan.md` Task 5.1 + Appendix A (Tier 1 file list) + Appendix B (transformation table)
- Spec: `.agents/docs/specs/2026-04-16-deep-clean-design.md`
- Process base (what subclasses must adapt to): `opgee/process.py` at `5aabd26` — new signature, `self.ctx.*` patterns
- Transformation table (Appendix B of the plan) — **authoritative** for `self.attr("x")` → explicit constructor param, `self.field.*` → `self.ctx.*`, etc.

### Tier 1 files (12 — parallel dispatch authorized by the plan)

All 12 can be dispatched as parallel implementer subagents simultaneously — they're independent, trivial, and zero-to-two `field.*` references each.

| File | Refs | Notes |
|------|------|-------|
| `processes/__init__.py` | 0 | Package init — likely just import-hygiene sweep |
| `processes/flaring.py` | 0 | |
| `processes/natural_gas_liquid.py` | 0 | |
| `processes/storage_well.py` | 0 | |
| `processes/CO2_injection_well.py` | 1 | `field.save_process_data` → `self.ctx.process_data[k] = v` |
| `processes/pre_membrane_chiller.py` | 1 | `self.attr` → constructor param |
| `processes/shared.py` | 1 | Helper module, not a Process subclass; also refactor `predict_blower_energy_use` per Task 5.4 (can be deferred) |
| `processes/sour_gas_injection.py` | 1 | `field.save_process_data` → ctx |
| `processes/compressor.py` | 2 | Helper class, not a Process subclass |
| `processes/gas_reinjection_well.py` | 2 | |
| `processes/LNG_transport.py` | 2 | |
| `processes/petrocoke_transport.py` | 2 | |

### Per-file implementer contract (applied to every Tier 1 subagent)

1. Read the assigned `processes/<file>.py`.
2. Read `opgee/process.py` to understand the new `__init__(name, ctx)` signature.
3. Apply transformations (Appendix B):
   - Add `ctx: FieldContext` param to `__init__` and call `super().__init__(name, ctx)`.
   - Replace `self.attr("x")` → `self.x` (add as explicit constructor param with class-level type annotation).
   - Replace `run(self, analysis)` → `run(self)`; drop `analysis.` references.
   - Replace `self.field.*` and `self.model.*` per the table.
   - Replace `from .log import getLogger` → `import logging`; `_logger = logging.getLogger(__name__)`.
   - Remove imports of deleted modules (attributes, config, smart_defaults, etc.).
   - Use `Quantity[float]` for pint type annotations.
4. Run `uv run ruff check opgee/processes/<file>.py` — clean.
5. Return a 1-paragraph report: what changed, ruff status, any surprises.

### Dispatch strategy for Task 5.1

- 12 implementer subagents, **sonnet model** (mechanical migration).
- **Dispatch them all in parallel** in a single assistant turn (per skill `superpowers:dispatching-parallel-agents`).
- **After all 12 return**: single controller run of `uv run ruff check opgee/processes/` + the scoped pytest set + a review sweep comparing each diff against the contract.
- Two-stage review at Tier-1 completion (not per-file): spec-compliance reviewer against the plan's Appendix B + a code-quality reviewer dispatched on the whole Tier 1 batch. Individual per-file reviews would be noise.
- Single commit for the batch: `phase 5: migrate Tier 1 processes (12 files, 0-2 field refs)`.

### Pre-flight for Task 5.1 dispatch
- Verify `opgee/context.FieldContext` exports `process_data` (it does — Phase 2.2).
- Verify `Stream` constructor takes `ctx: FieldContext | None` (it does — Phase 3.3).
- Verify `Process.__init__` takes `(name, ctx)` (it does — Phase 4.1).
- Confirm `field.save_process_data(k, v)` call sites in Tier 1 — grep shows `CO2_injection_well.py`, `sour_gas_injection.py`. Both map to `self.ctx.process_data[k] = v`.

---

## 4. Tags and recent commits (newest first)

```
5aabd26 phase 4: address 4.1 code-quality review (iterating_processes clear, F821 cleanup, type hint fix)  ← phase-4-gate
ffacaec phase 4: fix test_processes.py call-site for new get_emission_rates signature
e9ec51b phase 4: restructure Process base — new __init__(name, ctx), drop XML/boundary/enabled
8c531a5 docs: phase 3 gate handoff                                                                         ← phase-3-gate
2e4d322 phase 3: address 3.3 code-quality review (tests + ctx TODO + CARBON_NUMBER_SERIES move)
a5df80f phase 3: strip stream.py — remove XML, add FieldContext, extract chemistry
7f7e664 docs: add progress handoff for phase 3.2 completion
83978ff phase 3: decouple thermodynamics constructors from field/model
1509b6a phase 3: strip core.py to OpgeeObject + TP + STP + dict_from_list + Timer
9938f37 phase 2: create FieldContext with frozen GWPData and SimulationParams                              ← phase-2-gate
17e806e phase 2: create chemistry.py with extracted component data
f544f0f phase 1: fix remaining imports of deleted modules                                                  ← phase-1-gate
…
a73fb4f phase 0: bulk delete excluded files, tests, and dependencies                                       ← phase-0-gate
```

Tag list (chronological): `phase-0-gate` → `phase-1-gate` → `phase-2-gate` → `phase-3-gate` → **`phase-4-gate`**.

The `phase-4-gate` tag points at the docs commit that added this handoff on top of `5aabd26`.

---

## 5. Still-broken-as-expected files (pre-Phase 5)

- `opgee/field.py` — imports deleted modules (`decache_subclasses` [now gone from `process.py`], `smart_defaults`, etc.). Fixed by 6.1.
- All 51 `opgee/processes/*.py` subclasses — they inherit the old `Process(name, **kwargs)` pattern, reach through `self.field`/`self.attr(...)`/`self.model.*`, and take `run(self, analysis)`. Fixed by Phase 5.1–5.3.
- `opgee/processes/shared.py::predict_blower_energy_use` — takes `proc` that reads `proc.field.model.const(...)`. Fixed by 5.4.
- Any test that uses `utils_for_tests.load_test_model` or `configure_logging_for_tests`, or relies on `test_model`/`test_model_with_change`/`test_model2` fixtures. Phase 6.2.
- `tests/test_processes.py` — `test_get_reservoir` + ~40 other tests rely on Field/Analysis infrastructure. Phase 6.2.
- `test_emissions.py::test_gwp*` + `test_use_GWP_error` — 6 errors at gate, accepted. Phase 6.2.

---

## 6. Files to read at session start (for the next session)

1. **This file** — the handoff.
2. `.agents/docs/plans/2026-04-16-deep-clean-plan.md` — skim; read Phase 5 Task 5.1 + Appendix A + Appendix B in detail.
3. `opgee/process.py` at `5aabd26` — so you know what subclasses must conform to (new `__init__`, `self.ctx.*` surface).
4. `opgee/processes/__init__.py` + the 4 zero-ref files (`flaring.py`, `natural_gas_liquid.py`, `storage_well.py`) — skim to see how trivial they are before dispatching.
5. `opgee/processes/CO2_injection_well.py` + `sour_gas_injection.py` — the two `save_process_data` callers — confirm the ctx translation works.
6. `.agents/notes/2026-04-16-deep-clean-processes_shared.md` — for `shared.py` + `predict_blower_energy_use` context (Task 5.4 will revisit).

Historical reference (skim only if specifically needed):
- `.agents/notes/2026-04-16-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-17-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-16-deep-clean-process.md` (the proposal doc for Phase 4 — Phase 5 subclasses should treat it as context, not as their spec)

---

## 7. Process tips carried forward

1. **Always use `superpowers:subagent-driven-development`** — implementer → spec-compliance review → code-quality review → fix-up as needed → mark complete. Don't skip either review.
2. **Model selection**:
   - Tier 1 Phase 5 subclasses (mechanical, 0–2 refs) → **sonnet** in parallel batches.
   - Tier 2 Phase 5 (3–11 refs) → **sonnet** but watch for judgment calls that merit opus.
   - Tier 3 Phase 5 complex (12+ refs) + `gas_partition.py` / `steam_generator.py` → **opus**.
   - Phase 6.1 Field restructure → **opus**.
   - Reviewers → **sonnet** unless the work is architectural.
3. **Critical rule**: no re-adding/re-importing/restoring DELETE/DROP/REMOVE symbols. Every implementer prompt must restate this.
4. **Parallel dispatch authorized for Phase 5**:
   - Tier 1: 12 subagents in a single assistant turn
   - Tier 2 Batch A/B/C: 5–7 per batch
   - Tier 3: pairs / triples
   - Single-subagent for `gas_partition.py` and `steam_generator.py`.
5. **Gate checks only over the spec-compliant test subset**. Full `pytest` remains non-runnable until Phase 6.2 — don't chase the 6 pre-existing test_emissions errors in earlier phases.
6. **Every verification-gate task overwrites this file** — single stable name, not dated. Prior dated handoffs remain as history.
7. **Trust the diff, not the subagent report.** See §1's off-task subagent anecdote. If a report is nonsense but the file edits look correct, verify directly and commit.
