# `chemistry.py` loads PubChem CID table at import time

**Severity:** Minor
**Location:** `opgee/chemistry.py:51-52`

## Problem
Module-level side effect: `_mgr = TableManager(); _pubchem_cid_df = _mgr.get_table("pubchem-cid")`. Because `chemistry` is imported during `import opgee`, every downstream consumer (and every test) pays this table-load cost eagerly.

## Suggested fix
Lazy-load: wrap the table fetch in a module-level `@functools.cache` accessor (e.g. `get_pubchem_cid_df()`) and call it from consumers. Keeps the API clean while deferring I/O.
