# `getBooleanXML` deprecation alias still present

**Severity:** Minor
**Location:** `opgee/utils.py` (alias definition); `tests/test_utils.py:4, 14, 20` (still imports/exercises it)

## Problem
`getBooleanXML` is retained as a deprecated alias for `parse_boolean`. The transition window is past — XML is gone, there are no external callers.

## Suggested fix
Delete the alias; rename the test imports to `parse_boolean` and remove the alias-specific test cases.
