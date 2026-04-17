# `_iterating_processes` is a module-global mutated by staticmethods

**Severity:** Important
**Location:** `opgee/process.py:37, 466-493`

## Problem
Iteration tracking uses a module-level list, registered via `Process.register_iterating_process(process)` (staticmethod) and cleared via `Process.reset_all_iteration()` (staticmethod). Two Field instances in the same Python process share this global. If a user builds `field_a` and `field_b` and runs them back-to-back without manually calling `reset_all_iteration()`, the second run's convergence check sees processes from the first. Violates spec §3.1 "children don't know their parent" more severely than the old `self.field` did. The in-file TODO `# TODO(phase 6.1): Move ownership of iterating-process tracking to Field.` acknowledges this but Phase 6.1 closed without the move.

## Suggested fix
Move `_iterating_processes` onto `Field` as an instance attribute. Pass registration through `ctx` (or a callback stored on ctx). This is where the "`ctx.process_data` as bulletin board" pattern should generalize.

## Notes
Worth fixing before Monte Carlo re-introduction — MC will almost certainly run multiple Fields in one process.
