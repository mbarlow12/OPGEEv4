# Deep Clean Analysis: `opgee/units.py`

**Status**: INCLUDED (with modifications)

## Symbol Inventory

### Module-level imports

| Symbol | Source | Verdict |
|---|---|---|
| `Final, Optional` | `typing` | RETAIN |
| `pint` | `pint` | RETAIN |
| `ApplicationRegistry` | `pint.registry` | RETAIN |
| `OpgeeException` | `opgee.error` | RETAIN (no transitive deps) |
| `getLogger` | `opgee.log` | **DROP** -- `log.py` imports `config.py` at module level, creating a transitive config dependency |
| `resourceStream` | `opgee.pkg_utils` | **DROP** -- replaced by `importlib.resources` inline |

### Module-level variables

| Symbol | Kind | Verdict | Notes |
|---|---|---|---|
| `_logger` | `logging.Logger` | **DROP** -- only consumer is `validate_unit()` warning; replace with stdlib `logging.getLogger` |
| `_ureg` | `ApplicationRegistry` (temporary) | RETAIN (initialization logic) | Deleted after setup; only exists during module init |
| `ureg` | `Final[ApplicationRegistry]` | **RETAIN** | Core export; used in 41 files / 228 occurrences across the package |
| `Qty` | `pint.Quantity` alias | **DROP** | Assigned but never imported anywhere (0 external usages) |
| `_undefined_units` | `dict` | RETAIN | Used by `validate_unit()`; accessed in `tests/test_core.py` |

### Functions

| Symbol | Verdict | Notes |
|---|---|---|
| `validate_unit(unit)` | **RETAIN** | Used in `core.py` and `attributes.py` for attribute unit validation |
| `magnitude(value, units=None)` | **RETAIN** | Used in 7 modules (`emissions.py`, `stream.py`, `core.py`, `analysis.py`, `process.py`, `attributes.py`); 20 total occurrences |

## Required Modifications

### 1. Replace `pkg_utils.resourceStream` with `importlib.resources`

The current initialization loads `etc/units.txt` via `pkg_utils.resourceStream`, which uses the deprecated `pkgutil.get_data`. Replace with `importlib.resources` directly:

```python
from importlib.resources import files

_units_text = files("opgee.etc").joinpath("units.txt").read_text()
_lines = [line.strip() for line in _units_text.splitlines()]
_ureg.load_definitions(_lines)
```

**Prerequisite**: `opgee/etc/` must become a package (add `__init__.py`) or use `files("opgee") / "etc" / "units.txt"`. Since `etc/` is a data directory (not a Python package), the preferred approach is:

```python
from importlib.resources import files

_units_text = (files("opgee") / "etc" / "units.txt").read_text()
```

This works with `importlib.resources` as of Python 3.9+ using the `Traversable` API and does **not** require `etc/__init__.py` -- it only requires the data to be included as package data (already ensured by `MANIFEST.in`'s `graft opgee/etc`).

### 2. Replace `opgee.log.getLogger` with stdlib `logging.getLogger`

The only usage of `_logger` is a single warning in `validate_unit()`. Replace:

```python
# Before
from opgee.log import getLogger
_logger = getLogger(__name__)

# After
import logging
_logger = logging.getLogger(__name__)
```

This eliminates the transitive dependency chain: `units.py` -> `log.py` -> `config.py`.

### 3. Remove `Qty` alias

`Qty = _ureg.Quantity` is assigned at line 23 but has zero external consumers. Remove it.

## Dependency Graph (current)

```
units.py
  -> pint                  (KEEP)
  -> opgee.error           (KEEP - standalone)
  -> opgee.log             (DROP - pulls in config.py)
     -> opgee.config       (DROP target)
  -> opgee.pkg_utils       (DROP - replaced by importlib.resources)
```

## Dependency Graph (after clean)

```
units.py
  -> pint                  (external)
  -> logging               (stdlib)
  -> importlib.resources   (stdlib)
  -> opgee.error           (internal, standalone)
```

## Summary

| Category | Symbols |
|---|---|
| **RETAIN as-is** | `ureg`, `_undefined_units`, `validate_unit()`, `magnitude()` |
| **RETAIN with mods** | `_logger` (switch to stdlib), module init block (switch to `importlib.resources`) |
| **DROP** | `Qty`, `opgee.log.getLogger` import, `opgee.pkg_utils.resourceStream` import |

The file is small (73 lines) and almost entirely retainable. The two changes are surgical: swap the resource-loading mechanism and the logger source, both removing config.py from the import chain.
