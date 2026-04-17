# Redundant `Field.all_processes` alias

**Severity:** Minor
**Location:** `opgee/field.py:282-292`

## Problem
`Field` exposes `streams()`, `processes()`, and `all_processes = processes` "for API compatibility." The library is brand-new with no external callers needing compatibility.

## Suggested fix
Drop the `all_processes` alias. Keep a single canonical accessor.
