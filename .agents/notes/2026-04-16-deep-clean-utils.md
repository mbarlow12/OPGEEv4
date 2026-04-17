# Deep Clean Proposal: `opgee/utils.py`

## Summary

`utils.py` is a grab-bag of helper functions inherited from pygcam. Many are tied to XML parsing, CLI (argparse), config system, or file-management tasks that a pure library does not need. A handful of general-purpose utilities are used by retained core modules (field, process, stream, core, attributes, thermodynamics) and must stay.

---

## RETAIN

### Functions

| Symbol | Reason |
|---|---|
| `coercible(value, pytype, raiseError)` | Used in `core.py`, `stream.py`, `attributes.py` for attribute type coercion. Core to the data model. |
| `to_int(s)` | Internal helper called by `coercible` when `pytype == 'int'`. |
| `binary(value)` | Internal helper called by `coercible` when `pytype == 'binary'`. |
| `getBooleanXML(value)` | Despite the name, this is a general boolean-string parser used in `core.py`, `stream.py`, `field.py`, `process.py`, `process_groups.py`, `analysis.py`. Deeply embedded; rename to `parse_boolean` during refactor. |
| `getFuncName` (lambda) | Called inside `coercible` for error messages. Tiny; keep as long as `coercible` stays. |
| `roundup(value, digits)` | Used in `field.py` (`num_prod_wells` calculation). |
| `flatten(listOfLists)` | General-purpose list utility. Currently used only in `manager.py` (DROP target), but trivial and potentially useful. Keep for now. |
| `dequantify_dataframe(df)` | Used in `field.py` for debug/summary output of pint-quantity DataFrames. |
| `splitAndStrip(s, delim)` | Used in `model_file.py` (DROP target) and `ParseCommaList` (DROP target), but also duplicated in `log.py`. If `model_file.py` is dropped, the only remaining consumer disappears. **Re-evaluate after model_file decision; lean RETAIN as a general-purpose one-liner.** |

### Module-level

| Symbol | Reason |
|---|---|
| `_logger` | Used by several functions; standard logging setup. |

---

## DROP

### Functions

| Symbol | Reason |
|---|---|
| `ipython_info()` | Used only in `graph.py` for notebook detection. Not needed in a pure library. |
| `pushd(directory)` | Context manager for `os.chdir`. No consumers in retained modules. |
| `positive_int(value)` | argparse type validator. Only used in `built_ins/run_plugin.py` (CLI, DROP). |
| `mkdirs(newdir, mode)` | File-system helper. Used in `manager.py` (DROP) and `model_file.py` (DROP). No retained-module consumers. |
| `removeTree(path, ignore_errors)` | File-system helper. No consumers outside tests. |
| `filecopy(src, dst, removeDst)` | File-system helper. No consumers at all (even tests don't use it). |
| `loadModuleFromPath(module_path, raiseError)` | Dynamic module loader. Used in `model_file.py` (DROP), `tool.py` (DROP), `post_processor.py` (DROP). No retained-module consumers. |
| `is_relpath(p)` | Used only in `model_file.py` (DROP). |
| `parseTrialString(string)` | MCS trial-range parser. Used only in `built_ins/run_plugin.py` (DROP). |

### Classes

| Symbol | Reason |
|---|---|
| `ParseCommaList` (argparse.Action) | argparse action class. Used only in `built_ins/run_plugin.py` and `csv2xml_plugin.py` (both DROP). |

### Constants

| Symbol | Reason |
|---|---|
| `TRIAL_STRING_DELIMITER` | Only used by `parseTrialString` (DROP). |

### Imports to remove

| Import | Reason |
|---|---|
| `import argparse` (line 10) | Only needed by `positive_int` and `ParseCommaList` (both DROP). |
| `from .config import unixPath` (line 15) | Only needed by `loadModuleFromPath` (DROP). Eliminates config dependency. |
| `from contextlib import contextmanager` (line 13) | Only needed by `pushd` (DROP). |

---

## UNCERTAIN

| Symbol | Reason |
|---|---|
| `splitAndStrip(s, delim)` | Listed under RETAIN above, but if `model_file.py` is fully dropped, the only production consumer vanishes. `log.py` has its own local copy. Could go either way -- trivial to keep as a general utility. |
| `flatten(listOfLists)` | Only current consumer is `manager.py` (DROP target). Trivial one-liner wrapping `itertools.chain`. Lean RETAIN as a general utility but could be inlined if needed. |

---

## Refactoring Notes

1. **Rename `getBooleanXML`** to `parse_boolean` -- the function has nothing XML-specific; it parses string representations of booleans. Widely used across retained core modules.
2. **Remove `import os` if possible** -- after dropping file-system helpers, check if `os` is still needed. `getFuncName` uses `sys`, not `os`. After drops, `os` would be unused.
3. **Remove `import sys`** -- only needed by `getFuncName` (via `sys._getframe`) and `loadModuleFromPath` (via `sys.modules`). After dropping `loadModuleFromPath`, `sys` is still needed for `getFuncName`.
4. **Config dependency eliminated** -- dropping `loadModuleFromPath` removes the `from .config import unixPath` import, breaking the circular-ish dependency between utils and config.
5. **Resulting file** will be ~80 lines (down from ~323), containing: `coercible`, `to_int`, `binary`, `getBooleanXML` (renamed), `getFuncName`, `roundup`, `flatten`, `dequantify_dataframe`, and optionally `splitAndStrip`.
