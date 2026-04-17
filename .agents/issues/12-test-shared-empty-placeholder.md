# `tests/test_shared.py` is an empty placeholder

**Severity:** Minor
**Location:** `tests/test_shared.py` (1-byte file, single newline)

## Problem
File was created as a placeholder and never grew content.

## Suggested fix
Either delete the file, or populate it with real tests for the helpers in `opgee/processes/shared.py` (e.g. `predict_blower_energy_use`, `get_energy_carrier`, `get_bounded_value`). These helpers are live and currently uncovered — natural candidates during the planned test-parity pass.
