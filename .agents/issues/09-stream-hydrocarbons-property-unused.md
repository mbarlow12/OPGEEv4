# `Stream.hydrocarbons` property is unused

**Severity:** Minor
**Location:** `opgee/stream.py:540-542`

## Problem
`@property hydrocarbons` returns the module-level `HYDROCARBONS` constant. No caller uses it (grep confirmed).

## Suggested fix
Delete the property. Callers that need the list can import `HYDROCARBONS` directly.
