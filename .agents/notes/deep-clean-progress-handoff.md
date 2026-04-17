# OPGEE v5 Deep Clean — Final Handoff (Phase 6 complete)

**Branch:** `refactor/v5-deep-clean`
**Tags at HEAD:** `phase-6-gate`, `STOP`
**Status:** REFACTOR COMPLETE — full suite passing, ruff clean, library ready for next steps. The `STOP` tag marks the session-stop / resume point for the next session.

---

## 1. Final state at `phase-6-gate`

### Acceptance

- `uv run ruff check .` → All checks passed! (0 errors)
- `uv run pytest -v` → 126 passed (2 warnings, 0 failures, 0 errors)
- `import opgee` exposes: `Field, FieldContext, GWPData, Process, SimulationParams, Stream`

### Commits landed in Phase 6

| Commit | Subject |
|---|---|
| (HEAD) | docs: phase 6 gate final handoff (self-consistent post-commit state) |
| `fce975f` | phase 6.4: delete docs/, restore thermosteam-transitive deps (graphviz, pyyaml) |
| `d4c50fa` | docs: phase 6 gate handoff — refactor complete, phase-6-gate tagged |
| `27cfd35` | phase 6.4: final ruff cleanup — delete dead generate_models.py, fix conf.py E402 |
| `51c0675` | phase 6: final cleanup — public API exports, __all__ on processes/, drop dead deps |
| `50e0b17` | phase 6.2: adapt remaining test files for new Field/Process architecture |
| `7420235` | phase 6.1: address code-quality review — drop dead run_after, annotations, docstring |
| `53f68a2` | phase 6: restructure Field — explicit constructor, FieldContext, networkx graph |

### What Phase 6 accomplished

- Phase 6.1: Rewrote `opgee/field.py` end-to-end. New explicit-param constructor. Internal FieldContext build. networkx DiGraph for process scheduling. Graph metadata (cycle_starts, impute_starts) moved from Process to Field. `run()` simplified to zero args — GWP from ctx. `tests/test_field.py` rewritten for direct instantiation (no XML).
- Phase 6.2: Deleted 6 test files entirely (XML-dependent or orchestration-dependent). Trimmed test_emissions.py (removed the test_gwp*/test_use_GWP_error suite — the Analysis class is gone). Deleted tests/utils_for_tests.py (no live importers).
- Phase 6.3: Public API exposed via `opgee/__init__.py` (Field, FieldContext, GWPData, Process, SimulationParams, Stream). Added `__all__` to `opgee/processes/__init__.py` (silenced 46 pre-existing F401 errors). Dropped 12 unused dependencies from pyproject.toml (dash*, dask*, lxml, pydantic-xml, xmlschema, pydantic*, python-dateutil, semver, graphviz, pydot). Initially moved sphinx deps to a `[dependency-groups] docs` group — later dropped entirely when the docs/ directory was deleted.
- Phase 6.4: Deleted dead `scripts/generate_models.py` (used dropped pydantic_xml). Fixed `docs/source/conf.py` E402. Then deleted `docs/` directory entirely (Sphinx docs were a developer convenience for the legacy XML API; they're obsolete for the v5 library). Dropped the `[dependency-groups] docs` sphinx group. Restored `graphviz` and added `pyyaml` as direct deps — both are transitively required by `thermosteam` at import time; the Phase 6.3 "drop unused deps" pass had missed this because `uv sync` didn't prune them until after the docs group was removed.

## 2. Tags (chronological)

`phase-0-gate` → `phase-1-gate` → `phase-2-gate` → `phase-3-gate` → `phase-4-gate` → `phase-5-gate` → **`phase-6-gate`** + **`STOP`** (both on this HEAD commit).

Note: `phase-5-tier-2-complete` was an intermediate milestone tag; the canonical gate tags above are the official ones.

## 3. Public API

```python
from opgee import Field, FieldContext, GWPData, Process, SimulationParams, Stream
```

See `opgee/__init__.py` for the `__all__` declaration.

## 4. Known follow-ups (NOT in scope of Phase 6)

- **Boundary**: deferred — will be redesigned as graph edge cuts rather than process nodes.
- **compute_carbon_intensity**: deferred — CI calculation removed from Field.run(). Will be reimplemented as a separate analysis step.
- **Monte Carlo simulation**: removed. If reintroduced later, it will build on the new Field API.
- **XML/CLI/GUI/plugins**: removed. The library is now a pure importable package — callers build Field objects directly.
- **Documentation**: the legacy `docs/` directory (Sphinx-based, written for the XML-era API) was deleted in Phase 6.4. Any new docs should be rebuilt from scratch for the new library API.
- **Pre-existing latent bugs in migrated processes**: the Phase 5 handoff enumerated several latent bugs (diluent_temp/diluent_temp typo, water_treatment makeup_water_table selection, dead ivars in bitumen_mining, etc.) faithfully preserved. These are out-of-scope cleanup for a correctness pass.

## 5. Full commit history (phase-0-gate..phase-6-gate)

```
(HEAD)  docs: phase 6 gate final handoff (self-consistent post-commit state)   ← phase-6-gate, STOP
fce975f phase 6.4: delete docs/, restore thermosteam-transitive deps (graphviz, pyyaml)
d4c50fa docs: phase 6 gate handoff — refactor complete, phase-6-gate tagged
27cfd35 phase 6.4: final ruff cleanup — delete dead generate_models.py, fix conf.py E402
51c0675 phase 6: final cleanup — public API exports, __all__ on processes/, drop dead deps
50e0b17 phase 6.2: adapt remaining test files for new Field/Process architecture
7420235 phase 6.1: address code-quality review — drop dead run_after, annotations, docstring
53f68a2 phase 6: restructure Field — explicit constructor, FieldContext, networkx graph
d8a6ff2 docs: phase 5 gate handoff (self-consistent post-commit state)
9f91c28 docs: phase 5 gate handoff
c6cc513 phase 5: migrate Tier 3 singles gas_partition.py + steam_generator.py (closes Task 5.3)
b9a53c0 phase 5: migrate Tier 3 Batch I (2 files, 30-32 refs) + exploration TransportEnergy rewire
7bf2a46 phase 5: migrate Tier 3 Batch H (3 files, 24-28 refs)
ea46dfb phase 5: migrate Tier 3 Batch G (3 files, 17-22 refs) + heavy_oil_dilution TransportEnergy rewire
bc5bdee phase 5: migrate Tier 3 Batch F + refactor predict_blower_energy_use (4 files)
69c2a82 phase 5: migrate Tier 3 Batch E (3 files, 14-15 refs)
449ca38 phase 5: migrate Tier 3 Batch D (3 files, 12-13 refs)
4b28c9c docs: mid-phase-5 handoff after Tier 1+2 completion (final session-stop revision)
19f0bbb docs: mid-phase-5 handoff after Tier 1+2 completion (Tier 3 next)
cf3a438 phase 5: migrate Tier 2 Batch C (6 files, 8-11 field refs) + rewire 3 transport callers
4a269cf phase 5: migrate Tier 2 Batch B (7 files, 4-8 field refs)
f5f9344 phase 5: migrate Tier 2 Batch A (7 files, 3-5 field refs)
6a20b23 phase 5: migrate Tier 1 processes (12 files, 0-2 field refs)
00d4d4e docs: phase 4 gate handoff
5aabd26 phase 4: address 4.1 code-quality review (iterating_processes clear, F821 cleanup, type hint fix)
ffacaec phase 4: fix test_processes.py call-site for new get_emission_rates signature
e9ec51b phase 4: restructure Process base — new __init__(name, ctx), drop XML/boundary/enabled
8c531a5 docs: phase 3 gate handoff
2e4d322 phase 3: address 3.3 code-quality review (tests + ctx TODO + CARBON_NUMBER_SERIES move)
a5df80f phase 3: strip stream.py — remove XML, add FieldContext, extract chemistry
7f7e664 docs: add progress handoff for phase 3.2 completion
83978ff phase 3: decouple thermodynamics constructors from field/model
1509b6a phase 3: strip core.py to OpgeeObject + TP + STP + dict_from_list + Timer
9938f37 phase 2: create FieldContext with frozen GWPData and SimulationParams
17e806e phase 2: create chemistry.py with extracted component data
f544f0f phase 1: fix remaining imports of deleted modules
3458ec4 phase 1: clean combine_streams.py — stdlib logging, fix header
8c840b8 phase 1: clean table_manager.py — drop OpgeeObject, absorb pkg_utils, drop XML updates
ae0a6a3 phase 1: clean utils.py — strip to 9 utilities, rename getBooleanXML
4c6b5b9 phase 1: clean import_export.py — drop OpgeeObject base and dead logger
ccd9bb9 phase 1: clean emissions.py — drop OpgeeObject base
dddf8e4 phase 1: register pint_pandas in units.py so pint[...] pandas dtype works
e9a0f24 phase 1: clean energy.py — drop OpgeeObject base and dead logger
bf48e35 phase 1: clean units.py — stdlib logging, importlib.resources, drop Qty
3b90730 phase 1: clean error.py — drop 9 unused exception classes
```

## 6. Tests summary

- `tests/test_field.py` — 6 direct-instantiation tests of the new Field.
- `tests/test_emissions.py` — pure Emissions unit tests (GWP tests removed with Analysis class).
- `tests/test_chemistry`, `test_context`, `test_core`, `test_energy`, `test_import_export`, `test_molecule_names`, `test_stream`, `test_table_manager`, `test_thermofunction`, `test_utils`, `test_shared`, `test_coeff` — all retained and green.

## 7. Session task list

All Phase 6 tasks complete:
- Task 6.1 Restructure Field ✅
- Task 6.2 Adapt remaining tests ✅
- Task 6.3 Final cleanup — public API + dependencies ✅
- Task 6.4 Final verification gate ✅ (this handoff)

**Next-session pending:**
- Final code-reviewer dispatch for the whole refactor (spec-compliance + code-quality on the full `phase-0-gate..phase-6-gate` range), then decide whether to merge the branch to main.

## 8. Files to read at session start (for the next session)

1. **This file** — the handoff.
2. `.agents/docs/plans/2026-04-16-deep-clean-plan.md` — the original plan (skim; refactor is complete, but useful context for the final review).
3. `.agents/docs/specs/2026-04-16-deep-clean-design.md` — the original spec (the review's primary benchmark).
4. `opgee/__init__.py` — the public API surface at HEAD.
5. `opgee/field.py`, `opgee/process.py`, `opgee/stream.py`, `opgee/context.py` — the four central modules to spot-check during the final review.
