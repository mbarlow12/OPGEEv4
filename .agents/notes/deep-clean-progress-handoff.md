# OPGEE v5 Deep Clean — Progress Handoff

**Branch:** `refactor/v5-deep-clean`
**Plan:** `.agents/docs/plans/2026-04-16-deep-clean-plan.md`
**Spec:** `.agents/docs/specs/2026-04-16-deep-clean-design.md`
**Execution mode:** `superpowers:subagent-driven-development` — TaskList + dispatched implementer / spec-reviewer / code-quality-reviewer subagents per task.
**Handoff convention:** This single file is overwritten at every phase gate (and at major mid-phase checkpoints). Prior dated handoffs (`2026-04-16-…`, `2026-04-17-…`) remain in `.agents/notes/` as historical reference only.

---

## 1. Status at this handoff

**Just completed:** Task 5.1 (Tier 1, 12 files) + Task 5.2 (Tier 2, 20 files in 3 batches A/B/C). All committed and verified.
**Next resume point:** Task 5.3 — migrate 19 Tier 3 process subclasses in batches D–I, plus single dispatches for `gas_partition.py` (52 refs) and `steam_generator.py` (61 refs).

### What landed since the previous handoff (phase-4-gate `5aabd26`)

| Commit | Subject | Files |
|---|---|---|
| `6a20b23` | phase 5: migrate Tier 1 processes (12 files, 0-2 field refs) | `__init__.py`, `flaring.py`, `natural_gas_liquid.py`, `storage_well.py`, `CO2_injection_well.py`, `pre_membrane_chiller.py`, `shared.py` (audit only), `sour_gas_injection.py`, `compressor.py` (helper class — drop OpgeeObject + `__init__`, retype static-method `field`→`gas: Gas`), `gas_reinjection_well.py` (drop `check_enabled` too), `LNG_transport.py` (NotImplementedError TODO pending TransportEnergy), `petrocoke_transport.py` (same TODO). |
| `f5f9344` | phase 5: migrate Tier 2 Batch A (7 files, 3-5 field refs) | `LNG_regasification.py`, `pre_membrane_compressor.py`, `storage_compressor.py`, `storage_separator.py`, `VRU_compressor.py`, `gas_distribution.py`, `gas_lifting_compressor.py`. Annotation-style fixes applied (string-quoted/`pint.Quantity` → bare `Quantity[float]`). |
| `4a269cf` | phase 5: migrate Tier 2 Batch B (7 files, 4-8 field refs) | `ryan_holmes.py`, `CO2_reinjection_compressor.py`, `LNG_liquefaction.py`, `post_storage_compressor.py`, `sour_gas_compressor.py`, `CO2_membrane.py`, `crude_oil_transport.py` (third TODO/NotImplementedError pending TransportEnergy). |
| `cf3a438` | phase 5: migrate Tier 2 Batch C (6 files, 8-11 field refs) + rewire 3 transport callers | `transport_energy.py` (helper migration: drop `OpgeeObject`, drop `field` first arg from `get_transport_energy_dict`, replace `field.<x>` with constructor params + explicit `denominator` method arg), `VF_partition.py`, `gas_gathering.py`, `gas_reinjection_compressor.py`, `transmission_compressor.py`, `water_injection.py`. **Atomic rewire**: `LNG_transport.py`, `petrocoke_transport.py`, `crude_oil_transport.py` all now call the new TransportEnergy API (NotImplementedError TODOs gone). |

### TransportEnergy API — final shape (after `cf3a438`)

`TransportEnergy.__init__(self, residual_oil_LHV: Quantity[float], residual_oil_density: Quantity[float], ocean_tanker_size: Quantity[float])`

`TransportEnergy.get_transport_energy_dict(self, parameter_table, transport_share_fuel, transport_by_mode, LHV_rate, prod_type: str, denominator: Quantity[float])`

The `denominator` previously came from per-product field/model lookups (`field.gas.component_LHV_mass[...]`, `model.const(...)`, `field.get_process_data("crude_LHV")`). Each caller now computes the appropriate denominator and passes it explicitly:
- LNG: `self.gas.component_LHV_mass["C1"]`
- Petrocoke: `self.petro_coke_heating_value / 1.10231` (short-ton → tonne conversion preserved)
- Crude oil: `self.ctx.process_data["crude_LHV"]`

### Gate verification at `cf3a438`

- `uv run ruff check opgee/processes/<all 32 files migrated so far>` — **All checks passed!**
- Forbidden-symbol grep (`self.field`, `self.model.`, `self.attr(`, `cache_attributes`, `def check_enabled`, `set_enabled\b`, `venting_fugitive_rate`, string-quoted `"Quantity[float]"`) over the 32 files — **zero hits in live code** (only references inside TODO/comment text in a few files, which are documentation only).
- `uv run pytest tests/test_chemistry.py tests/test_context.py tests/test_core.py tests/test_energy.py tests/test_import_export.py tests/test_molecule_names.py tests/test_stream.py tests/test_table_manager.py tests/test_thermofunction.py tests/test_utils.py tests/test_emissions.py -q` — **116 passed, 6 errors** (exact Phase 4 baseline; 6 errors are `test_emissions.py::test_gwp*` + `test_use_GWP_error`, fixture-blocked on deleted `test_model`, Phase 6.2 scope).
- Full `uv run pytest` is **still not runnable** — `opgee/field.py` still has deleted-module imports; will be fixed in Phase 6.1.

### Phase 5.1/5.2 deviations / breadcrumbs

- **`heavy_oil_dilution.py` (Tier 3)** still uses the legacy 7-arg TransportEnergy API. The Tier 3 implementer for that file MUST rewire it to the new API (matching the LNG/petrocoke/crude pattern from Batch C).
- **`exploration.py` (Tier 3)** uses `field.transport_energy` (legacy access). Tier 3 implementer must convert to constructor param `transport_energy: TransportEnergy` and route through the new API.
- **Annotation style watchpoint:** Tier 1 code review flagged a recurring inconsistency where some implementers use `"Quantity[float]"` (string-quoted), some `pint.Quantity` (bare). Each implementer prompt for Tier 3 should explicitly say: **`from pint.facets.plain import PlainQuantity as Quantity` + bare `Quantity[float]`** (not string-quoted, not `pint.Quantity`). The controller fixed these inline in Batches A and B and they have not recurred in Batch C.
- **Reviewer cadence:** Tier 1 ran full two-stage review (spec + code-quality). Batch A ran spec-only. Batches B/C used inline forbidden-symbol grep + ruff + scoped pytest as the quality gate (skipping reviewer dispatch to conserve session context). For Tier 3 (higher per-file complexity), revert to per-batch spec+code-quality reviewers.
- **`compressor.py` constructor was deleted** (Tier 1) because it had zero callers. All `Compressor.<staticmethod>(...)` calls now take `gas: Gas` instead of `field`. Every Tier 2 file that used Compressor was updated accordingly. Tier 3 files (e.g. `downhole_pump.py`, `steam_generation.py`, etc.) that use Compressor must do the same.
- **`get_compressor_and_well_loss_rate` callers fully migrated**: the four pre-existing call sites (`sour_gas_injection`, `gas_lifting_compressor`, `gas_reinjection_well`, `CO2_injection_well`) were all rewired to take `loss_rate: Quantity[float]` as a constructor param. The base method's NotImplementedError stub remains in place but is no longer called from anywhere.

---

## 2. TaskList state

| TaskList ID | Status | Subject |
|---|---|---|
| #1 | ✅ completed | Phase 5.1: Tier 1 — 12 simple processes |
| #2 | ✅ completed | Phase 5.2: Tier 2 — 20 medium processes (3 batches) |
| #3 | 🔄 pending (next) | **Phase 5.3: Tier 3 — 19 complex processes (batches D–I + 2 single)** ← resume here |
| #4 | pending | Phase 5.4: Refactor `predict_blower_energy_use` |
| #5 | pending | Phase 5.5: Verification gate — Phase 5 |
| #6 | pending | Phase 6.1: Restructure Field class |
| #7 | pending | Phase 6.2: Adapt remaining test files |
| #8 | pending | Phase 6.3: Final cleanup — public API + dependencies |
| #9 | pending | Phase 6.4: Final verification gate |
| #10 | pending | Final code-reviewer dispatch for the whole refactor |

(IDs #1–#10 in this table are TaskCreate IDs from the current session; they were 1–14 in the prior handoff, renumbered after a fresh `TaskCreate` round at session start.)

---

## 3. Resume point — Task 5.3: Tier 3 process subclass migration (19 files)

### Authoritative references
- Plan: `.agents/docs/plans/2026-04-16-deep-clean-plan.md` Task 5.3 + Appendix A (Tier 3 file list, 19 files) + Appendix B (transformation table)
- Spec: `.agents/docs/specs/2026-04-16-deep-clean-design.md`
- Process base (target shape): `opgee/process.py` at `5aabd26` (unchanged since Phase 4)
- TransportEnergy reference (for `heavy_oil_dilution.py` and `exploration.py`): the 6 callers already migrated in Tier 2 Batch C — see `crude_oil_transport.py` for the cleanest pattern.

### Tier 3 batches (per plan Task 5.3)

| Batch | Files | Refs |
|------|------|------|
| D | `crude_oil_stabilization.py`, `crude_oil_storage.py`, `heavy_oil_upgrading.py` | 12, 13, 13 |
| E | `bitumen_mining.py`, `crude_oil_dewatering.py`, `reservoir_well_interface.py` | 14, 14, 15 |
| F | `acid_gas_removal.py`, `gas_dehydration.py`, `demethanizer.py` | 16, 16, 18 |
| G | `venting.py`, `heavy_oil_dilution.py`, `water_treatment.py` | 17, 22, 22 |
| H | `drilling.py`, `steam_generation.py`, `downhole_pump.py` | 24, 25, 28 |
| I | `separation.py`, `exploration.py` | 30, 32 |
| (single) | `gas_partition.py` | 52 — heaviest Process subclass |
| (single) | `steam_generator.py` | 61 — heaviest overall, helper class |

### Per-file implementer contract (proven in Tier 1 + Tier 2)

1. Read assigned file + `opgee/process.py` lines 1–150 (new __init__ shape).
2. Apply Appendix B transformations:
   - `super().__init__(name, **kwargs)` → `super().__init__(name, ctx)`
   - `__init__(self, name, **kwargs)` → `__init__(self, name: str, ctx: FieldContext, ...explicit typed params)`
   - `run(self, analysis)` → `run(self)`
   - `self.attr` / `self.field.attr` / `self.field.<x>` → constructor param
   - `self.field.gas/oil/water` → `gas: Gas` / etc constructor param
   - `self.field.stp` → `self.ctx.stp`
   - `self.field.process_data[k]` → `self.ctx.process_data[k]` (or `.get` for None-guard)
   - `self.field.save_process_data(k,v)` → `self.ctx.process_data[k] = v`
   - `self.field.import_export` → `self.import_export` (Process base)
   - `self.model.const(...)` → constructor param OR inline literal
   - `self.model.<csv_table>` → constructor param (caller pre-slices)
   - `self.venting_fugitive_rate()` → `self.loss_rate` constructor param
   - `self.get_compressor_and_well_loss_rate(...)` → `self.loss_rate` constructor param
   - `cache_attributes()` method → DELETE; logic absorbed into `__init__`
   - `check_enabled()` method → DELETE entirely
   - `Compressor.<staticmethod>(field, ...)` → `Compressor.<staticmethod>(gas, ...)`
3. Annotation style: `from pint.facets.plain import PlainQuantity as Quantity` + bare `Quantity[float]` (NOT string-quoted, NOT `pint.Quantity`).
4. Each implementer prompt MUST include the OFF-TOPIC LOCKDOWN preamble + structured Fix Report footer (per `feedback_subagent_guardrails` memory).
5. Run `uv run ruff check opgee/processes/<file>.py` — must be clean.
6. Do NOT commit. Do NOT touch other files (except for the heavy_oil_dilution + exploration TransportEnergy rewires, which are scoped to those two files only).

### Dispatch strategy for Task 5.3

- **Batches D–I**: 2–3 parallel implementers per batch, sonnet model.
- **`gas_partition.py`**: single subagent, **opus** (52 refs, complex per handoff guidance).
- **`steam_generator.py`**: single subagent, **opus** (61 refs, helper class with ~40 uncached field attrs).
- After each batch completes: ruff + scoped pytest + forbidden-symbol grep + (for Tier 3) full spec+code-quality reviewer round (Tier 1/2 batches that skipped code-quality review left some style debt — Tier 3 is more complex per file and needs the full review pass).
- Single commit per batch: `phase 5: migrate Tier 3 Batch <X> (<n> files, <range> refs)`.

### Pre-flight for Task 5.3 dispatch
- Verify all Tier 1 + Tier 2 files are committed (last commit: `cf3a438`).
- Confirm `TransportEnergy` migration is complete and `heavy_oil_dilution.py` + `exploration.py` are the only remaining users of the legacy API.
- For each Tier 3 implementer, optionally point to `.agents/notes/field-attr-trace-processes.md` for deep ref maps (the implementer will normally derive everything from file inspection).

---

## 4. Tags and recent commits (newest first)

```
cf3a438 phase 5: migrate Tier 2 Batch C (6 files, 8-11 field refs) + rewire 3 transport callers
4a269cf phase 5: migrate Tier 2 Batch B (7 files, 4-8 field refs)
f5f9344 phase 5: migrate Tier 2 Batch A (7 files, 3-5 field refs)
6a20b23 phase 5: migrate Tier 1 processes (12 files, 0-2 field refs)
00d4d4e docs: phase 4 gate handoff
5aabd26 phase 4: address 4.1 code-quality review                                       ← phase-4-gate
ffacaec phase 4: fix test_processes.py call-site for new get_emission_rates signature
e9ec51b phase 4: restructure Process base — new __init__(name, ctx), drop XML/boundary/enabled
8c531a5 docs: phase 3 gate handoff                                                     ← phase-3-gate
2e4d322 phase 3: address 3.3 code-quality review (tests + ctx TODO + CARBON_NUMBER_SERIES move)
a5df80f phase 3: strip stream.py — remove XML, add FieldContext, extract chemistry
…
9938f37 phase 2: create FieldContext with frozen GWPData and SimulationParams          ← phase-2-gate
f544f0f phase 1: fix remaining imports of deleted modules                              ← phase-1-gate
a73fb4f phase 0: bulk delete excluded files, tests, and dependencies                   ← phase-0-gate
```

Tag list (chronological): `phase-0-gate` → `phase-1-gate` → `phase-2-gate` → `phase-3-gate` → `phase-4-gate`. **No new tag yet** — `phase-5-gate` will be applied at Task 5.5.

---

## 5. Still-broken-as-expected files (pre-Phase 6)

- `opgee/field.py` — imports deleted modules (`smart_defaults`, etc.). Fixed by 6.1.
- All 19 remaining Tier 3 `opgee/processes/*.py` subclasses — they inherit the old `Process(name, **kwargs)` pattern, reach through `self.field`/`self.attr(...)`/`self.model.*`, and take `run(self, analysis)`. Fixed by Phase 5.3.
- `opgee/processes/shared.py::predict_blower_energy_use` — takes `proc` that reads `proc.field.model.const(...)`. Fixed by 5.4.
- `tests/test_processes.py::test_get_reservoir` — references deleted `process.get_reservoir()`. Phase 6.2.
- `test_emissions.py::test_gwp*` + `test_use_GWP_error` — 6 errors at gate, accepted. Phase 6.2.
- Any test that uses `utils_for_tests.load_test_model` or relies on `test_model`/`test_model_with_change`/`test_model2` fixtures. Phase 6.2.

---

## 6. Files to read at session start (for the next session)

1. **This file** — the handoff.
2. `.agents/docs/plans/2026-04-16-deep-clean-plan.md` — skim; read Phase 5 Task 5.3 + Appendix A (Tier 3 file list) + Appendix B in detail.
3. `opgee/process.py` at `cf3a438` — confirm new `Process(name, ctx)` shape (unchanged since Phase 4).
4. `opgee/processes/transport_energy.py` at `cf3a438` — for the `heavy_oil_dilution.py` and `exploration.py` rewires (the new API).
5. `opgee/processes/crude_oil_transport.py` at `cf3a438` — cleanest pattern for a TransportEnergy caller; reference template for the two Tier 3 rewires.
6. (Optional) `opgee/processes/separation.py` or another representative Tier 3 file — to gauge the per-file complexity before dispatching the first batch.

Historical reference (skim only if specifically needed):
- `.agents/notes/2026-04-16-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-17-deep-clean-progress-handoff.md`
- `.agents/notes/2026-04-16-deep-clean-process.md`

---

## 7. Process tips carried forward

1. **Always use `superpowers:subagent-driven-development`** — implementer → spec-compliance review → code-quality review → fix-up as needed → mark complete.
2. **Model selection**:
   - Tier 3 simple (12-22 refs) → **sonnet** in pairs/triples per batch.
   - Tier 3 heavy (24-32 refs) → **sonnet** (still mechanical; opus only if implementer reports BLOCKED on judgment calls).
   - **`gas_partition.py` (52 refs) and `steam_generator.py` (61 refs) → opus**.
   - Phase 6.1 Field restructure → **opus**.
   - Reviewers → **sonnet** unless the work is architectural.
3. **Critical rule**: no re-adding/restoring DELETED symbols. Every implementer prompt restates this and lists the specific forbidden symbols.
4. **Annotation style**: `from pint.facets.plain import PlainQuantity as Quantity` + bare `Quantity[float]`. NOT string-quoted, NOT `pint.Quantity`.
5. **Subagent prompt guardrails** (per `feedback_subagent_guardrails` memory): every implementer/fix-up prompt MUST wrap with OFF-TOPIC LOCKDOWN preamble + structured Fix Report footer. Reviewer prompts are exempt.
6. **Parallel dispatch strategy**:
   - Tier 3 batches D–I: 2–3 parallel implementers per batch.
   - `gas_partition.py` and `steam_generator.py`: single-subagent each (opus).
   - One controller-side fix-up commit per batch.
7. **Gate checks only over the spec-compliant test subset**. Full `pytest` remains non-runnable until Phase 6.2 — don't chase the 6 pre-existing test_emissions errors in Phase 5.
8. **Every verification-gate task overwrites this file** — single stable name, not dated. This handoff was written mid-Phase 5 to checkpoint after Tier 1+2 completion (not at a phase gate). Phase 5.5 will write the next one after Tier 3 completes.
9. **Trust the diff, not the subagent report.** Verify directly when the report is ambiguous. (See prior 2026-04-17 handoff §1 for the off-task-subagent anecdote.)
