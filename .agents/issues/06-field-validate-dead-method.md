# `Field.validate()` is a dead method

**Severity:** Important (dead public method)
**Location:** `opgee/field.py:781-805`

## Problem
`Field.validate()` is never called from anywhere (grep confirmed). It iterates processes calling `getattr(proc, "validate", None)` — no process defines `validate()`. It also re-runs `_check_run_after_procs`, duplicating the check already run at `__init__` time (`field.py:189`).

## Suggested fix
Either wire `Field.validate()` into `Field.run()` as a defensive pre-flight, or delete the method.
