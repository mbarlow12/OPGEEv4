# OPGEE v5 Deep Clean — Progress Handoff

**Date**: 2026-04-16
**Branch**: `refactor/v5-deep-clean`
**Plan**: `.agents/docs/plans/2026-04-16-deep-clean-plan.md`
**Spec**: `.agents/docs/specs/2026-04-16-deep-clean-design.md`
**Execution mode**: `superpowers:subagent-driven-development` (TaskCreate list + dispatched implementer/reviewer subagents per task)

---

## 1. Completed Work (Phases 0, 1, 2 + partial 3)

### Phase 0: Bulk Delete (✅ gate tagged `phase-0-gate`)

| Task | Commit | Summary |
|------|--------|---------|
| 0.1 Delete source files | (consolidated) | 24 `.py`/`.sh` files + `built_ins/` + `bin/` + selective `etc/` (48 deletions staged) |
| 0.2 Delete test files | (consolidated) | 21 test files + 17 test data files + `post-proc-plugins/` |
| 0.3 Minimal conftest / strip utils_for_tests | (consolidated) | `conftest.py` 65→13 lines; `utils_for_tests.py` 91→44 lines |
| 0.4 pyproject.toml | (consolidated) | Removed `[project.scripts]` opg entry |
| 0.5 Gate | `a73fb4f` | Consolidated Phase 0 commit. Also deleted `tests/test_packet.py` (spec omission — imported deleted `manager.py`) and ruff-cleaned pre-existing nits in surviving tests |

**Known Phase 0 side note:** Implementer scope-crept minor cosmetic ruff fixes in 11 surviving test files (f-string prefixes, `isinstance` vs `type() ==`, `is None` vs `== None`, duplicate function-name rename). Harmless; documented here for traceability.

### Phase 1: Clean Leaf Modules (✅ gate tagged `phase-1-gate`)

| Task | Commit | Summary |
|------|--------|---------|
| 1.1 error.py | `3b90730` | Dropped 9 exceptions; kept 8 (OpgeeException, OpgeeStopIteration, OpgeeMaxIterationsReached, OpgeeIterationConverged, AbstractMethodError, ModelValidationError, BalanceError, ZeroEnergyFlowError). Dropped `.boundary` ref in ZeroEnergyFlowError.__str__ |
| 1.2 units.py | `bf48e35` | Stdlib logging, `importlib.resources`, dropped `Qty` alias |
| 1.2a pint_pandas | `dddf8e4` | **Non-plan fix** — added `import pint_pandas  # noqa: F401` to units.py because tests importing Energy directly failed without pint_pandas registered first. See §4. |
| 1.3 energy.py | `e9a0f24` | Dropped OpgeeObject + dead logger |
| 1.4 emissions.py | `ccd9bb9` | Dropped OpgeeObject (kept `from .stream import Stream` — migrates to chemistry.py in Phase 3) |
| 1.5 import_export.py | `4c6b5b9` | Dropped OpgeeObject + dead logger; hoisted inner `ureg` import |
| 1.6 utils.py | `ae0a6a3` | Stripped 323→54 lines. New `coercible(value, type_fn, default=None)` signature (⚠️ semantic change, see §4). `getBooleanXML = parse_boolean` alias kept |
| 1.7 table_manager.py | `8c840b8` | Dropped OpgeeObject, absorbed pkg_utils via `importlib.resources.files`, dropped XML updates. test_table_manager.py had `_path_to_test_file` inlined to bypass broken utils_for_tests chain |
| 1.8 combine_streams.py | `3458ec4` | Stdlib logging + fix header comment |
| 1.9 Fix remaining imports | `f544f0f` | Mass replaced `from ..log import getLogger` in 45 processes files. Hand-fixed process.py (getParamAsBoolean→False hardcoded), field.py (removed 5 deleted-module imports + 28 `@SmartDefault.register` decorators). stream.py logger fix |

**Gate compromise**: Phase 1 gate as literally specified ("both must pass") can't be met — `opgee/process.py` and `opgee/stream.py` still have `from .attributes import ...` (Phase 3 fixes). User agreed on the pragmatic interpretation: parse-clean + surviving tests green + tag gate. 35 tests pass across test_chemistry, test_context, test_utils, test_energy, test_import_export, test_table_manager.

### Phase 2: New Foundations (✅ gate tagged `phase-2-gate`)

| Task | Commit | Summary |
|------|--------|---------|
| 2.1 chemistry.py | `17e806e` | Extracted 48 COMPONENT_NAMES, 43 CARBON_NUMBER entries, 29 VOCS, 30 HYDROCARBONS (C1..C30 from pubchem-cid.csv), R_GAS=8.31446 J/mol/K. Helpers `is_carbon_number`, `is_hydrocarbon`, `molecule_to_carbon`, `carbon_to_molecule`. 6/6 tests pass. Note: plan's test said `C5 in CARBON_NUMBER == 5` (integer) — chemistry.py stores as floats (`5.0`), test was written to accept |
| 2.2 context.py | `9938f37` | Created `FieldContext` (mutable, process_data dict), `GWPData` (frozen), `SimulationParams` (frozen). 5/5 tests pass. core.py imported cleanly (no attributes chain) |

### Phase 3: Strip Core Classes — IN PROGRESS

| Task | Commit | Status |
|------|--------|--------|
| 3.1 core.py | `1509b6a` | ✅ DONE. Stripped 335→91 lines. Kept OpgeeObject (with name/str), TemperaturePressure (full methods incl. set/get/copy_from per user decision), STP constants, dict_from_list, Timer. Dropped XmlInstantiable, A, elt_name, instantiate_subelts, name_of, split_attr_name, CLASS_DELIMITER. test_core.py 55→34 lines, 4/4 pass |
| **3.2 thermodynamics.py** | — | **🔄 IN PROGRESS — Task 3.2 implementer prompt was interrupted by user** |
| 3.3 stream.py | — | ⏳ Pending |
| 3.4 Phase 3 gate | — | ⏳ Pending |

---

## 2. Housekeeping Commit (pre-Phase 0)

**Commit** `207f7a1` — `chore: allow agents to read .agents/, ignore .agents/tmp/`
- Added `Read(.agents/**)` to `.claude/settings.json` permissions (subagents need to read notes/specs)
- Added `.agents/tmp` to `.gitignore` so helper scripts don't leak into phase commits

---

## 3. Task List State

See `TaskList` tool output. Summary:
- Completed: Tasks #1–#19 (Phases 0, 1, 2 + 3.1)
- In progress: Task #20 (Phase 3.2 thermodynamics decoupling)
- Pending: Tasks #21–#34 (Phase 3.3, 3.4, 4–6, final review)

---

## 4. Known Concerns / Deviations / Plan Discrepancies

### 4.1 pint_pandas registration (resolved, non-plan addition)

**Issue:** Plan Task 1.2 didn't mention `pint_pandas`. Before Phase 1, `opgee.stream.py` was the sole site with `import pint_pandas`, and any test exercising Energy/Stream accidentally loaded pint_pandas transitively through opgee.config or opgee.log imports. After Phase 0 deletions, test_energy.py imports Energy directly; the `pint[mmBtu / day]` pandas dtype isn't registered and `pd.Series(..., dtype=...)` raises `TypeError: data type 'pint[mmBtu / day]' not understood`.

**Resolution:** Added `import pint_pandas  # noqa: F401  (registers pandas extension dtype for pint[unit])` to `opgee/units.py` (commit `dddf8e4`). User approved. All Energy/Stream usage now works regardless of import path.

### 4.2 Phase 1 gate "both must pass" is aspirational

**Issue:** Plan Task 1.10 says `uv run ruff check .` and `uv run pytest -x -q` "Both must pass." But process.py/stream.py still `from .attributes import ...` (attributes.py deleted Phase 0; Phase 3 fixes). 12 tests fail at collection. 69 ruff errors in opgee/.

**User decision:** Pragmatic — tag gate and continue. Phase 3 will clean up.

### 4.3 TemperaturePressure methods retention

**Issue:** Plan Task 3.1 narrative said "TP unchanged (clean dataclass)" but the code sample dropped `set(T, P)`, `get()`, `copy_from(tp)` methods. 18+ process files + stream.py + test_impute.py call these.

**User decision:** Keep TP methods — avoids ~30 unspec'd call-site updates. `std_pressure` kept at current 14.676 psia (plan had 14.696 which would be a physical-constant change out of scope).

### 4.4 utils.coercible() semantic change

**Issue:** Plan rewrites `coercible(value, pytype, raiseError=True)` (string pytype, raises) → `coercible(value, type_fn, default=None)` (callable, returns default). Existing callers:
- `opgee/core.py:244` used it with string pytype inside the `A` class (A class dropped Phase 3.1 — no longer an issue)
- `opgee/stream.py:712` used `coercible(comp_elt.text, float)` — callable, works with new signature

**Resolution:** New signature adopted. core.py's usage removed via A deletion. Stream.py's usage will be removed in Phase 3.3 (XML parsing stripped).

### 4.5 utils.roundup() semantic change

**Issue:** Plan rewrites `roundup(value, digits)` (round to N decimals using `+0.5` trick) → `roundup(value, nearest)` (round to nearest multiple via `int(nearest * ((v + nearest - 1) // nearest))`). Only caller is `field.py:1697` with `roundup(num_prod_wells * fraction, 0)` — the new signature would divide by zero.

**Status:** Left as-is per plan. field.py is unimportable anyway; Phase 6.1 rewrites field.py. Flagged as latent issue that Phase 6.1 must address (e.g., use `math.ceil` instead).

### 4.6 test_packet.py deleted (spec omission)

**Issue:** `tests/test_packet.py` imported only `from opgee.manager import FieldPacket, _batched`. `manager.py` was in the Phase 0 delete list but `test_packet.py` wasn't. Phase 0.5 implementer deleted it as clean-up.

**Status:** Accepted as a spec-omission fix. Plan could be amended to list it but unnecessary.

### 4.7 SmartDefault decorators stripped in Phase 1.9

**Issue:** `opgee/field.py` had 28 `@SmartDefault.register(...)` decorators that execute at class-body load time. After Phase 0 deletes `smart_defaults.py`, these would fail at module import.

**Resolution (Phase 1.9):** Helper script stripped all 28 decorator lines; the decorated methods remain as bare `def`s in field.py. Those methods are dead code until Phase 6.1 rewrites field.py (which will prune them entirely).

### 4.8 Test infrastructure duplication

**Issue:** Phase 1.7 (table_manager) inlined `_path_to_test_file` in `test_table_manager.py` to bypass the broken utils_for_tests → process.py → attributes.py chain. This duplicates `path_to_test_file` from `utils_for_tests.py`.

**Resolution:** Accept temporary duplication. Phase 6.2 adapts remaining tests — a good time to consolidate. Alternative: remove `ProcA`/`ProcB`/`Before`/`After` from utils_for_tests.py (they're only used by tests that are already broken) to unblock the import chain.

### 4.9 Phase 3.2 thermodynamics scope (open — in progress at handoff)

**Issue:** Task 3.2 requires refactoring 8 classes in 1359-line thermodynamics.py + rewriting 55 tests in test_thermofunction.py. The original implementer prompt (crafted by controller) was interrupted by user before dispatch.

**Next step:** Pick up Task 3.2 with fresh dispatch. See §5.

---

## 5. Resume Instructions

### Where to pick up

1. Task 3.2 (Decouple thermodynamics.py) — currently marked in_progress in task list, no commits yet.
2. The controller had drafted an implementer prompt for Task 3.2 but it was rejected/interrupted before send.

### Task 3.2 dispatch outline

**Goal:** Decouple Oil, Gas, Water, Air, DryAir, AbstractSubstance, ChemicalInfo constructors from the `field` object. Drop WetAir. Replace `field.model.const(...)` with explicit constants or `R_GAS` (from chemistry.py) / `STP.T`, `STP.P` (from core).

**Known field references in thermodynamics.py** (confirmed by grep):
- Line 310: `self.res_tp = TemperaturePressure(field.attr("res_temp"), field.attr("res_press"))` — AbstractSubstance
- Line 312: `self.model = field.model` — AbstractSubstance (drop)
- Line 339: `field.stp.T / field.stp.P` — AbstractSubstance (replace with STP from core)
- Line 363: `self.API = field.attr("API")` — Oil
- Line 366: `self.gas_comp = field.attrs_with_prefix('gas_comp_')` — Oil
- Line 367: `self.gas_oil_ratio = field.attr('GOR')` — Oil
- Line 1242: `self.TDS = field.attr("total_dissolved_solids")` — Water
- Plus Gas/Water body calls `self.model.const("universal-gas-constants")` / `("std-temperature")` / `("std-pressure")` — replace

**Known test fixture values** (from old tests/files/test_model.xml, field "test"):
- `API = 32.8 degAPI`
- `GOR = 2429.30 scf/bbl_oil`
- `res_temp = 200.0 degF`
- `res_press = 1556.6 psia`
- `gas_comp`: N2=2.86, CO2=0.33, C1=89.18, C2=5.3, C3=1.62, C4=0.71, H2S=0.0

**Test expectations to preserve** (sample):
- `test_gas_specific_gravity`: `gas_SG == pytest.approx(0.620513719)` frac
- `test_bubble_point_solution_GOR`: `gor_bubble == pytest.approx(2822.361)` scf/bbl_oil
- `test_reservoir_solution_GOR`: `res_GOR == pytest.approx(291.03397)` scf/bbl_oil

**Suggested model for dispatch:** `opus` — thermodynamics is complex, has nontrivial physics, and test rewrites need careful numeric-value reconstruction. `sonnet` may need multiple re-dispatches.

**Pre-flight checks before dispatching:**
1. Confirm `opgee.chemistry.R_GAS` string-reps as `"joule / kelvin / mole"` (pint canonicalization) — Task 2.1 tests confirmed this.
2. Confirm `opgee.core.STP` importable — Task 2.2 tests confirmed this.
3. Confirm `field.attrs_with_prefix('gas_comp_')` returns what — it's a dict of `A` objects keyed by suffix. Since `A` is dropped, gas_comp will become an explicit `pd.Series` in Oil's constructor.

### Remaining after 3.2

- Task 3.3 strip stream.py (remove XML/parent/enabled; import chemistry constants; add `ctx: FieldContext` param; rename `xml_data` → `initial_data`)
- Task 3.4 Phase 3 gate — ruff + pytest
- Phase 4 (Process base), Phase 5 (51 process subclasses in tiered batches), Phase 6 (Field + final)

Appendix A of the plan lists the 51 process subclasses with tier assignments for Phase 5.

---

## 6. Repository state snapshot

### Tags (in chronological order)
- `phase-0-gate` at `a73fb4f`
- `phase-1-gate` at `f544f0f`
- `phase-2-gate` at `9938f37`

### Commits since plan start (top is newest)
```
1509b6a phase 3: strip core.py to OpgeeObject + TP + STP + dict_from_list + Timer
9938f37 phase 2: create FieldContext with frozen GWPData and SimulationParams  <- phase-2-gate
17e806e phase 2: create chemistry.py with extracted component data
f544f0f phase 1: fix remaining imports of deleted modules                       <- phase-1-gate
3458ec4 phase 1: clean combine_streams.py — stdlib logging, fix header
8c840b8 phase 1: clean table_manager.py — drop OpgeeObject, absorb pkg_utils, drop XML updates
ae0a6a3 phase 1: clean utils.py — strip to 9 utilities, rename getBooleanXML
4c6b5b9 phase 1: clean import_export.py — drop OpgeeObject base and dead logger
ccd9bb9 phase 1: clean emissions.py — drop OpgeeObject base
dddf8e4 phase 1: register pint_pandas in units.py so pint[...] pandas dtype works
e9a0f24 phase 1: clean energy.py — drop OpgeeObject base and dead logger
bf48e35 phase 1: clean units.py — stdlib logging, importlib.resources, drop Qty
3b90730 phase 1: clean error.py — drop 9 unused exception classes
a73fb4f phase 0: bulk delete excluded files, tests, and dependencies           <- phase-0-gate
207f7a1 chore: allow agents to read .agents/, ignore .agents/tmp/
```

### Files touched so far
- **Deleted (Phase 0):** 24 top-level `.py`/`.sh`, `built_ins/` (9 files), `bin/` (7 files), 8 `etc/` files; 21 test files; 17 test data files; `post-proc-plugins/`; later `tests/test_packet.py`.
- **Cleaned (Phase 1):** error.py, units.py, energy.py, emissions.py, import_export.py, utils.py, table_manager.py, combine_streams.py; plus stream.py/process.py/field.py (imports only); 45 processes/*.py (logger only); test_utils.py, test_table_manager.py.
- **Created (Phase 2):** chemistry.py, context.py, test_chemistry.py, test_context.py.
- **Cleaned (Phase 3.1):** core.py, test_core.py.
- **Pending structural work:** thermodynamics.py, stream.py, process.py, field.py, all 51 processes/*.py (per Phase 5 tier assignments in plan Appendix A), remaining tests.

---

## 7. Process tips for the next session

1. **Follow subagent-driven-development discipline:** one implementer per task, then spec-compliance review, then code-quality review, then mark complete in TaskList.
2. **Use `opus` model for complex tasks** (thermodynamics, Field restructure, gas_partition.py, steam_generator.py). Use `sonnet` for mechanical migrations.
3. **Respect the critical rule:** No agent may re-add, re-import, or restore any module/symbol marked DELETE/DROP/REMOVE. Escalate to user before deviating.
4. **Flag plan discrepancies proactively** — the plan has several inconsistencies (see §4). When an agent hits one, they must STOP and escalate instead of silently deviating.
5. **Expect test file rewrites in Phases 3.2, 3.3, 5, 6** — many test fixtures depend on deleted XML loading. Reconstruction is laborious; budget for it.
6. **Phase 5 has parallel dispatch guidance** — Tier 1 (12 files) can run 12 subagents in parallel; Tier 2 has 3 batches of 5–7; Tier 3 runs in pairs/triples.
7. **Phase 5 Appendix B transformation table is authoritative** for `self.attr(...)` → explicit param translations.
