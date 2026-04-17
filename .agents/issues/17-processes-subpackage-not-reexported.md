# `opgee.processes` not re-exported from top-level package

**Severity:** Minor (documentation / API decision)
**Location:** `opgee/__init__.py` vs `opgee/processes/__init__.py`

## Problem
The top-level `opgee` package exports 6 core names (Field, FieldContext, GWPData, Process, SimulationParams, Stream). Users wanting a concrete process must do `from opgee.processes import Drilling`. This is a defensible split but currently undocumented.

## Suggested fix
Make the split explicit in a future README/docstring: "library API" lives at `opgee.*`, "process catalog" lives at `opgee.processes.*`. Alternatively, re-export all 46 concrete processes from `opgee/__init__.py` — pick one.
