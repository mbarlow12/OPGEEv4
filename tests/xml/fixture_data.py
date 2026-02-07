"""Pre-built element trees and parametrize data for XML pipeline tests.

Composed using E_* factories from conftest.  Organized by pipeline stage.
"""

from tests.xml.conftest import (
    E_a,
    E_analysis,
    E_field,
    E_model,
    E_process,
    E_process_choice,
    E_process_group,
    E_process_ref,
    E_stream,
)


# ── Reusable model-level builders ─────────────────────────────


def model_with_field(*field_children, field_kw=None, analysis_children=None):
    """Build a full Model with one Analysis and one Field."""
    a_children = analysis_children or (E_a("functional_unit", "oil"),)
    fkw = field_kw or {}
    return E_model(
        E_analysis(*a_children),
        E_field(*field_children, **fkw),
    )


def minimal_field_children():
    """Minimum children for a valid Field: country attr + process + stream."""
    return (
        E_a("country", "US"),
        E_process("Separation"),
        E_stream("Reservoir", "Separation"),
    )


# ── Schema test parametrize data ──────────────────────────────

# (test_id, kwargs) for Process optional attributes
PROCESS_OPTIONAL_ATTRS = [
    ("name", {"name": "drill1"}),
    ("enabled", {"enabled": "0"}),
    ("boundary", {"boundary": "Production"}),
    ("after", {"after": "true"}),
    ("impute_start", {"impute_start": "1"}),
    ("cycle_start", {"cycle_start": "1"}),
    ("extend", {"extend": "1"}),
    ("delete", {"delete": "true"}),
    ("desc", {"desc": "A description"}),
]

# (test_id, kwargs) for Stream optional attributes
STREAM_OPTIONAL_ATTRS = [
    ("name", {"name": "gas_flow"}),
    ("impute", {"impute": "0"}),
    ("boundary", {"boundary": "Production"}),
    ("delete", {"delete": "true"}),
]

# (test_id, name, phase, value) for Component phases
COMPONENT_PHASES = [
    ("gas", "CH4", "gas", "0.95"),
    ("liquid", "C5", "liquid", "0.10"),
    ("solid", "ite", "solid", "0.01"),
]

# (test_id, kwargs) for AttrDef single optional attributes
ATTRDEF_SINGLE_ATTRS = [
    ("type", {"type": "int"}),
    ("unit", {"unit": "ft"}),
    ("desc", {"desc": "Age of field"}),
    ("exclusive", {"exclusive": "true"}),
    ("synchronized", {"synchronized": "partner"}),
]

# (test_id, kwargs) for AttrDef constraint attributes
ATTRDEF_CONSTRAINTS = [
    ("GT", {"GT": "0"}),
    ("GE", {"GE": "0"}),
    ("LT", {"LT": "1"}),
    ("LE", {"LE": "1"}),
    ("GT_and_LE", {"GT": "0", "LE": "1"}),
]

# (test_id, kwargs) for ProcessChoice optional attributes
PROCESS_CHOICE_ATTRS = [
    ("default", {"default": "All"}),
    ("extend", {"extend": "1"}),
    ("delete", {"delete": "true"}),
]

# (test_id, kwargs) for Field optional attributes (core schema)
FIELD_OPTIONAL_ATTRS = [
    ("enabled", {"enabled": "1"}),
    ("extend", {"extend": "1"}),
    ("delete", {"delete": "true"}),
]


# ── Process choices test data ─────────────────────────────────


def _choice_model(selection, *, extra_procs=(), extra_streams=()):
    """Build a Model with a gas_path ProcessChoice using the given selection."""
    return model_with_field(
        E_a("country", "US"),
        E_a("gas_path", selection),
        E_process_choice(
            "gas_path",
            E_process_group("None", E_process_ref("GasGathering")),
            E_process_group(
                "Minimal",
                E_process_ref("GasGathering"),
                E_process_ref("GasDehydration"),
            ),
        ),
        E_process("GasGathering"),
        E_process("GasDehydration"),
        *extra_procs,
        E_process("Separation"),
        E_stream("Reservoir", "Separation"),
        *extra_streams,
    )


# (test_id, selection, expected_present, expected_absent)
PROCESS_CHOICE_SCENARIOS = [
    ("select_minimal", "Minimal", ["GasGathering", "GasDehydration", "Separation"], []),
    ("select_none", "None", ["GasGathering", "Separation"], ["GasDehydration"]),
]


# ── Builder test data ─────────────────────────────────────────


def builder_model(*extra_field_children):
    """Build a Model suitable for builder tests."""
    return model_with_field(
        E_a("country", "US"),
        E_process("Separation"),
        E_stream("Reservoir", "Separation"),
        *extra_field_children,
    )
