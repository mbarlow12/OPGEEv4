# `Field.check_balances()` invokes a hook no process implements

**Severity:** Important (dead hook)
**Location:** `opgee/field.py:370-379`

## Problem
`Field.check_balances()` (called from `Field.run()`) iterates processes and calls `check_balances()` on any that define it. Grep confirms zero process implementations. The docstring is transparent about this, but it's still dead dispatch on every `run()` call.

## Suggested fix
Either delete `Field.check_balances()` (and the call from `Field.run()`), or land an actual implementation in at least one representative process and wire it.
