# OPGEE v5 Deep Clean Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strip OPGEE to a minimal pure-library package — no XML, CLI, MCS, GUI, plugins, config, or attribute system. Users construct and run simulations from Python.

**Architecture:** Seven sequential phases (delete → clean leaves → new foundations → strip core → restructure Process → migrate subclasses → restructure Field), each ending with a green `pytest` and a tagged gate commit. FieldContext carries infrastructure only (STP, tables, GWP, simulation params, process_data). All physical parameters are explicit typed constructor args on the classes that use them.

**Tech Stack:** Python >= 3.12, pint (Quantity[float] generics), pandas, numpy, networkx, pytest, ruff

**CRITICAL RULE — NO DEVIATIONS WITHOUT APPROVAL:**
> No agent may re-add, re-import, or restore any module, symbol, class, or function
> that the spec marks as REMOVE, DROP, or DELETE — not even temporarily, not even
> to fix a failing test. If a test failure or import error appears to require
> restoring deleted code, STOP and escalate to the user for discussion. The
> appropriate fix is almost always to adapt the consuming code, not to undo the
> deletion. This rule applies to every phase and every task.

**Spec:** `.agents/docs/specs/2026-04-16-deep-clean-design.md`

**Attribute traces:** `.agents/notes/field-attr-*.md`

**Per-module proposals:** `.agents/notes/2026-04-16-deep-clean-*.md`

---

## Phase 0: Bulk Delete

### Task 0.1: Delete excluded source files

**Files:**
- Delete: 24 individual files + 3 directories (see list below)

- [ ] **Step 1: Delete individual excluded source files**

```bash
cd /home/michael/rmi/dlab/opgee/current
git rm opgee/tool.py opgee/main.py opgee/subcommand.py \
       opgee/model_file.py opgee/XMLFile.py opgee/xml_utils.py \
       opgee/config.py opgee/attributes.py \
       opgee/smart_defaults.py opgee/audit.py opgee/process_groups.py \
       opgee/manager.py opgee/post_processor.py \
       opgee/graph.py opgee/model.py opgee/analysis.py \
       opgee/log.py opgee/results.py opgee/bfs.py \
       opgee/pkg_utils.py opgee/constants.py opgee/table_update.py \
       opgee/version.py opgee/version.sh
```

- [ ] **Step 2: Delete excluded directories**

```bash
git rm -r opgee/built_ins/ opgee/bin/
# Delete all etc/ files except units.txt
git rm opgee/etc/attributes.xml opgee/etc/Darwin.cfg opgee/etc/imported_fields.xml \
       opgee/etc/opgee.xml opgee/etc/opgee.xsd opgee/etc/pluginTemplate.py \
       opgee/etc/system.cfg opgee/etc/Windows.cfg
```

- [ ] **Step 3: Verify units.txt still exists**

```bash
ls opgee/etc/units.txt
```

Expected: file exists.

---

### Task 0.2: Delete excluded test files and test data

**Files:**
- Delete: ~18 test files + XML test data + support files

- [ ] **Step 1: Delete test files for deleted modules**

```bash
git rm tests/test_config.py tests/test_audit.py tests/test_model_file.py \
       tests/test_merge_xml.py tests/test_csv2xml.py tests/test_run_subcmd.py \
       tests/test_opgee_xml.py tests/test_smart_defaults.py tests/test_process_groups.py \
       tests/test_post_proc_plugin.py tests/test_distributed_mcs.py \
       tests/test_attr_constraints.py tests/test_attributes.py \
       tests/test_model.py tests/test_graph.py tests/test_xml_file.py \
       tests/BROKEN_test_smart_defaults.py tests/DERECATED_test_mcs.py
```

- [ ] **Step 2: Delete boundary-related tests (deferred feature)**

```bash
git rm tests/test_boundary.py tests/test_boundary_procs.py \
       tests/test_intermediate_boundary.py
```

- [ ] **Step 3: Delete test data files that depend on deleted modules**

```bash
git rm tests/files/opgee.cfg \
       tests/files/bad_model.xml tests/files/test_merge_1.xml \
       tests/files/test_merge_2.xml tests/files/test_merge_3.xml \
       tests/files/test_run_subcmd.xml tests/files/audit_model.xml \
       tests/files/test_process_groups.xml tests/files/test_boundary.xml \
       tests/files/test_boundary_procs.xml \
       tests/files/test_attr_constraints_1.xml \
       tests/files/test_attr_constraints_2.xml \
       tests/files/test_attr_constraints_3.xml \
       tests/files/test_mcs.xml \
       tests/files/simple_post_processor.py \
       tests/files/broken_post_proc_plugin.py \
       tests/files/output.py
git rm -r tests/files/post-proc-plugins/
```

---

### Task 0.3: Update conftest.py — remove XML/config dependencies

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/utils_for_tests.py`

- [ ] **Step 1: Replace conftest.py with minimal version**

Write `tests/conftest.py`:

```python
import pytest


def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", default=False, help="run slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
```

- [ ] **Step 2: Check if utils_for_tests.py imports deleted modules**

Read `tests/utils_for_tests.py`. If it imports from deleted modules (model_file, config, tool, etc.), strip those imports and functions. Keep any pure utility functions that don't depend on deleted code.

- [ ] **Step 3: Update opgee/__init__.py**

Write `opgee/__init__.py`:

```python
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
```

No changes needed — current content is already clean.

---

### Task 0.4: Update pyproject.toml — remove deleted entry points and dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Read pyproject.toml and identify sections to update**

Check for:
- `[project.scripts]` — remove `opg` CLI entry point
- `[project.entry-points]` — remove plugin entry points
- Dependencies on `lxml` (XML parsing) — keep for now, remove in later cleanup if unused

- [ ] **Step 2: Remove CLI entry point and plugin config**

Remove any `[project.scripts]` section referencing `opgee.tool` or `opgee.main`.
Remove any `[project.entry-points]` sections referencing `opgee.built_ins`.

---

### Task 0.5: Verification gate — Phase 0

- [ ] **Step 1: Run ruff to check for import errors**

```bash
uv run ruff check . 2>&1 | head -50
```

Fix any remaining imports of deleted modules in surviving files. Common patterns:
- `from .log import getLogger` → will be fixed in Phase 1
- `from .config import ...` → will be fixed in Phase 1
- `from .attributes import ...` → will be fixed in Phase 3

For Phase 0, the goal is to get `pytest` passing on surviving tests only. Some surviving test files may need temporary import fixes or may need to be skipped.

- [ ] **Step 2: Run pytest**

```bash
uv run pytest -x -q 2>&1 | tail -30
```

Expected: All surviving tests pass. If tests fail due to import errors from deleted modules, fix the imports in the affected test files (the source module fixes happen in Phase 1+).

- [ ] **Step 3: Commit and tag**

```bash
git add -A
git commit -m "phase 0: bulk delete excluded files, tests, and dependencies"
git tag phase-0-gate
```

---

## Phase 1: Clean Leaf Modules

### Task 1.1: Clean error.py

**Files:**
- Modify: `opgee/error.py`
- Test: `tests/test_core.py` (if it tests exceptions)

- [ ] **Step 1: Remove dropped exception classes**

Remove these classes from `opgee/error.py`:
- `AttributeError` (shadows builtin, attributes.py deleted)
- `FileFormatError` (parent of dropped exceptions only)
- `XmlFormatError` (XML deleted)
- `ConfigFileError` (config deleted)
- `CommandlineError` (CLI deleted)
- `McsUserError` (MCS deleted)
- `McsSystemError` (MCS deleted)
- `DistributionSpecError` (MCS deleted)
- `RemoteError` (distributed execution deleted)

Keep these classes unchanged:
- `OpgeeException`
- `OpgeeStopIteration`, `OpgeeMaxIterationsReached`, `OpgeeIterationConverged`
- `AbstractMethodError`
- `ModelValidationError`
- `BalanceError`
- `ZeroEnergyFlowError`

The result:

```python
class OpgeeException(Exception):
    pass


class OpgeeStopIteration(OpgeeException):
    def __init__(self, reason):
        self.reason = reason

class OpgeeMaxIterationsReached(OpgeeStopIteration):
    """Thrown when iterations have reached maximum_iterations."""
    pass

class OpgeeIterationConverged(OpgeeStopIteration):
    """Thrown when change variables have converged within tolerance."""
    pass

class AbstractMethodError(OpgeeException):
    def __init__(self, cls, method):
        self.cls = cls
        self.method = method

    def __str__(self):
        return f"Abstract method {self.method} was called. Subclass {self.cls.__name__} must implement this method."


class ModelValidationError(OpgeeException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f'<{self.__class__.__name__} "{self.msg}">'


class BalanceError(OpgeeException):
    def __init__(self, proc_name, mass_or_energy, message=None):
        self.proc_name = proc_name
        self.mass_or_energy = mass_or_energy
        self.message = message

    def __str__(self):
        return f"{self.mass_or_energy} is not balanced in {self.proc_name}" + \
               (f": {self.message}" if self.message else "")


class ZeroEnergyFlowError(OpgeeException):
    def __init__(self, stream, message=None):
        self.stream = stream
        self.message = message

    def __str__(self):
        return (f"Zero energy flow rate for {self.stream} boundary stream" +
                (f": {self.message}" if self.message else ""))
```

- [ ] **Step 2: Run pytest**

```bash
uv run pytest -x -q 2>&1 | tail -20
```

- [ ] **Step 3: Commit**

```bash
git add opgee/error.py
git commit -m "phase 1: clean error.py — drop 9 unused exception classes"
```

---

### Task 1.2: Clean units.py

**Files:**
- Modify: `opgee/units.py`

- [ ] **Step 1: Replace log and pkg_utils imports with stdlib**

Replace the current imports and initialization in `opgee/units.py`:

```python
import logging
from importlib.resources import files
from typing import Final, Optional

import pint
from pint.registry import ApplicationRegistry

from opgee.error import OpgeeException

_logger = logging.getLogger(__name__)

_ureg: Optional[ApplicationRegistry] = None

if _ureg is None:
    _ureg = pint.get_application_registry()
    del _ureg._units["bbl"]
    units_path = files("opgee.etc").joinpath("units.txt")
    lines = [line.strip() for line in units_path.read_text().splitlines()]
    _ureg.load_definitions(lines)

ureg: Final[ApplicationRegistry] = _ureg
del _ureg

# to avoid redundantly reporting bad units
_undefined_units = {}
```

Remove the `Qty = _ureg.Quantity` line (zero external consumers).

- [ ] **Step 2: Run pytest**

```bash
uv run pytest tests/test_core.py tests/test_energy.py -x -q 2>&1 | tail -20
```

- [ ] **Step 3: Commit**

```bash
git add opgee/units.py
git commit -m "phase 1: clean units.py — stdlib logging, importlib.resources, drop Qty"
```

---

### Task 1.3: Clean energy.py

**Files:**
- Modify: `opgee/energy.py`

- [ ] **Step 1: Remove OpgeeObject base and dead logger**

In `opgee/energy.py`, change imports:

```python
import pandas as pd

from .units import ureg
from .error import OpgeeException
```

Remove: `from .core import OpgeeObject`, `from .log import getLogger`, `_logger = getLogger(__name__)`.

Change class definition from `class Energy(OpgeeObject):` to `class Energy:`.

If `Energy.__init__` calls `super().__init__(name)`, remove that call and set `self.name` directly if needed (check if name is used — Energy may not have a name).

- [ ] **Step 2: Run pytest**

```bash
uv run pytest tests/test_energy.py -x -v 2>&1 | tail -30
```

- [ ] **Step 3: Commit**

```bash
git add opgee/energy.py
git commit -m "phase 1: clean energy.py — drop OpgeeObject base and dead logger"
```

---

### Task 1.4: Clean emissions.py

**Files:**
- Modify: `opgee/emissions.py`

- [ ] **Step 1: Remove OpgeeObject base**

In `opgee/emissions.py`, change imports — remove `from .core import OpgeeObject`.

Change class definition from `class Emissions(OpgeeObject):` to `class Emissions:`.

Remove `super().__init__(name)` call if present.

Keep the `from .stream import Stream` import for now — it accesses `Stream.VOCs`. This moves to chemistry.py in Phase 2.

- [ ] **Step 2: Run pytest**

```bash
uv run pytest tests/test_emissions.py -x -v 2>&1 | tail -30
```

- [ ] **Step 3: Commit**

```bash
git add opgee/emissions.py
git commit -m "phase 1: clean emissions.py — drop OpgeeObject base"
```

---

### Task 1.5: Clean import_export.py

**Files:**
- Modify: `opgee/import_export.py`

- [ ] **Step 1: Remove OpgeeObject base and dead logger**

In `opgee/import_export.py`:
- Remove `from .core import OpgeeObject`
- Remove `from .log import getLogger` and `_logger = getLogger(__name__)`
- Change `class ImportExport(OpgeeObject):` to `class ImportExport:`
- Remove `super().__init__(name)` if present
- Move inner import `from .units import ureg` (line 162) to top-level imports

- [ ] **Step 2: Run pytest**

```bash
uv run pytest tests/test_import_export.py -x -v 2>&1 | tail -30
```

- [ ] **Step 3: Commit**

```bash
git add opgee/import_export.py
git commit -m "phase 1: clean import_export.py — drop OpgeeObject base and dead logger"
```

---

### Task 1.6: Clean utils.py

**Files:**
- Modify: `opgee/utils.py`

- [ ] **Step 1: Strip to retained utilities only**

Rewrite `opgee/utils.py` keeping only:

```python
"""General-purpose utility functions."""
import logging

from .error import OpgeeException

_logger = logging.getLogger(__name__)


def coercible(value, type_fn, default=None):
    """Attempt to coerce `value` using `type_fn`, return `default` on failure."""
    try:
        return type_fn(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    return coercible(value, int, default=default)


def binary(value, default=None):
    return coercible(value, lambda v: int(float(v)), default=default)


def parse_boolean(value):
    """Parse string to boolean. Replaces getBooleanXML."""
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ('1', 'true', 'yes'):
        return True
    if s in ('0', 'false', 'no'):
        return False
    raise OpgeeException(f"Cannot convert '{value}' to boolean")


def getFuncName(level=1):
    """Return the name of the calling function."""
    import inspect
    return inspect.stack()[level][3]


def roundup(value, nearest):
    """Round `value` up to the nearest multiple of `nearest`."""
    return int(nearest * ((value + nearest - 1) // nearest))


def flatten(lst):
    """Flatten a list of lists into a single list."""
    return [item for sublist in lst for item in sublist]


def dequantify_dataframe(df):
    """Remove pint units from a DataFrame's values."""
    return df.apply(lambda col: col.pint.magnitude if hasattr(col, 'pint') else col)
```

Note: `getBooleanXML` is renamed to `parse_boolean`. Both names should work during transition — add an alias if needed:

```python
getBooleanXML = parse_boolean  # deprecated alias
```

- [ ] **Step 2: Run pytest**

```bash
uv run pytest tests/test_utils.py -x -v 2>&1 | tail -30
```

Adapt test_utils.py if it tests dropped functions — remove those test cases.

- [ ] **Step 3: Commit**

```bash
git add opgee/utils.py tests/test_utils.py
git commit -m "phase 1: clean utils.py — strip to 8 utilities, rename getBooleanXML"
```

---

### Task 1.7: Clean table_manager.py

**Files:**
- Modify: `opgee/table_manager.py`

- [ ] **Step 1: Replace imports and base class**

In `opgee/table_manager.py`:
- Replace `from .core import OpgeeObject` → remove
- Replace `from .log import getLogger` → `import logging`
- Replace `from .pkg_utils import resourceStream` → use `importlib.resources`
- Replace `_logger = getLogger(__name__)` → `_logger = logging.getLogger(__name__)`
- Change `class TableManager(OpgeeObject):` to `class TableManager:`

- [ ] **Step 2: Replace resourceStream usage with importlib.resources**

Add a private helper method:

```python
from importlib.resources import files

def _table_stream(basename):
    """Load a CSV table from the opgee.tables package data."""
    return files("opgee.tables").joinpath(basename)
```

Replace all `resourceStream(f"tables/{basename}")` calls with `_table_stream(basename)`.

- [ ] **Step 3: Remove XML TableUpdate mechanism**

Remove the `self.updates` instance variable and the XML update block in `get_table()` (lines ~123-128 that apply table updates from XML).

- [ ] **Step 4: Run pytest**

```bash
uv run pytest tests/test_table_manager.py -x -v 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git add opgee/table_manager.py
git commit -m "phase 1: clean table_manager.py — drop OpgeeObject, absorb pkg_utils, drop XML updates"
```

---

### Task 1.8: Clean combine_streams.py

**Files:**
- Modify: `opgee/combine_streams.py`

- [ ] **Step 1: Replace logger and fix header comment**

In `opgee/combine_streams.py`:
- Replace `from .log import getLogger` → `import logging`
- Replace `_logger = getLogger(__name__)` → `_logger = logging.getLogger(__name__)`
- Fix the module docstring from "Attribute and related classes" to "Stream combination utilities"

- [ ] **Step 2: Commit**

```bash
git add opgee/combine_streams.py
git commit -m "phase 1: clean combine_streams.py — stdlib logging, fix header"
```

---

### Task 1.9: Fix remaining import errors across codebase

**Files:**
- Modify: any surviving file that imports from deleted modules

- [ ] **Step 1: Find all remaining imports of deleted modules**

```bash
uv run ruff check . 2>&1 | grep -E "F811|F401|E902|import" | head -50
```

Also grep for specific deleted imports:

```bash
cd /home/michael/rmi/dlab/opgee/current
grep -rn "from .log import\|from .config import\|from .attributes import\|from .pkg_utils import" opgee/ --include="*.py" | grep -v __pycache__
```

- [ ] **Step 2: Fix each remaining import**

Common patterns:
- `from .log import getLogger` → `import logging` + `_logger = logging.getLogger(__name__)`
- `from .config import getParam...` → remove (config is deleted)
- `from .pkg_utils import resourceStream` → `from importlib.resources import files`

Note: Some files (core.py, process.py, stream.py, field.py, thermodynamics.py) will still have broken imports from attributes, XmlInstantiable, etc. — those are fixed in Phase 3-4. For now, only fix imports of modules that were fully deleted in Phase 0.

- [ ] **Step 3: Run full pytest**

```bash
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "phase 1: fix remaining imports of deleted modules"
```

---

### Task 1.10: Verification gate — Phase 1

- [ ] **Step 1: Run full test suite + ruff**

```bash
uv run ruff check .
uv run pytest -x -q 2>&1 | tail -30
```

Both must pass.

- [ ] **Step 2: Tag**

```bash
git tag phase-1-gate
```

---

## Phase 2: New Foundations

### Task 2.1: Create opgee/chemistry.py

**Files:**
- Create: `opgee/chemistry.py`
- Create: `tests/test_chemistry.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_chemistry.py`:

```python
"""Tests for opgee.chemistry — shared component chemistry constants."""
from opgee.chemistry import (
    PHASE_GAS, PHASE_LIQUID, PHASE_SOLID,
    COMPONENT_NAMES, CARBON_NUMBER, VOCS, HYDROCARBONS,
    R_GAS,
)


def test_phase_constants():
    assert PHASE_GAS == "gas"
    assert PHASE_LIQUID == "liquid"
    assert PHASE_SOLID == "solid"


def test_component_names_populated():
    assert len(COMPONENT_NAMES) > 20
    assert "CO2" in COMPONENT_NAMES
    assert "CH4" in COMPONENT_NAMES
    assert "C1" in COMPONENT_NAMES


def test_carbon_numbers():
    assert CARBON_NUMBER["C1"] == 1
    assert CARBON_NUMBER["C5"] == 5
    assert len(CARBON_NUMBER) > 0


def test_vocs():
    assert isinstance(VOCS, list)
    assert len(VOCS) > 0


def test_hydrocarbons():
    assert isinstance(HYDROCARBONS, list)
    assert len(HYDROCARBONS) > 0


def test_r_gas():
    # Universal gas constant in J/(mol·K)
    assert abs(R_GAS.magnitude - 8.31446) < 0.001
    assert str(R_GAS.units) == "joule / kelvin / mole"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_chemistry.py -x -v 2>&1 | tail -20
```

Expected: FAIL — `ModuleNotFoundError: No module named 'opgee.chemistry'`

- [ ] **Step 3: Extract chemistry data from stream.py**

Read `opgee/stream.py` and extract the class-level data: component_names list, carbon_number dict, VOCs list, _hydrocarbons list, _solids, _liquids, _gases, _other, phase constants. Also extract `is_carbon_number()`, `is_hydrocarbon()`, `molecule_to_carbon()`, `carbon_to_molecule()` helper functions.

Create `opgee/chemistry.py` with this extracted data. Example structure:

```python
"""
Component chemistry data and physical constants.

Extracted from Stream class-level data to break stream↔emissions coupling.
"""
import re

import pandas as pd

from .units import ureg

# Phase constants
PHASE_GAS: str = "gas"
PHASE_LIQUID: str = "liquid"
PHASE_SOLID: str = "solid"

# Compile patterns at load time
_carbon_number_prog = re.compile(r"^C(\d+)$")
_hydrocarbon_prog = re.compile(r"^(C\d+)H(\d+)$")


def is_carbon_number(name: str) -> bool:
    return _carbon_number_prog.match(name) is not None


def is_hydrocarbon(name: str) -> bool:
    return _hydrocarbon_prog.match(name) is not None


def molecule_to_carbon(name: str) -> str:
    # ... extract from stream.py
    pass


def carbon_to_molecule(name: str) -> str:
    # ... extract from stream.py
    pass


# Component names — extract the exact list from Stream.component_names
COMPONENT_NAMES: list[str] = [
    # ... copy the exact list from Stream class body
]

# Carbon number mapping — extract from Stream._carbon_number_dict
CARBON_NUMBER: dict[str, int] = {
    # ... copy from Stream
}

# VOC components — extract from Stream.VOCs
VOCS: list[str] = [
    # ... copy from Stream
]

# Hydrocarbon components
HYDROCARBONS: list[str] = [
    # ... copy from Stream._hydrocarbons
]

# Phase-grouped component lists
SOLIDS: list[str] = [...]    # from Stream._solids
LIQUIDS: list[str] = [...]   # from Stream._liquids
GASES: list[str] = [...]     # from Stream._gases
OTHER: list[str] = [...]     # from Stream._other

# Physical constants
R_GAS = ureg.Quantity(8.31446, "J/mol/K")
```

**Important:** Copy the exact data values from `stream.py` class body. Do not guess or abbreviate.

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_chemistry.py -x -v 2>&1 | tail -20
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add opgee/chemistry.py tests/test_chemistry.py
git commit -m "phase 2: create chemistry.py with extracted component data"
```

---

### Task 2.2: Create FieldContext and supporting dataclasses

**Files:**
- Create: `opgee/context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_context.py`:

```python
"""Tests for opgee.context — FieldContext and frozen config dataclasses."""
import pandas as pd
import pytest

from opgee.context import FieldContext, GWPData, SimulationParams
from opgee.core import STP
from opgee.table_manager import TableManager


def test_gwp_data_frozen():
    gwp = GWPData(values=pd.Series({"CO2": 1.0, "CH4": 30.0}), horizon=100)
    assert gwp.horizon == 100
    assert gwp.values["CH4"] == 30.0
    with pytest.raises(AttributeError):
        gwp.horizon = 20


def test_simulation_params_frozen():
    sim = SimulationParams(maximum_iterations=10, maximum_change=0.001)
    assert sim.maximum_iterations == 10
    with pytest.raises(AttributeError):
        sim.maximum_iterations = 20


def test_field_context_creation():
    ctx = FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=pd.Series({"CO2": 1.0}), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
    assert ctx.stp is STP
    assert isinstance(ctx.process_data, dict)
    assert len(ctx.process_data) == 0


def test_field_context_process_data_mutable():
    ctx = FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=pd.Series({"CO2": 1.0}), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
    ctx.process_data["key"] = "value"
    assert ctx.process_data["key"] == "value"


def test_field_context_table_access():
    ctx = FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=pd.Series({"CO2": 1.0}), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
    tbl = ctx.tables.get_table("constants")
    assert tbl is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_context.py -x -v 2>&1 | tail -20
```

Expected: FAIL — `ModuleNotFoundError: No module named 'opgee.context'`

- [ ] **Step 3: Create opgee/context.py**

```python
"""
FieldContext and supporting configuration dataclasses.

FieldContext is injected into Process and Stream instances. It carries
shared infrastructure only — no physical parameters. Physical params
are passed directly to Process/Stream constructors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .core import TemperaturePressure
from .table_manager import TableManager


@dataclass(frozen=True)
class GWPData:
    """Immutable global warming potentials."""
    values: pd.Series
    horizon: int


@dataclass(frozen=True)
class SimulationParams:
    """Immutable iteration/convergence settings."""
    maximum_iterations: int
    maximum_change: float


@dataclass
class FieldContext:
    """Injected into Process and Stream instances.

    Contains shared infrastructure only. Physical parameters (api, gor,
    res_press, etc.) are explicit constructor args on the classes that
    use them.

    process_data is intentionally mutable — it's the inter-process
    communication bulletin board (23+ call sites).
    """
    stp: TemperaturePressure
    tables: TableManager
    gwp: GWPData
    simulation: SimulationParams
    process_data: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_context.py -x -v 2>&1 | tail -20
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add opgee/context.py tests/test_context.py
git commit -m "phase 2: create FieldContext with frozen GWPData and SimulationParams"
```

---

### Task 2.3: Verification gate — Phase 2

- [ ] **Step 1: Run full suite**

```bash
uv run ruff check .
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 2: Tag**

```bash
git tag phase-2-gate
```

---

## Phase 3: Strip Core Classes

### Task 3.1: Strip core.py

**Files:**
- Modify: `opgee/core.py`
- Modify: `tests/test_core.py`

- [ ] **Step 1: Read current core.py fully to understand all exports**

Read `opgee/core.py` in full. Identify everything that's used by retained modules.

- [ ] **Step 2: Strip core.py to minimal exports**

Keep only:
- `OpgeeObject` class — just `name` + `__str__()`
- `TemperaturePressure` class — unchanged (clean dataclass with `__slots__`)
- `std_temperature`, `std_pressure`, `STP` constants
- `dict_from_list()` function

Remove:
- `XmlInstantiable` class and all methods
- `A` class (attribute accessor)
- `elt_name()`, `instantiate_subelts()`, `name_of()` functions
- Imports of `coercible`, `getBooleanXML` from utils
- Any other XML-related code

The stripped `core.py`:

```python
"""Core OPGEE base classes and physical constants."""
from .units import ureg, validate_unit
from .error import OpgeeException


class OpgeeObject:
    """Minimal base class — provides name and string representation."""
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


class TemperaturePressure:
    """Standard temperature-pressure pair with unit validation."""
    __slots__ = ['T', 'P']

    def __init__(self, T, P):
        self.T = T
        self.P = P

    def __str__(self):
        return f"TP({self.T}, {self.P})"


std_temperature = ureg.Quantity(60.0, "degF")
std_pressure = ureg.Quantity(14.696, "psia")
STP = TemperaturePressure(std_temperature, std_pressure)


def dict_from_list(lst):
    """Build a name-keyed dict from a list of named objects, checking for duplicates."""
    d = {}
    for obj in lst:
        name = obj.name
        if name in d:
            raise OpgeeException(f"Duplicate name '{name}'")
        d[name] = obj
    return d
```

- [ ] **Step 3: Update tests/test_core.py**

Remove tests for XmlInstantiable, A, elt_name, instantiate_subelts. Keep tests for OpgeeObject, TemperaturePressure, STP, dict_from_list.

- [ ] **Step 4: Run pytest**

```bash
uv run pytest tests/test_core.py -x -v 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git add opgee/core.py tests/test_core.py
git commit -m "phase 3: strip core.py to OpgeeObject + TP + STP + dict_from_list"
```

---

### Task 3.2: Decouple thermodynamics.py constructors

**Files:**
- Modify: `opgee/thermodynamics.py`
- Modify: `tests/test_thermofunction.py`

- [ ] **Step 1: Read thermodynamics.py and identify field/model references**

Read `opgee/thermodynamics.py` with targeted searches for `field.attr`, `field.`, `self.model`, `model.const`. Map each to its replacement.

- [ ] **Step 2: Refactor Oil/Gas/Water/Air constructors**

For each class:
- Remove `OpgeeObject` base class
- Replace `field` parameter with explicit typed parameters
- Replace `field.attr("name")` → explicit parameter
- Replace `model.const("universal-gas-constants")` → `R_GAS` from chemistry.py
- Replace `model.const("std-temperature")` → `STP.T`
- Replace `model.const("std-pressure")` → `STP.P`
- Drop `WetAir` class

Use Context7 to check `pint.Quantity[float]` generic syntax for type annotations.

- [ ] **Step 3: Update tests/test_thermofunction.py**

The 55 thermofunction tests need their setup updated. Find how they currently construct Oil/Gas/Water (likely via model fixtures) and update to use explicit construction.

- [ ] **Step 4: Run pytest**

```bash
uv run pytest tests/test_thermofunction.py -x -v 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git add opgee/thermodynamics.py tests/test_thermofunction.py
git commit -m "phase 3: decouple thermodynamics constructors from field/model"
```

---

### Task 3.3: Strip stream.py

**Files:**
- Modify: `opgee/stream.py`
- Modify: `tests/test_stream.py`

- [ ] **Step 1: Read stream.py fully**

Map all imports, class variables, and methods to retain/drop per the per-module proposal in `.agents/notes/2026-04-16-deep-clean-stream.md`.

- [ ] **Step 2: Strip XML/parent/enabled from Stream**

- Remove `AttributeMixin`, `XmlInstantiable` base classes
- Remove `from_xml()`, `children()`, `validate()`, `extend_components()`
- Remove `_extensions` class variable, `has_exogenous_data`
- Import phase constants and component data from `opgee.chemistry` instead of defining class-level
- Rename `xml_data` → `initial_data`
- Add `ctx: FieldContext` parameter to `__init__`
- Add `contents: list[str]` parameter to `__init__`
- Fix `to_dataframe()` to not reference `self.parent.name`

- [ ] **Step 3: Update tests/test_stream.py**

Replace XML construction with direct `Stream(name=..., ctx=..., contents=...)` construction.

- [ ] **Step 4: Run pytest**

```bash
uv run pytest tests/test_stream.py tests/test_molecule_names.py -x -v 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git add opgee/stream.py tests/test_stream.py tests/test_molecule_names.py
git commit -m "phase 3: strip stream.py — remove XML, add FieldContext, extract chemistry"
```

---

### Task 3.4: Verification gate — Phase 3

- [ ] **Step 1: Run full suite**

```bash
uv run ruff check .
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 2: Tag**

```bash
git tag phase-3-gate
```

---

## Phase 4: Restructure Process Base

### Task 4.1: Restructure Process class

**Files:**
- Modify: `opgee/process.py`

- [ ] **Step 1: Read process.py fully and map all methods**

Read `opgee/process.py` and cross-reference with `.agents/notes/2026-04-16-deep-clean-process.md` for the retain/drop list.

- [ ] **Step 2: Strip Process to new design**

Remove:
- Base classes: `AttributeMixin`, `XmlInstantiable`
- All imports of deleted modules (attributes, config, core.XmlInstantiable, utils.getBooleanXML)
- Class-registry functions: `get_subclasses`, `_subclass_dict`, `decache_subclasses`, `_get_subclass`, `reload_subclass_dict`
- Methods: `from_xml`, `validate`, `validate_proc`, `validate_streams`, `children`, `run_if_enabled`, `check_enabled`, `clear_iterating_process_list`, `set_run_after`, `set_extend`, `find_stream`, `get_reservoir`, `impute`, `venting_fugitive_rate`, `get_process_EF`, `within_boundary`, `beyond_boundary`, `check_balances`
- `Boundary` class entirely

New `__init__` signature:

```python
class Process:
    name: str
    ctx: FieldContext
    emissions: Emissions
    energy: Energy
    import_export: ImportExport
    intermediate_results: IntermediateValues
    input_streams: list[Stream]
    output_streams: list[Stream]

    def __init__(self, name: str, ctx: FieldContext):
        self.name = name
        self.ctx = ctx
        self.emissions = Emissions()
        self.energy = Energy()
        self.import_export = ImportExport()
        self.intermediate_results = IntermediateValues()
        self.input_streams = []
        self.output_streams = []
        self._iteration_value = None
        self._visited = False

    def __str__(self) -> str:
        return self.name
```

Keep `Reservoir` as a simplified Process subclass.
Keep `IntermediateValues` inner class.
Keep all retained methods (~35) — stream finding, emission/energy rates, fugitives, iteration, reset.

- [ ] **Step 3: Run pytest**

```bash
uv run pytest -x -q 2>&1 | tail -30
```

Many process subclass tests may break here because they depend on the old constructor. That's expected — they'll be fixed in Phase 5.

- [ ] **Step 4: Commit**

```bash
git add opgee/process.py
git commit -m "phase 4: restructure Process base — new init, drop XML/boundary/enabled"
```

---

### Task 4.2: Verification gate — Phase 4

- [ ] **Step 1: Run ruff and pytest**

```bash
uv run ruff check .
uv run pytest -x -q 2>&1 | tail -30
```

Note: Some process subclass tests may be failing if they haven't been adapted yet. The gate here is that the base Process class and its direct tests pass, and no ruff errors in process.py.

- [ ] **Step 2: Tag**

```bash
git tag phase-4-gate
```

---

## Phase 5: Migrate Process Subclasses

### Task 5.1: Tier 1 — Simple processes (12 files, parallel dispatch)

**Files:** See Appendix A for full list (12 files, 0-2 field refs each).

All 12 Tier 1 files can be dispatched as parallel subagents simultaneously — they are
independent and trivial to migrate.

- [ ] **Step 1: Dispatch 12 parallel subagents, one per file**

Each subagent receives the file path, the transformation rules (Appendix B), and these instructions:
1. Read the assigned process file
2. Read `opgee/process.py` to understand the new `__init__(name, ctx)` signature
3. Apply transformations:
   - Add `ctx: FieldContext` parameter, replace `super().__init__(name, **kwargs)` with `super().__init__(name, ctx)`
   - Replace `self.attr("x")` → `self.x` (add as typed constructor param with class-level annotation)
   - Replace `run(self, analysis)` → `run(self)`
   - Remove `analysis.` references inside `run()`
   - Replace `from .log import getLogger` → `import logging`
   - Remove imports of deleted modules
   - Use `Quantity[float]` for pint type annotations
4. Run `uv run ruff check opgee/processes/<file>`

Files:
- `__init__.py` (0 refs)
- `flaring.py` (0 refs)
- `natural_gas_liquid.py` (0 refs)
- `storage_well.py` (0 refs)
- `CO2_injection_well.py` (1 ref — `field.save_process_data`)
- `pre_membrane_chiller.py` (1 ref — `self.attr`)
- `shared.py` (1 ref — also refactor `predict_blower_energy_use` per Task 5.4)
- `sour_gas_injection.py` (1 ref — `field.save_process_data`)
- `compressor.py` (2 refs — helper class, not Process subclass)
- `gas_reinjection_well.py` (2 refs)
- `LNG_transport.py` (2 refs)
- `petrocoke_transport.py` (2 refs)

- [ ] **Step 2: Review subagent results and run pytest**

```bash
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 3: Commit**

```bash
git add opgee/processes/
git commit -m "phase 5: migrate Tier 1 processes (12 files, 0-2 field refs)"
```

---

### Task 5.2: Tier 2 — Medium processes (20 files, 3 parallel batches)

**Files:** See Appendix A for full list (20 files, 3-11 field refs each).

Each subagent reads its assigned file, the field access traces in `.agents/notes/field-attr-*.md`,
and applies the transformation rules from Appendix B.

- [ ] **Step 1: Batch A — dispatch 7 parallel subagents (3-5 refs each)**

- `LNG_regasification.py` (3 refs)
- `pre_membrane_compressor.py` (3 refs)
- `storage_compressor.py` (3 refs)
- `storage_separator.py` (3 refs)
- `VRU_compressor.py` (3 refs)
- `gas_distribution.py` (4 refs)
- `gas_lifting_compressor.py` (4 refs)

- [ ] **Step 2: Review Batch A, run pytest, commit**

```bash
uv run pytest -x -q 2>&1 | tail -30
git add opgee/processes/
git commit -m "phase 5: migrate Tier 2 Batch A (7 files, 3-5 refs)"
```

- [ ] **Step 3: Batch B — dispatch 7 parallel subagents (4-8 refs each)**

- `ryan_holmes.py` (4 refs)
- `CO2_reinjection_compressor.py` (5 refs)
- `LNG_liquefaction.py` (5 refs)
- `post_storage_compressor.py` (5 refs)
- `sour_gas_compressor.py` (5 refs)
- `CO2_membrane.py` (7 refs)
- `crude_oil_transport.py` (8 refs)

- [ ] **Step 4: Review Batch B, run pytest, commit**

```bash
uv run pytest -x -q 2>&1 | tail -30
git add opgee/processes/
git commit -m "phase 5: migrate Tier 2 Batch B (7 files, 4-8 refs)"
```

- [ ] **Step 5: Batch C — dispatch 6 parallel subagents (8-11 refs each)**

- `transport_energy.py` (8 refs — helper class)
- `VF_partition.py` (8 refs)
- `gas_gathering.py` (9 refs)
- `gas_reinjection_compressor.py` (9 refs)
- `transmission_compressor.py` (11 refs)
- `water_injection.py` (11 refs)

- [ ] **Step 6: Review Batch C, run pytest, commit**

```bash
uv run pytest -x -q 2>&1 | tail -30
git add opgee/processes/
git commit -m "phase 5: migrate Tier 2 Batch C (6 files, 8-11 refs)"
```

---

### Task 5.3: Tier 3 — Complex processes (19 files, small parallel batches)

**Files:** See Appendix A for full list (19 files, 12-61 field refs each).

Dispatch in batches of 2-3 with review between batches due to complexity.

- [ ] **Step 1: Batch D — dispatch 3 parallel subagents (12-13 refs)**

- `crude_oil_stabilization.py` (12 refs)
- `crude_oil_storage.py` (13 refs)
- `heavy_oil_upgrading.py` (13 refs)

- [ ] **Step 2: Review Batch D, run pytest, commit**

```bash
uv run pytest -x -q 2>&1 | tail -30
git add opgee/processes/
git commit -m "phase 5: migrate Tier 3 Batch D (3 files, 12-13 refs)"
```

- [ ] **Step 3: Batch E — dispatch 3 parallel subagents (14-15 refs)**

- `bitumen_mining.py` (14 refs)
- `crude_oil_dewatering.py` (14 refs)
- `reservoir_well_interface.py` (15 refs)

- [ ] **Step 4: Review Batch E, run pytest, commit**

- [ ] **Step 5: Batch F — dispatch 3 parallel subagents (16-18 refs)**

- `acid_gas_removal.py` (16 refs)
- `gas_dehydration.py` (16 refs)
- `demethanizer.py` (18 refs)

- [ ] **Step 6: Review Batch F, run pytest, commit**

- [ ] **Step 7: Batch G — dispatch 3 parallel subagents (17-22 refs)**

- `venting.py` (17 refs)
- `heavy_oil_dilution.py` (22 refs)
- `water_treatment.py` (22 refs)

- [ ] **Step 8: Review Batch G, run pytest, commit**

- [ ] **Step 9: Batch H — dispatch 3 parallel subagents (24-28 refs)**

- `drilling.py` (24 refs)
- `steam_generation.py` (25 refs)
- `downhole_pump.py` (28 refs)

- [ ] **Step 10: Review Batch H, run pytest, commit**

- [ ] **Step 11: Batch I — dispatch 2 parallel subagents (30-32 refs)**

- `separation.py` (30 refs)
- `exploration.py` (32 refs)

- [ ] **Step 12: Review Batch I, run pytest, commit**

- [ ] **Step 13: gas_partition.py (52 refs) — single subagent, most complex Process**

Heaviest Process subclass. Subagent must read full file + field access traces
and carefully map all 52 references.

- [ ] **Step 14: Review gas_partition.py, run pytest, commit**

- [ ] **Step 15: steam_generator.py (61 refs) — single subagent, heaviest overall**

Helper class with ~40 uncached field attrs via `field.attr()`. All become typed
constructor params. `SteamGeneration` process constructs it and passes params.

- [ ] **Step 16: Review steam_generator.py, run pytest, commit**

---

### Task 5.4: Clean up processes/shared.py

**Files:**
- Modify: `opgee/processes/shared.py`
- Modify: `tests/test_shared.py`

- [ ] **Step 1: Refactor predict_blower_energy_use signature**

Current: takes `proc` object and reads `proc.field.model.const()`.
New: all 7 parameters explicit, no `proc` argument.

```python
def predict_blower_energy_use(
    air_volume_rate,
    air_press_in,
    air_press_out,
    air_temp_in,
    air_temp_out,
    air_density,
    blower_efficiency,
) -> ...:
```

Update all callers to pass explicit values.

- [ ] **Step 2: Update tests/test_shared.py**

- [ ] **Step 3: Commit**

```bash
git add opgee/processes/shared.py tests/test_shared.py
git commit -m "phase 5: refactor shared.py — explicit params for predict_blower_energy_use"
```

---

### Task 5.5: Verification gate — Phase 5

- [ ] **Step 1: Run full suite**

```bash
uv run ruff check .
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 2: Tag**

```bash
git tag phase-5-gate
```

---

## Phase 6: Restructure Field

### Task 6.1: Restructure Field class

**Files:**
- Modify: `opgee/field.py`
- Modify: `tests/test_field.py`

- [ ] **Step 1: Read field.py fully and map all methods**

Cross-reference with `.agents/notes/2026-04-16-deep-clean-field.md`.

- [ ] **Step 2: Strip Field to new design**

Remove:
- `AttributeMixin`, `XmlInstantiable` base classes
- `from_xml()`, `cache_attributes()`, `set_extend()`, `set_modifies()`
- `resolve_process_choices()`, all `@SmartDefault.register` methods
- All Boundary-related methods
- `compute_carbon_intensity()` (deferred)
- `energy_and_emissions()`, `check_enabled_processes()`
- All imports of deleted modules

New constructor:

```python
class Field:
    name: str
    ctx: FieldContext
    graph: nx.DiGraph
    processes: dict[str, Process]
    streams: dict[str, Stream]
    oil: Oil
    gas: Gas
    water: Water
    # ... ~7 Field-internal attrs

    def __init__(
        self,
        name: str,
        simulation: SimulationParams,
        gwp: GWPData,
        tables: TableManager,
        processes: list[Process],
        streams: list[Stream],
        num_prod_wells: int = 0,
        oil_sands_mine: str = "",
        field_production_lifetime: Quantity[float] = ...,
        res_press: Quantity[float] = ...,
        res_temp: Quantity[float] = ...,
        has_grid_mix: bool = False,
    ):
        self.ctx = FieldContext(
            stp=STP, tables=tables, gwp=gwp, simulation=simulation,
        )
        self.processes = {p.name: p for p in processes}
        self.streams = {s.name: s for s in streams}
        self.graph = self._build_graph()
        ...
```

- [ ] **Step 3: Replace bfs.py with networkx**

Replace custom `bfs()` calls with `nx.topological_sort()`, `nx.simple_cycles()`, etc.

- [ ] **Step 4: Move graph scheduling metadata from Process to Field**

`cycle_starts`, `impute_starts`, `run_after` become Field instance attributes, populated during graph construction.

- [ ] **Step 5: Simplify run()**

`run()` takes no params. GWP comes from `self.ctx.gwp`. No `analysis` parameter. No `trial_num`.

- [ ] **Step 6: Update tests/test_field.py**

Rewrite Field construction to use direct instantiation. Keep assertion logic for energy/emission calculations.

- [ ] **Step 7: Run pytest**

```bash
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 8: Commit**

```bash
git add opgee/field.py tests/test_field.py
git commit -m "phase 6: restructure Field — new constructor, networkx graph, FieldContext"
```

---

### Task 6.2: Update remaining tests

**Files:**
- Modify: `tests/test_process_loop.py`
- Modify: `tests/test_impute.py`
- Modify: `tests/test_field_groups.py`
- Modify: `tests/test_comparison.py`
- Modify: `tests/test_coeff.py`
- Modify: `tests/test_packet.py`

- [ ] **Step 1: Evaluate each remaining test file**

For each, determine if it:
- Tests deleted functionality → delete the test file
- Tests retained functionality with old construction → adapt
- Tests orchestration that no longer exists → delete

- [ ] **Step 2: Adapt or delete each test file**

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "phase 6: adapt remaining test files to new architecture"
```

---

### Task 6.3: Final cleanup

**Files:**
- Modify: `opgee/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Update __init__.py with clean public API**

```python
"""OPGEE — Oil Production Greenhouse gas Emissions Estimator."""
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from .context import FieldContext, GWPData, SimulationParams
from .field import Field
from .process import Process
from .stream import Stream
```

- [ ] **Step 2: Clean pyproject.toml dependencies**

Remove dependencies that are no longer needed:
- `lxml` (XML parsing — verify no remaining imports)
- Any other dependencies only used by deleted modules

Add `networkx` if not already present.

- [ ] **Step 3: Run full suite one final time**

```bash
uv run ruff check .
uv run pytest -x -q 2>&1 | tail -30
```

- [ ] **Step 4: Commit**

```bash
git add opgee/__init__.py pyproject.toml
git commit -m "phase 6: final cleanup — public API exports, clean dependencies"
```

---

### Task 6.4: Verification gate — Phase 6 (final)

- [ ] **Step 1: Run full suite with verbose output**

```bash
uv run ruff check .
uv run pytest -v 2>&1 | tail -50
```

All tests must pass.

- [ ] **Step 2: Tag**

```bash
git tag phase-6-gate
```

- [ ] **Step 3: Summary commit**

```bash
git log --oneline phase-0-gate..HEAD
```

Review the commit history to ensure it tells a clear story.

---

## Appendix A: Process Subclass Tier Assignments (all 51 files)

Classification by total field access references (self.field + self.attr + field. alias).

### Tier 1 — Simple (12 files, 0-2 references)

Good candidates for parallel subagent dispatch — each is independent and quick.

| File | Total refs | Notes |
|------|-----------|-------|
| `__init__.py` | 0 | Package init |
| `flaring.py` | 0 | |
| `natural_gas_liquid.py` | 0 | |
| `storage_well.py` | 0 | |
| `CO2_injection_well.py` | 1 | |
| `pre_membrane_chiller.py` | 1 | |
| `shared.py` | 1 | Helper module, not a Process subclass |
| `sour_gas_injection.py` | 1 | |
| `compressor.py` | 2 | Helper class, not a Process subclass |
| `gas_reinjection_well.py` | 2 | |
| `LNG_transport.py` | 2 | |
| `petrocoke_transport.py` | 2 | |

### Tier 2 — Medium (20 files, 3-11 references)

Can be dispatched in parallel batches of ~5-7 subagents.

| File | Total refs | Notes |
|------|-----------|-------|
| `LNG_regasification.py` | 3 | |
| `pre_membrane_compressor.py` | 3 | |
| `storage_compressor.py` | 3 | |
| `storage_separator.py` | 3 | |
| `VRU_compressor.py` | 3 | |
| `gas_distribution.py` | 4 | |
| `gas_lifting_compressor.py` | 4 | |
| `ryan_holmes.py` | 4 | |
| `CO2_reinjection_compressor.py` | 5 | |
| `LNG_liquefaction.py` | 5 | |
| `post_storage_compressor.py` | 5 | |
| `sour_gas_compressor.py` | 5 | |
| `CO2_membrane.py` | 7 | |
| `crude_oil_transport.py` | 8 | |
| `transport_energy.py` | 8 | Helper class, not a Process subclass |
| `VF_partition.py` | 8 | |
| `gas_gathering.py` | 9 | |
| `gas_reinjection_compressor.py` | 9 | |
| `transmission_compressor.py` | 11 | |
| `water_injection.py` | 11 | |

### Tier 3 — Complex (19 files, 12+ references)

Migrate individually or in small batches of 2-3. Each needs careful attention.

| File | Total refs | Notes |
|------|-----------|-------|
| `crude_oil_stabilization.py` | 12 | |
| `crude_oil_storage.py` | 13 | |
| `heavy_oil_upgrading.py` | 13 | |
| `bitumen_mining.py` | 14 | |
| `crude_oil_dewatering.py` | 14 | |
| `reservoir_well_interface.py` | 15 | |
| `acid_gas_removal.py` | 16 | |
| `gas_dehydration.py` | 16 | |
| `venting.py` | 17 | |
| `demethanizer.py` | 18 | |
| `heavy_oil_dilution.py` | 22 | |
| `water_treatment.py` | 22 | |
| `drilling.py` | 24 | |
| `steam_generation.py` | 25 | |
| `downhole_pump.py` | 28 | |
| `separation.py` | 30 | |
| `exploration.py` | 32 | |
| `gas_partition.py` | 52 | Heaviest Process subclass |
| `steam_generator.py` | 61 | Helper class, heaviest overall |

### Totals

| Tier | Files | Parallel strategy |
|------|-------|-------------------|
| Tier 1 | 12 | All 12 in parallel |
| Tier 2 | 20 | 3-4 batches of 5-7 in parallel |
| Tier 3 | 19 | Individual or pairs |
| **Total** | **51** | |

## Appendix B: Key Transformation Patterns

| Old Pattern | New Pattern |
|-------------|-------------|
| `self.attr("name")` | `self.name` (explicit constructor param) |
| `self.field.attr("name")` | `self.name` (explicit constructor param) |
| `self.field.oil_volume_rate` | `self.oil_volume_rate` (explicit constructor param) |
| `self.field.gas` | `self.gas` (constructor param: `gas: Gas`) |
| `self.field.oil` | `self.oil` (constructor param: `oil: Oil`) |
| `self.field.water` | `self.water` (constructor param: `water: Water`) |
| `self.field.stp` | `self.ctx.stp` |
| `self.field.process_data[k]` | `self.ctx.process_data[k]` |
| `self.field.save_process_data(k, v)` | `self.ctx.process_data[k] = v` |
| `self.field.get_process_data(k)` | `self.ctx.process_data[k]` |
| `self.field.model.const("x")` | Inline constant or `self.ctx.tables` |
| `self.field.import_export` | `self.import_export` (on Process base) |
| `self.field.component_fugitive_table` | Constructor param or `self.ctx.tables` |
| `self.field.imported_gas_comp[k]` | Constructor param |
| `run(self, analysis)` | `run(self)` |
| `analysis.gwp` | `self.ctx.gwp` |
| `from .log import getLogger` | `import logging` |
| `getLogger(__name__)` | `logging.getLogger(__name__)` |
| `from .attributes import AttributeMixin` | Remove |
| `from .core import XmlInstantiable` | Remove |
