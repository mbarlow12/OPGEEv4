# `Timer` class in `core.py` is unused

**Severity:** Minor
**Location:** `opgee/core.py:70-98`

## Problem
`Timer` was retained during the phase 3 strip of `core.py` but has no live callers in the stripped library.

## Suggested fix
Delete the class. If profiling primitives become useful later, re-add with an intentional design.
