# Minor Process spec deviations (cosmetic)

**Severity:** Minor
**Location:** `opgee/process.py` (various)

## Problem
Two small divergences from spec §4.1:
1. Spec named the stream collections `self.input_streams` / `self.output_streams`; implementation uses `self.inputs` / `self.outputs`. Consistent internally; harmless.
2. Spec typed `self.intermediate_results: IntermediateValues`; implementation has `self.intermediate_results: dict | None = None` populated later by `init_intermediate_results()` as a plain `dict`. The `IntermediateValues` inner class exists but is never used.

## Suggested fix
- Decide whether to rename `inputs`/`outputs` → `input_streams`/`output_streams`, or update the spec to match the impl.
- Either wire `IntermediateValues` as the actual container type, or delete the unused inner class.
