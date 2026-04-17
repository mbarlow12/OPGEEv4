# Deep Clean Proposal: `opgee/error.py`

## Summary

`error.py` defines 12 exception classes. Several are tied to removed subsystems (MCS, distributed execution, CLI, config, XML parsing). The core LCA simulation classes (iteration control, validation, balance errors, zero-energy-flow) are used by retained modules and must stay.

---

## RETAIN

| Symbol | Used By (retained modules) | Purpose |
|---|---|---|
| `OpgeeException` | Everywhere -- base exception for the entire package. | Root exception class. |
| `OpgeeStopIteration` | `field.py` (catch in run loop) | Parent of iteration-control exceptions. |
| `OpgeeMaxIterationsReached` | `field.py` (raised when max iterations exceeded) | Signals iteration limit hit. |
| `OpgeeIterationConverged` | `field.py`, `process.py` (raised/caught during cycle convergence) | Signals successful convergence. |
| `AbstractMethodError` | `core.py` (`XmlInstantiable.from_xml`), `process.py` (`Process.run`) | Enforces subclass contract for abstract methods. |
| `ModelValidationError` | `field.py`, `process.py`, `stream.py`, `core.py`, `thermodynamics.py`, `attributes.py` | Raised during model validation (constraints, missing streams, bad API gravity, etc.). |
| `BalanceError` | `processes/steam_generation.py` | Mass/energy balance failure in process calculations. |
| `ZeroEnergyFlowError` | `field.py`, `results.py` | Zero energy at system boundary prevents CI calculation. |

---

## DROP

| Symbol | Reason |
|---|---|
| `McsUserError` | MCS subsystem removed. Used only in `post_processor.py` (DROP) and `manager.py` (DROP). |
| `McsSystemError` | MCS subsystem removed. Used only in `manager.py` (DROP). |
| `DistributionSpecError` | MCS subsystem removed. Zero consumers anywhere in the codebase (not even tests). |
| `RemoteError` | Distributed execution removed. Zero consumers in source code (only defined, never raised or caught). |
| `CommandlineError` | CLI removed. Used only in `tool.py` (DROP), `model.py` CLI path (DROP), and `built_ins/*.py` (DROP). |
| `ConfigFileError` | Config system removed. Used only in `config.py` (DROP). |
| `XmlFormatError` | XML parsing removed. Used only in `model_file.py` (DROP), `XMLFile.py` (DROP), and `built_ins/update_plugin.py` (DROP). |
| `FileFormatError` | Parent of `XmlFormatError` and `ConfigFileError`, both dropped. No direct consumers. |

---

## FINALIZED UNCERTAIN → DROP

| Symbol | Decision |
|---|---|
| `AttributeError` (custom) | **DROPPED.** `attributes.py` is dropped, so this exception has no consumer. Shadows Python builtin — dangerous. Can be re-added with proper naming if needed later. |

---

## Refactoring Notes

1. **`AttributeError` naming conflict** -- this custom class shadows Python's built-in `AttributeError`. Any code that does `from opgee.error import AttributeError` silently replaces the built-in. This is a latent bug source. Rename to `AttrDefError` or `AttributeDefinitionError` if retained.
2. **`FileFormatError` hierarchy collapses** -- with `XmlFormatError` and `ConfigFileError` both dropped, the intermediate `FileFormatError` class has no subclasses or direct consumers. Drop the entire branch.
3. **Resulting file** will contain 8 exception classes (down from 12), all directly tied to LCA simulation: `OpgeeException`, `OpgeeStopIteration`, `OpgeeMaxIterationsReached`, `OpgeeIterationConverged`, `AbstractMethodError`, `AttributeError` (renamed), `ModelValidationError`, `BalanceError`, `ZeroEnergyFlowError`.
4. **Clean hierarchy** after refactor:
   ```
   OpgeeException
   +-- OpgeeStopIteration
   |   +-- OpgeeMaxIterationsReached
   |   +-- OpgeeIterationConverged
   +-- AbstractMethodError
   +-- AttrDefError (renamed from AttributeError)
   +-- ModelValidationError
   +-- BalanceError
   +-- ZeroEnergyFlowError
   ```
