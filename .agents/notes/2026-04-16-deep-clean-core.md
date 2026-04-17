# Deep Clean: core.py

## Summary

`core.py` currently defines `OpgeeObject`, `XmlInstantiable`, `A` (attribute accessor), `TemperaturePressure`, physical constants (`STP`), XML helpers, and a `Timer` utility. The entire XML layer and parent/child hierarchy are dropped. What remains is a minimal base class, a TP dataclass, and physical constants.

## Retain

- **`OpgeeObject`** (class) — Root base class. Stripped to `name` + `__str__` only:
  ```python
  class OpgeeObject:
      def __init__(self, name):
          self.name = name
      def __str__(self): ...  # e.g. <Process name="Separation">
  ```
- **`TemperaturePressure`** (class) — Clean dataclass-like with `__slots__`, used pervasively in thermodynamics, streams, combine_streams, process code. No dependencies beyond `pint`/`ureg`. No changes needed.
- **`std_temperature`** — Module constant, used via `STP`.
- **`std_pressure`** — Module constant, used via `STP`.
- **`STP`** — `TemperaturePressure` instance for standard conditions. Used in field.py, thermodynamics.py, combine_streams.py.
- **`dict_from_list(objs)`** — Builds a name-keyed dict with uniqueness check. Used by `field.py`. No XML dependency.

## Drop

### XmlInstantiable (entire class)
- `XmlInstantiable` class definition
- `from_xml()` abstract classmethod
- `print_in_context()` — debug-only, called within its own error path
- `parent` attribute / `set_parent()` — parent hierarchy eliminated
- `find_container(cls)` — parent hierarchy eliminated
- `adopt(objs, asDict)` — parent hierarchy eliminated
- `enabled` / `is_enabled()` / `set_enabled()` — existence = enabled

### A (attribute accessor class)
- `A` class — XML attribute accessor
- `split_attr_name()` — attribute system parser
- `CLASS_DELIMITER` — used only by `split_attr_name`

### XML helpers
- `elt_name(elt)` — extracts name from lxml elements
- `instantiate_subelts(elt, cls, ...)` — XML factory function

### Dead code
- `name_of(obj)` — not imported anywhere

### Imports to remove
- `getBooleanXML` — no longer needed (was for `set_enabled`)
- `coercible` — only used by `A` class

## Uncertain

- **`Timer`** — Pure utility (context manager for timing). Only remaining consumer after cleanup is `field.py`. Could inline `time.time()` there, or keep Timer in `utils.py`. Low stakes.
- **`OpgeeObject.clear()` classmethod** — Currently a no-op hook for subclass override. With `post_processor.py` dropped, evaluate whether any remaining class needs this. Likely drop.
- **`__str__` format** — Current format is `<TypeName name="foo" enabled=True>`. Drop the `enabled` part. Decide whether all OpgeeObject subclasses get this `__str__` (lean yes — useful for debugging).
