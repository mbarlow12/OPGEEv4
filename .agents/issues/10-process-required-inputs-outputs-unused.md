# `Process.required_inputs()` / `required_outputs()` unused

**Severity:** Minor
**Location:** `opgee/process.py:150-160`; subclass class-vars `_required_inputs` / `_required_outputs` in many `opgee/processes/*.py` files

## Problem
Many subclasses still populate class-level `_required_inputs` / `_required_outputs`, and Process exposes `required_inputs()` / `required_outputs()` accessors — but nothing reads them. The `validate_streams` check that once consumed them was removed in Phase 4.

## Suggested fix
Either wire these into a runtime pre-flight check in `Field.run()`, or delete both the accessors and the subclass class-var assignments.
