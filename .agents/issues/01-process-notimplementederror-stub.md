# Dead NotImplementedError stub on Process base class

**Severity:** Important
**Location:** `opgee/process.py:284-296`

## Problem
`Process.get_compressor_and_well_loss_rate` raises `NotImplementedError` with comment "TODO(phase 5): wiring deferred to Phase 5 subclass migration." Phase 5 is closed. The four subclasses the TODO names have all been migrated to use explicit `loss_rate` constructor params + `self.set_gas_fugitives()`. Grep confirms the method is never called anywhere. It is dead, public, broken, and misleading on the library's base class.

## Suggested fix
Delete the method and its comment block.
