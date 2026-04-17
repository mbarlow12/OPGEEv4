# Deep Clean Proposal: `opgee/table_manager.py`

**Status**: INCLUDED (with changes -- absorb resource-loading from `pkg_utils.py`)

## Purpose

Loads and caches built-in CSV data tables (in `opgee/tables/`) into pandas DataFrames.
Process implementations look up emission factors, thermodynamic data, transport parameters,
etc. via `TableManager.get_table()`. This is a critical data-access layer.

## Symbol Inventory

### Module-level imports

| Symbol | Source | Verdict | Notes |
|---|---|---|---|
| `os` | stdlib | RETAIN | Used in `add_table` for `os.path.splitext`/`os.path.basename` |
| `pd` | `pandas` | RETAIN | Core dependency for CSV loading |
| `OpgeeObject` | `.core` | DROP | `TableManager` inherits from `OpgeeObject` but only gets a no-op `clear()` classmethod. Replace with plain `object` or standalone class. |
| `OpgeeException` | `.error` | RETAIN | Raised when unknown table requested |
| `getLogger` | `.log` | RETAIN | Standard logging |
| `resourceStream` | `.pkg_utils` | DROP | Replace with `importlib.resources` directly (absorbing `pkg_utils` functionality) |

### Module-level variables

| Symbol | Verdict | Notes |
|---|---|---|
| `_logger` | RETAIN | Standard logger instance |

### Classes

#### `TableDef`

| Symbol | Verdict | Notes |
|---|---|---|
| `class TableDef` | RETAIN | Simple metadata container for table loading parameters |
| `TableDef.__init__(self, basename, index_col, index_row, has_units, fillna)` | RETAIN | All five fields are used in `get_table()` loading logic |
| `TableDef.basename` | RETAIN | CSV filename stem |
| `TableDef.index_col` | RETAIN | Passed to `pd.read_csv(index_col=...)` |
| `TableDef.index_row` | RETAIN | Used as `header=` param for multi-row headers |
| `TableDef.has_units` | RETAIN | Controls pint-quantified column loading |
| `TableDef.fillna` | RETAIN | Optional NA fill value |

#### `TableManager`

| Symbol | Verdict | Notes |
|---|---|---|
| `class TableManager(OpgeeObject)` | RETAIN (modify base class) | Change to inherit from `object` instead of `OpgeeObject` |
| `TableManager.table_defs` (class variable, list) | RETAIN | Registry of all 32 built-in table definitions |
| `TableManager._table_def_dict` (class variable, dict) | RETAIN | Lookup dict keyed by basename |
| `TableManager.__init__(self, updates=None)` | RETAIN (modify) | See notes on `updates` parameter below |
| `TableManager.table_dict` (instance variable) | RETAIN | Cache of loaded DataFrames |
| `TableManager.updates` (instance variable) | DROP | XML-based `TableUpdate` mechanism from `table_update.py`. This is part of the XML model system. |
| `TableManager.get_table(self, name, raiseError=True)` | RETAIN (modify) | Core method. Must replace `resourceStream()` call with `importlib.resources`. Must remove `updates` application block. |
| `TableManager.add_table(self, pathname, index_col=None, skiprows=0)` | UNCERTAIN | Loads external CSV files. Only used in `test_add_table` test. Useful for extensibility but not part of core LCA flow. |

### Individual `TableDef` entries in `table_defs` list (all 32)

All RETAIN -- these define the built-in CSV tables used by process calculations:
`constants`, `GWP`, `bitumen-mining-energy-intensity`, `process-specific-EF`,
`water-treatment`, `heavy-oil-upgrading`, `transport-parameter`, `transport-share-fuel`,
`transport-by-mode`, `reaction-combustion-coeff`, `product-combustion-coeff`,
`gas-turbine-specs`, `gas-dehydration`, `acid-gas-removal`, `ryan-holmes-process`,
`imported-gas-comp`, `upstream-CI`, `vertical-drilling-energy-intensity`,
`horizontal-drilling-energy-intensity`, `fracture-consumption-table`, `land-use-EF`,
`pubchem-cid`, `ASPEN_input_boundary`, `demethanizer`, `loss-matrix-oil`,
`loss-matrix-gas`, `productivity-gas`, `productivity-oil`,
`site-fugitive-processing-unit-breakdown`, `well-completion-and-workover-C1-rate`,
`grid_mix_EF`, `grid_mix_feed`.

## Retain

- `class TableDef` -- metadata container, all fields
- `class TableManager` -- core data-access class (change base to `object`)
- `TableManager.table_defs` -- all 32 table definition entries
- `TableManager._table_def_dict` -- lookup dict
- `TableManager.__init__` -- simplified (drop `updates` param)
- `TableManager.table_dict` -- DataFrame cache
- `TableManager.get_table()` -- core method (rewrite resource loading, remove XML update block)
- `_logger`, `OpgeeException`, `pd`, `os` imports

## Drop

- `from .core import OpgeeObject` -- replace inheritance with plain `object`
- `from .pkg_utils import resourceStream` -- replace with `importlib.resources`
- `self.updates` instance variable -- XML-based `TableUpdate` system
- The XML table-update application block in `get_table()` (lines 123-128):
  ```python
  update = self.updates and self.updates.get(name)
  if update and update.enabled:
      for cell in update.cells:
          df.loc[cell.row, cell.col] = cell.value
  ```

## Uncertain

- `TableManager.add_table()` -- Only exercised in tests. Useful for allowing users to register external CSV tables at runtime. Leaning RETAIN for library extensibility, but could be dropped if the API surface is being minimized.

## Refactoring Notes

### Absorbing `pkg_utils.py` resource loading

The current call chain is:
```
get_table() -> resourceStream(relpath, stream_type='text')
  -> getResource(relpath) -> pkgutil.get_data('opgee', relpath)
  -> io.StringIO(text)
```

Replace with `importlib.resources` (available in Python 3.9+, preferred over deprecated `pkgutil.get_data`):

```python
from importlib.resources import files

def _table_stream(relpath: str):
    """Return a text stream for a package-relative CSV file."""
    return files("opgee").joinpath(relpath).open("r", encoding="utf-8")
```

Then in `get_table()`:
```python
s = _table_stream(f"tables/{name}.csv")
```

This is a private helper function that absorbs the specific functionality needed from
`pkg_utils.resourceStream` and `pkg_utils.getResource` without carrying over the
general-purpose API.

### Removing XML `TableUpdate` dependency

The `updates` parameter and the update-application block in `get_table()` depend on
`table_update.py`, which depends on `XmlInstantiable` from `core.py`. Since the goal
is to remove XML, this entire mechanism should be dropped. If programmatic table
overrides are needed later, a simpler dict-based API can be added.

### Base class change

`OpgeeObject` provides only a no-op `clear()` classmethod. `TableManager` does not
use it. Switch to inheriting from `object` (or use no explicit base class).
