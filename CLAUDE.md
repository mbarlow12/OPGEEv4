# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

OPGEE v4 is a life cycle assessment (LCA) tool for oil and gas fields, implemented as a Python package. It translates physical descriptions of oil and gas fields and their processes into runnable LCA models, calculating energy use, greenhouse gas emissions, and carbon intensity.

## File Size and Performance Considerations

**CRITICAL**: This codebase contains large files that require special handling:

| File                               | Size/Lines  | Handling                                    |
| ---------------------------------- | ----------- | ------------------------------------------- |
| `opgee/tables/loss-matrix-gas.csv` | 7.1 MB      | **NEVER read fully** - use targeted queries |
| `opgee/tables/loss-matrix-oil.csv` | 4.8 MB      | **NEVER read fully** - use targeted queries |
| `opgee/field.py`                   | 1,825 lines | Read with offset/limit or targeted searches |
| `opgee/thermodynamics.py`          | 1,359 lines | Read with offset/limit or targeted searches |
| `opgee/process.py`                 | 1,125 lines | Read with offset/limit or targeted searches |
| `tests/files/test-fields-9000.xml` | 609K+ lines | **NEVER read fully** - test data file       |

When investigating code patterns in large files, use targeted grep operations rather than full file reads.

## Key Architecture

OPGEE uses a flat package structure with all core modules in `opgee/`:

```
opgee/                      # Main package (all core modules at root level)
├── model.py               # Top-level Model class orchestrating the system
├── field.py               # Field class - oil/gas fields with processes/streams
├── process.py             # Base Process class for all LCA processes
├── stream.py              # Material/energy flow connections between processes
├── thermodynamics.py      # Oil/gas/water property calculations
├── model_file.py          # XML model definition parsing
├── attributes.py          # XML attribute definitions and validation
├── emissions.py           # Emission calculation utilities
├── energy.py              # Energy calculation utilities
├── analysis.py            # Analysis orchestration
├── config.py              # Configuration management
├── error.py               # Custom exception classes
├── tool.py                # Main CLI entry point (`opg` command)
│
├── processes/             # 51 process implementations
│   ├── drilling.py
│   ├── separation.py
│   ├── compressor.py
│   ├── gas_dehydration.py
│   └── ... (48 more)
│
├── tables/                # CSV data files
│   ├── constants.csv      # Physical constants
│   ├── GWP.csv           # Global Warming Potentials
│   ├── process-specific-EF.csv
│   ├── loss-matrix-*.csv  # LARGE - fugitive emissions lookup
│   └── ...
│
├── built_ins/             # 9 plugin implementations
│   ├── run_plugin.py
│   ├── graph_plugin.py
│   └── ...
│
├── bin/                   # 7 CLI utility scripts
│   ├── combine_csvs.py
│   └── ...
│
└── etc/                   # Configuration files
    └── attributes.xml     # Class attribute definitions (757 lines)
```

### Core Module Relationships

1. **Model** (`model.py`) - Top-level container for analyses and fields
2. **Analysis** (`analysis.py`) - Groups fields for a specific analysis scenario
3. **Field** (`field.py`) - Contains processes and streams for one oil/gas field
4. **Process** (`process.py`) - Base class for individual LCA calculation steps
5. **Stream** (`stream.py`) - Material/energy flows connecting processes

### XML Model Definition

Models are parsed from XML files via `model_file.py`:

- `attributes.xml` defines all valid attributes for Model, Analysis, Field, and Process classes
- Attribute types: binary, int, float, str with optional Options enums
- Validation constraints: GT/LT/GE/LE bounds, units, descriptions, defaults

## Development Commands

The project uses `uv` for Python package management. Python >= 3.11 is required.

```bash
# Initialize environment (first time or after dependency changes)
uv sync

# Run tests
uv run pytest
uv run pytest -v                    # Verbose
uv run pytest tests/test_model.py   # Specific test

# Linting and formatting
uv run ruff check .
uv run ruff format .

```

## Model Definition Format

Models are defined in XML files specifying:

- **Model**: Top-level container with iteration and validation settings
- **Analysis**: Calculation scenario with GWP settings and boundary conditions
- **Field**: Oil/gas field definition with 100+ attributes (location, reservoir properties, production methods, etc.)
- **Process**: Individual conversion/transport steps (drilling, separation, flaring, etc.)
- **Stream**: Material/energy flows connecting processes

Example workflow:

1. Define field properties in XML
2. Specify process network and connections
3. Run analysis: `opg run model.xml`
4. View results in CSV output

## Process Implementation Pattern

New processes inherit from `Process` base class and implement:

```python
from opgee.process import Process

class MyProcess(Process):
    def run(self, analysis):
        """Core calculation logic."""
        # Get input streams
        input_stream = self.find_input_stream("gas")

        # Perform calculations
        energy = self.calculate_energy(input_stream)

        # Set output streams and emissions
        self.set_output_stream(...)
        self.add_emission(...)
```

Key patterns:

- `run()`: Core calculation logic, called during field iteration
- Input/output stream handling via `find_input_stream()`, `set_output_stream()`
- Energy calculations with proper unit handling (Pint library)
- Emission tracking via `add_emission()`

Process calculations execute in dependency order, with cyclic process support for iterative convergence.

## Testing Strategy

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=opgee

# Run specific test file
uv run pytest tests/test_field.py
```

Test fixtures are in `tests/files/`:

- XML model files for integration testing
- `opgee.cfg` configuration for test environment

**Test Configuration**: Tests require a config file. If tests fail with "Missing user config file":

```bash
cp tests/files/opgee.cfg ~/opgee.cfg
```

## Development Guidelines

### Incremental Development Approach

- **Small, focused changes**: Make incremental progress rather than large changes
- **Test integrity**: Maintain existing functionality throughout changes
- **Compile and pass tests**: Each change should result in working code
- **Single responsibility**: Each change should focus on one specific aspect
- **Learn from existing code**: Study patterns in the codebase before implementing

### Code Quality Standards

- Follow existing code patterns and conventions
- Maintain type hints and documentation standards
- Preserve existing error handling patterns
- Use absolute imports: `from opgee.error import OpgeeException`

### Architecture Analysis

Before major changes:

- Map dependencies and inheritance patterns
- Understand current usage patterns before changing interfaces
- Identify critical files and their relationships
- Document architectural decisions and rationale

## Refactoring Context

This branch (`refactor-v5`) represents a simplified version of OPGEE:

- **Removed**: `mcs/` (Monte Carlo simulation) package
- **Removed**: `gui/` (Dash web interface) package
- **Flat structure**: All core modules in `opgee/` root (no `core/` or `xml/` subpackages)

The codebase is actively maintained with all tests passing.

## Data Dependencies

- **CSV tables**: Emission factors, transport parameters, thermodynamic data
- **XML schemas**: Model validation and structure definition
- **External libraries**: pandas, numpy, scipy, pint (units), lxml

## Detailed Module Analysis

For in-depth documentation on core modules, see `.agents/docs/`:

- `field-analysis.md` - Field class, carbon intensity calculation, process graph management
- `process-analysis.md` - Process base class, stream handling, energy/emission tracking
- `thermodynamics-analysis.md` - Oil/Gas/Water classes, property correlations

## Git Workflow

**IMPORTANT**: Always push to `personal` remote, NEVER to `origin` or `upstream`.

```bash
git push personal <branch-name>
```

## Temporary Scripts

When writing longer (more than 10 lines) temporary or inline scripts in any language, write them to `.agents/tmp` before executing them.
