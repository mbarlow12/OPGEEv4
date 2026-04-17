# `std_pressure` uses non-standard literature value

**Severity:** Minor (possible pre-existing, worth confirming)
**Location:** `opgee/core.py:49`

## Problem
`std_pressure = ureg.Quantity(14.676, "psia")`. Standard values are 14.696 psia (IUPAC/NIST), 14.7 (rounded engineering), or 1 atm exactly. 14.676 matches no convention the reviewer knew; the spec examples even show 14.696.

## Suggested fix
Check git history / original intent. If intentional, add a brief comment citing the source. If a typo, fix to 14.696.
