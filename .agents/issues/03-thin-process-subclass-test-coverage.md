# Thin test coverage of new Field/Process API

**Severity:** Important
**Location:** `tests/` (overall suite)

## Problem
126 tests is honest but front-loaded: `test_thermofunction.py` is 54 tests (43%). Zero tests instantiate any of the 51 migrated `Process` subclasses through their new typed constructors. The `self.attr("x")` → explicit constructor param migration was the biggest surface-area change in the refactor and is entirely unexercised. `test_field.py` has 6 tests but all use trivial `StubProc`/`SinkProc`; no real subclass graph runs end-to-end. No test exercises cyclic convergence (`OpgeeIterationConverged`, `OpgeeMaxIterationsReached`), `_impute()`, `_depends_on_cycle`, or `Field.get_component_fugitive` (~120 lines).

## Suggested fix
Planned workflow per the user:
1. Add the legacy OPGEE repo as a reference worktree/submodule.
2. **Test-parity pass:** port or adapt pre-refactor tests that still make sense under the new API. This restores coverage baseline for the 51 subclass migrations.
3. **New-architecture test pass:** add targeted tests for the refactor's new primitives — cyclic-graph convergence driving one real process, an impute-path test, and an integration test building a field with 5–6 real migrated processes and running `field.run()`.

## Notes
This is the #1 follow-up before merging to `main` with confidence.
