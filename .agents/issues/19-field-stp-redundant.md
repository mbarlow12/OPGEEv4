# `Field.stp` duplicates `Field.ctx.stp`

**Severity:** Minor
**Location:** `opgee/field.py:124` (and ctx assignment)

## Problem
`Field.__init__` sets both `self.stp = STP` and `self.ctx.stp = STP`. All callers use `self.ctx.stp` — `self.stp` is redundant.

## Suggested fix
Drop `self.stp` from Field. Use `self.ctx.stp` exclusively.
