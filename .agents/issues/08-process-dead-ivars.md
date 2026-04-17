# Dead ivars on every Process instance

**Severity:** Minor
**Location:** `opgee/process.py:119-121, 141`

## Problem
`self.desc`, `self.extend`, and `self.iteration_count` are set (and `iteration_count` reset) on every Process but never read anywhere in the codebase.

## Suggested fix
Remove from `Process.__init__` and from the reset path.
