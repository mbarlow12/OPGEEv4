# OPGEE v5 Deep Clean — Progress Handoff (2026-04-17)

**Branch:** `refactor/v5-deep-clean`
**Plan:** `.agents/docs/plans/2026-04-16-deep-clean-plan.md`
**Spec:** `.agents/docs/specs/2026-04-16-deep-clean-design.md`
**Previous handoff:** `.agents/notes/2026-04-16-deep-clean-progress-handoff.md` (Phases 0, 1, 2, and 3.1)
**Execution mode:** `superpowers:subagent-driven-development` — TaskList + dispatched implementer / spec-reviewer / code-quality-reviewer per task

---

## 1. What changed since the 2026-04-16 handoff

### Phase 3.2 landed ✅

**Commit:** `83978ff` — "phase 3: decouple thermodynamics constructors from field/model"
**Parent:** `1509b6a` (Phase 3.1 core strip)
**Files:** `opgee/thermodynamics.py` (+56/-64), `opgee/chemistry.py` (+6), `tests/test_thermofunction.py` (+35/-31)
**Reviews:** spec-compliance ✅, code-quality ✅ (approved, minor follow-up suggestions only)

What was done:
- Dropped `OpgeeObject` base from `ChemicalInfo`, `Air`, `AbstractSubstance` (and transitively subclasses)
- Deleted `WetAir` class entirely
- New constructor signatures (no `field` arg):
  - `Air(composition: list[tuple[str, float]])`
  - `DryAir()` — composition hardcoded
  - `AbstractSubstance(res_temp, res_press)`
  - `Oil(API, gas_comp, gas_oil_ratio, res_temp, res_press, TDS)` — `gas_comp` is `pd.Series[pint[mol_pct]]`
  - `Gas(res_temp, res_press)`
  - `Water(res_temp, res_press, TDS)`
- Three `self.model.const(...)` call sites replaced: `"universal-gas-constants"` → `R_GAS` (imported from chemistry); `"std-temperature"` → `STP.T`; `"std-pressure"` → `STP.P`
- Line 339's `field.stp.T/P` replaced with module-level `STP.T/P`
- `ChemicalInfo.__init__` now reads `GASES` and `PUBCHEM_CID_DF` from `opgee.chemistry` — the coupling to `Stream.non_hydrocarbon_gases` / `Stream.pubchem_cid_df` is gone
- `opgee/chemistry.py` gained a public `PUBCHEM_CID_DF: pd.DataFrame = _pubchem_cid_df` re-export (+ `import pandas as pd`)
- Test fixtures rewritten to construct Oil/Gas/Water directly — no more `test_model` fixture dependency. Historical XML values preserved:
  ```
  API=32.8 degAPI, GOR=2429.30 scf/bbl_oil, res_temp=200.0 degF,
  res_press=1556.6 psia, TDS=5000.0 mg/L
  gas_comp = pd.Series({N2:2.86, CO2:0.33, C1:89.18, C2:5.3, C3:1.62,
                        C4:0.71, H2S:0.0}, dtype="pint[mol_pct]")
  ```
- `test_check_balance` (out-of-scope Process test) deleted from `test_thermofunction.py`
- PHASE_* import in test file switched from `.stream` to `.chemistry`

### Verification

Phase 3.2 could not run `pytest tests/test_thermofunction.py` because `opgee/stream.py` still imports the deleted `attributes` module (that's Phase 3.3's job). Instead:
- AST-parse clean on both modified Python files
- `ruff check opgee/thermodynamics.py opgee/chemistry.py tests/test_thermofunction.py` → zero errors
- Regression: 39/39 pass on `test_chemistry test_context test_core test_utils test_energy test_import_export test_table_manager`

### Code-quality review follow-ups (not blocking, not yet addressed)

Captured here so Phase 3.3+ or a later cleanup can pick them up:

1. **Duplicate `TemperaturePressure` in `test_thermofunction.py`** — `RES_PRESS = 1556.6 psia` (reservoir) vs `test_tp = ...1556.0 psia` (stream). Historical divergence, documented as intentional. Worth a one-line comment in the test file to pre-empt confusion.
2. **`Oil.__init__` composition** — constructs `self.water = Water(...)` internally. Pre-existing pattern, unchanged by 3.2. Candidate for constructor injection (`Oil(..., water: Water)`) in Phase 6.1 when Field wiring is rewritten.
3. **`DryAir` singleton** — now parameter-free, so every instance allocates a redundant copy. A `@functools.cache` classmethod or module-level singleton would fix this — pre-existing TODO on `AbstractSubstance.__init__` already flags it.
4. **`PUBCHEM_CID_DF` docstring** — currently says "for use by `thermodynamics.ChemicalInfo`". Should describe the dataframe's contents instead (DataFrame indexed by hydrocarbon name with PubChem CIDs). Nit.

---

## 2. Current TaskList state

Generated from `TaskList` at handoff time. Task IDs do not match plan section numbers — they're TaskList internal IDs.

| TaskList ID | Status | Subject |
|---|---|---|
| #1 | ✅ completed | Phase 3.2: Decouple thermodynamics.py from field/model |
| #2 | 🔄 in_progress | **Phase 3.3: Strip stream.py — remove XML/parent/enabled, add ctx** ← resume here |
| #3 | pending | Phase 3.4: Verification gate — Phase 3 (run ruff + pytest, tag `phase-3-gate`, write `.agents/notes/<date>-phase-3-handoff.md`) |
| #4 | pending | Phase 4.1: Restructure Process base class |
| #5 | pending | Phase 4.2: Verification gate — Phase 4 (+ handoff doc) |
| #6 | pending | Phase 5.1: Tier 1 — migrate 12 simple processes (parallel) |
| #7 | pending | Phase 5.2: Tier 2 — migrate 20 medium processes (3 batches) |
| #8 | pending | Phase 5.3: Tier 3 — migrate 19 complex processes (small batches) |
| #9 | pending | Phase 5.4: Refactor processes/shared.py `predict_blower_energy_use` |
| #10 | pending | Phase 5.5: Verification gate — Phase 5 (+ handoff doc) |
| #11 | pending | Phase 6.1: Restructure Field class |
| #12 | pending | Phase 6.2: Adapt remaining test files |
| #13 | pending | Phase 6.3: Final cleanup — public API + dependencies |
| #14 | pending | Phase 6.4: Final verification gate (+ final handoff doc) |
| #15 | pending | Final code-reviewer dispatch for entire deep clean |

**Process note (new as of 2026-04-17):** every verification-gate task now includes a step to write a dated handoff markdown doc in `.agents/notes/`. Memory entry: `feedback_phase_gate_handoffs.md`. Pattern file for depth/style: `.agents/notes/2026-04-16-deep-clean-progress-handoff.md` + this file.

---

## 3. Resume point: Task 3.3 — strip `opgee/stream.py`

### Why this is next

Three consequences cascade from 3.2:
1. `opgee/stream.py` still has `from .attributes import AttributeMixin` — so *every* downstream import chain is broken at collection time. `tests/test_thermofunction.py` (just rewritten) can't be exercised until 3.3 lands.
2. Stream was the historical home of `PHASE_*`, `non_hydrocarbon_gases`, `pubchem_cid_df`, `VOCs`, `component_names`, `carbon_number` — all now owned by `opgee/chemistry.py`. Stream should import from chemistry, not duplicate.
3. Phase 4 restructures `Process` to take a `FieldContext` ctor arg. For `Process` subclasses to construct Streams cleanly, `Stream.__init__` needs the same `ctx` arg ready to go.

### What to do (summary — the authoritative spec is `.agents/notes/2026-04-16-deep-clean-stream.md`)

1. **Drop base classes**: remove `AttributeMixin` and `XmlInstantiable` inheritance. `Stream` becomes a standalone class.
2. **Drop `from_xml` classmethod** (stream.py lines 669–743 — ~75 lines of XML parsing).
3. **Drop `children()`, `validate()`, `extend_components()`** (lines 237–241, 262–290) — all either no-op or config-driven.
4. **Drop `_extensions` class variable**, `self.has_exogenous_data`, `self.enabled`, `self.parent`, `self.field`.
5. **Inline `self.name = name`** directly in `__init__` (no `XmlInstantiable.__init__` call).
6. **Rename `self.xml_data` → `self.initial_data`** (reset pattern stays, just drop XML branding).
7. **Update `to_dataframe()`** (lines 195–235) — it currently does `self.parent.name`. Replace with a constructor-passed field name, or drop the `'field'` column entirely until Phase 6 decides. Keep the method for now.
8. **Import chemistry data** from `opgee.chemistry` instead of re-defining at class level: `PHASE_*`, `GASES`, `HYDROCARBONS`, `VOCS`, `CARBON_NUMBER`, `COMPONENT_NAMES`, `SOLIDS`, `LIQUIDS`, `OTHER`. Delete the class-body TableManager lookup (lines 92–140 in current file).
9. **Replace `from .log import getLogger`** → stdlib `logging` (already imported `import logging` exists on line 20 — just delete the dead `from .log` remnants if any).
10. **Drop `from .utils import getBooleanXML, coercible`** and `from .core import XmlInstantiable, elt_name` — both only used by `from_xml` which is being deleted.
11. **Add `ctx: FieldContext` to `__init__`** (plan Task 3.3 step 2) — wire it into the existing Stream state. Also add `contents: list[str] | None` as explicit kwarg (already exists — just type it).

### New `__init__` signature (target)

```python
from .context import FieldContext

class Stream:
    def __init__(
        self,
        name: str,
        tp: TemperaturePressure,
        ctx: FieldContext | None = None,
        *,
        API: pint.Quantity | None = None,
        comp_matrix: pd.DataFrame | None = None,
        src_name: str | None = None,
        dst_name: str | None = None,
        contents: list[str] | None = None,
        impute: bool = True,
    ): ...
```

`ctx` is default-None to keep `test_thermofunction.py`'s bare `Stream("test_stream", tp)` and `Stream("test_stream", test_tp)` constructions working — Oil/Gas/Water internal Stream usage (e.g., `Stream("test_stream", self.res_tp)` at thermodynamics.py:520) doesn't need a `ctx`. Field in Phase 6.1 will always pass a real `ctx`.

### Tests to update

- **`tests/test_stream.py`** is currently broken multiple ways (references `load_test_model` which doesn't exist in the current `utils_for_tests.py`, uses `configure_logging_for_tests` fixture which doesn't exist, exercises `field.find_stream` / `proc.find_output_stream`). This file needs significant rewrite:
  - The `test_carbon_number` function (lines 44–49) is self-contained and should pass as-is (maybe needs import path fix — `is_carbon_number` is still exported from stream.py OR should move to testing `opgee.chemistry.is_carbon_number`).
  - The `test_stream_utils` function (lines 126–138) constructs a Stream directly with `Stream('stream1', tp)` — that stays easy.
  - `test_find_stream`, `test_initialization`, `test_combustion_stream` depend on a loaded `stream_model` from XML — these should be **deleted** (Process-level find-stream tests will be rewritten under Phase 6.2 against the new Field API).
- **`tests/test_molecule_names.py`** — need to verify it still imports cleanly after 3.3. If it imports PHASE_* / is_carbon_number from stream, switch to chemistry.
- **`tests/test_thermofunction.py`** — unchanged by 3.3, but should now be runnable. Run as part of verification.

### Verification

- `uv run ruff check opgee/stream.py tests/test_stream.py tests/test_thermofunction.py tests/test_molecule_names.py`
- `uv run pytest tests/test_stream.py tests/test_molecule_names.py tests/test_thermofunction.py -x -v` — expect **all tests pass** (this is the first time thermofunction runs in the new regime; 55 test assertions to verify)
- Regression: the 39-test green subset from 3.2 must still pass

### Commit message

```
phase 3: strip stream.py — remove XML, add FieldContext, extract chemistry
```

---

## 4. Key repository state (unchanged since 2026-04-16 unless noted)

### Tags
- `phase-0-gate` → `a73fb4f`
- `phase-1-gate` → `f544f0f`
- `phase-2-gate` → `9938f37`
- (Phase 3 gate pending — tag after Task 3.3 lands and all of Phase 3 is green)

### Commits since plan start (newest first)
```
83978ff phase 3: decouple thermodynamics constructors from field/model       ← new since last handoff
1509b6a phase 3: strip core.py to OpgeeObject + TP + STP + dict_from_list + Timer
9938f37 phase 2: create FieldContext with frozen GWPData and SimulationParams  ← phase-2-gate
17e806e phase 2: create chemistry.py with extracted component data
f544f0f phase 1: fix remaining imports of deleted modules                      ← phase-1-gate
3458ec4 phase 1: clean combine_streams.py — stdlib logging, fix header
8c840b8 phase 1: clean table_manager.py — drop OpgeeObject, absorb pkg_utils, drop XML updates
ae0a6a3 phase 1: clean utils.py — strip to 9 utilities, rename getBooleanXML
4c6b5b9 phase 1: clean import_export.py — drop OpgeeObject base and dead logger
ccd9bb9 phase 1: clean emissions.py — drop OpgeeObject base
dddf8e4 phase 1: register pint_pandas in units.py so pint[...] pandas dtype works
e9a0f24 phase 1: clean energy.py — drop OpgeeObject base and dead logger
bf48e35 phase 1: clean units.py — stdlib logging, importlib.resources, drop Qty
3b90730 phase 1: clean error.py — drop 9 unused exception classes
a73fb4f phase 0: bulk delete excluded files, tests, and dependencies          ← phase-0-gate
207f7a1 chore: allow agents to read .agents/, ignore .agents/tmp/
```

### Known still-broken files (expected; Phase 3.3+ fixes)
- `opgee/stream.py` — `from .attributes import AttributeMixin` (fixed by 3.3)
- `opgee/process.py` — `from .attributes import AttributeMixin` + other XML imports (fixed by 4.1)
- `opgee/field.py` — still has many deleted-module imports + dead SmartDefault-decorated methods (fixed by 6.1)
- Any test that uses `utils_for_tests.load_test_model` or `configure_logging_for_tests` — will be cleaned in 6.2

---

## 5. Open concerns / deviations tracker

Carries forward from `2026-04-16-deep-clean-progress-handoff.md` §4, plus:

- **4.10 (new) — `Stream` data expected by chemistry.py**: 3.2 added `PUBCHEM_CID_DF` public export. Phase 3.3 will need to delete the class-level `pubchem_cid_df = mgr.get_table(...)` and `non_hydrocarbon_gases = _gases = [...]` from `Stream` body (they moved to chemistry). The only stream-external reader of `Stream.pubchem_cid_df` was `ChemicalInfo` (fixed in 3.2). `Stream.non_hydrocarbon_gases` currently has no external reader either — grep'd opgee/ and tests/, no hits.
- **4.11 (new) — `test_tp = 1556.0 psia` in `test_thermofunction.py`** — flagged by code-quality review; intentional historical divergence from `RES_PRESS = 1556.6`. Consider adding a one-line clarifying comment in the test file during Phase 3.3 verification, since test_thermofunction is going to be touched when pytest is finally run against it.

All prior §4 items from 2026-04-16 still apply — read that file too.

---

## 6. Process tips for the next session

1. **Activate `superpowers:subagent-driven-development`** first. Dispatch fresh implementer subagent for each task — don't pile work onto one subagent.
2. **Use `opus` for complex work** (stream.py is complex — 748 lines, interlocking with Process/Field). Use `sonnet` for mechanical pattern migrations.
3. **Two-stage review discipline**: spec-compliance review first, then code-quality review. Don't skip either.
4. **Respect the critical rule**: no re-adding deleted modules/symbols. Every implementer prompt must restate this.
5. **Dogfood the handoff discipline** — after Phase 3.4 (and 4.2, 5.5, 6.4), write an updated handoff doc dated at the gate-tag date.
6. **Pre-dispatch pre-flight checks for 3.3**:
   - Confirm `opgee.chemistry` exports everything stream needs: `GASES`, `HYDROCARBONS`, `VOCS`, `CARBON_NUMBER`, `COMPONENT_NAMES`, `SOLIDS`, `LIQUIDS`, `OTHER`, `PHASE_*`, `PUBCHEM_CID_DF`. It already does — verified in 3.2.
   - Check whether any surviving file still imports `Stream.pubchem_cid_df` or `Stream.non_hydrocarbon_gases`. Grep says none. Good.
   - Confirm `combine_streams.py` still only uses static methods on Oil/Gas/Water (verified in 3.2 code-quality review).

---

## 7. Files to read at session start (in order)

1. `.agents/docs/plans/2026-04-16-deep-clean-plan.md` — the plan (skim, then read Task 3.3 section)
2. `.agents/notes/2026-04-16-deep-clean-progress-handoff.md` — the prior handoff (contains §4 deviation tracker not duplicated here)
3. **This file** — for what's new
4. `.agents/notes/2026-04-16-deep-clean-stream.md` — authoritative symbol-level proposal for stream.py
5. `opgee/stream.py` — read in full
6. `opgee/chemistry.py` — so you know what's already exported
7. `opgee/context.py` — for the `FieldContext` type that stream's `ctx` param will reference
8. `tests/test_stream.py`, `tests/test_molecule_names.py` — for the test rewrite scope
