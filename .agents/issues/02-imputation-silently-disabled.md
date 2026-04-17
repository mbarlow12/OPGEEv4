# Imputation silently disabled via dropped `has_exogenous_data`

**Severity:** Important (real correctness bug)
**Location:** `opgee/field.py:315` (`find_start_streams`)

## Problem
`find_start_streams` does `return [s for s in self.stream_dict.values() if getattr(s, "has_exogenous_data", False)]`. The spec §4.3 dropped `has_exogenous_data` from Stream and no code anywhere sets it — grep confirms zero setters. Result: this helper always returns `[]`. When a Field is built without passing `impute_start=`, `_impute()` finds no start streams and imputation is silently skipped. Users with realistic fields (`Separation`, `ReservoirWellInterface`, `DownholePump` all have live `impute()` methods) will get broken pipelines with no error. The docstring at `field.py:108-109` acknowledges the problem but ships it anyway.

## Suggested fix
One of:
- Drop the `has_exogenous_data` pathway entirely; require `impute_start=` and document it; or
- Promote `has_exogenous_data` to a first-class Stream constructor arg so callers can flag exogenous streams.
