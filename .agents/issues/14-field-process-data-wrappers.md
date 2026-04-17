# `Field.save_process_data` / `get_process_data` are dead wrappers

**Severity:** Minor
**Location:** `opgee/field.py:320-333`

## Problem
These methods wrap direct dict access on `self.ctx.process_data`. All 51 migrated processes use `self.ctx.process_data[...]` directly; nothing calls the Field-level wrappers.

## Suggested fix
Delete both methods. The `ctx.process_data` dict is the canonical "bulletin board" per the spec.
