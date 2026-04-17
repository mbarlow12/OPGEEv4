# Issues — post-Phase-6 code review

Issues surfaced by the final `phase-0-gate..phase-6-gate` code review (2026-04-17).
All items below were found AFTER the refactor's acceptance gate (ruff clean, 126 tests pass, public API imports cleanly). None are critical; the verdict is "merge with fixes."

## Important (correctness / dead-public-API)

- [01](01-process-notimplementederror-stub.md) — Dead `NotImplementedError` stub on `Process` base class
- [02](02-imputation-silently-disabled.md) — **Imputation silently disabled via dropped `has_exogenous_data`** (real correctness bug)
- [03](03-thin-process-subclass-test-coverage.md) — Thin test coverage of new Field/Process API
- [04](04-iterating-processes-module-global.md) — `_iterating_processes` module-global violates spec §3.1
- [05](05-stream-ctx-write-only.md) — `Stream.ctx` is a write-only attribute
- [06](06-field-validate-dead-method.md) — `Field.validate()` is dead
- [07](07-field-check-balances-unused-hook.md) — `Field.check_balances()` hook has no implementers

## Minor (cleanup / polish)

- [08](08-process-dead-ivars.md) — Dead ivars on every Process (`desc`, `extend`, `iteration_count`)
- [09](09-stream-hydrocarbons-property-unused.md) — `Stream.hydrocarbons` property unused
- [10](10-process-required-inputs-outputs-unused.md) — `required_inputs`/`required_outputs` unused
- [11](11-getbooleanxml-alias-lingering.md) — `getBooleanXML` deprecation alias lingering
- [12](12-test-shared-empty-placeholder.md) — `tests/test_shared.py` empty placeholder
- [13](13-field-accessor-duplication.md) — Redundant `Field.all_processes` alias
- [14](14-field-process-data-wrappers.md) — Dead `save_process_data`/`get_process_data` wrappers
- [15](15-process-intermediate-results-deviation.md) — Minor spec deviations (inputs/outputs naming, unused `IntermediateValues`)
- [16](16-core-std-pressure-value.md) — `std_pressure` = 14.676 psia (non-standard)
- [17](17-processes-subpackage-not-reexported.md) — `opgee.processes` split from top-level API undocumented
- [18](18-core-timer-unused.md) — `Timer` class unused
- [19](19-field-stp-redundant.md) — `Field.stp` duplicates `Field.ctx.stp`
- [20](20-chemistry-table-load-at-import.md) — PubChem CID table loaded at import time

## Planned follow-up workflow

Per user direction, the path to merge is:

1. **Add legacy OPGEE repo as a reference worktree/submodule.**
2. **Test-parity pass** — port/adapt pre-refactor tests that still make sense under the new API. Restores baseline coverage for the 51 subclass migrations. See [issue 03](03-thin-process-subclass-test-coverage.md).
3. **New-architecture test pass** — add tests for primitives the refactor introduced (cyclic-graph convergence, impute path, end-to-end `field.run()`).
4. Address Important issues 01, 02, 04–07 (most are small).
5. Batch-close Minor issues (08–20) in a cleanup commit or two.
6. Merge to `main`.
