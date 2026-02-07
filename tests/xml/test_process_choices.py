"""Tests for Stage 3: Process choice resolution."""

import pytest

from opgee.error import OpgeeException
from opgee.input.xml.process_choices import resolve_process_choices
from tests.xml.conftest import (
    E_a,
    E_aggregator,
    E_analysis,
    E_field,
    E_model,
    E_process,
    E_process_choice,
    E_process_group,
    E_process_ref,
    E_stream,
    E_stream_ref,
)
from tests.xml.fixture_data import (
    PROCESS_CHOICE_SCENARIOS,
    _choice_model,
    model_with_field,
)


class TestResolveProcessChoices:
    @pytest.mark.parametrize(
        "selection, expected_present, expected_absent",
        [
            pytest.param(sel, present, absent, id=tid)
            for tid, sel, present, absent in PROCESS_CHOICE_SCENARIOS
        ],
    )
    def test_process_choice_scenarios(
        self, selection, expected_present, expected_absent
    ):
        """Selected processes remain; non-selected processes are removed."""
        xml = _choice_model(selection)

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_classes = [p.get("class") for p in field.findall("Process")]
        for name in expected_present:
            assert name in proc_classes
        for name in expected_absent:
            assert name not in proc_classes

    def test_enabled_processes_remain(self):
        """Processes in the selected group should remain."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("gas_path", "All"),
            E_process_choice(
                "gas_path",
                E_process_group(
                    "All",
                    E_process_ref("GasGathering"),
                    E_process_ref("GasDehydration"),
                ),
                E_process_group("None"),
            ),
            E_process("GasGathering"),
            E_process("GasDehydration"),
            E_stream("Reservoir", "GasGathering"),
        )

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_classes = [p.get("class") for p in field.findall("Process")]
        assert "GasGathering" in proc_classes
        assert "GasDehydration" in proc_classes

    def test_stream_disabled_with_process(self):
        """Streams referenced by non-selected group should be removed."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("gas_path", "None"),
            E_process_choice(
                "gas_path",
                E_process_group("None", E_process_ref("GasGathering")),
                E_process_group(
                    "Minimal",
                    E_process_ref("GasGathering"),
                    E_process_ref("GasDehydration"),
                    E_stream_ref("GasGathering => GasDehydration"),
                ),
            ),
            E_process("GasGathering"),
            E_process("GasDehydration"),
            E_stream("GasGathering", "GasDehydration"),
            E_stream("Reservoir", "GasGathering"),
        )

        resolve_process_choices(xml)

        field = xml.find("Field")
        stream_names = []
        for s in field.findall("Stream"):
            name = s.get("name") or f"{s.get('src')} => {s.get('dst')}"
            stream_names.append(name)

        assert "GasGathering => GasDehydration" not in stream_names

    def test_error_on_enabled_stream_referencing_disabled_process(self):
        """Should raise error if enabled stream references a disabled process."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("gas_path", "None"),
            E_process_choice(
                "gas_path",
                E_process_group("None"),
                E_process_group("All", E_process_ref("GasDehydration")),
            ),
            E_process("GasDehydration"),
            E_stream("GasDehydration", "Separation"),
            E_process("Separation"),
        )

        with pytest.raises(OpgeeException, match="disabled"):
            resolve_process_choices(xml)

    def test_no_process_choice_in_output(self):
        """Output should not contain ProcessChoice/ProcessGroup elements."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("gas_path", "All"),
            E_process_choice(
                "gas_path",
                E_process_group("All", E_process_ref("GasGathering")),
            ),
            E_process("GasGathering"),
            E_stream("Reservoir", "GasGathering"),
        )

        resolve_process_choices(xml)

        field = xml.find("Field")
        assert field.findall("ProcessChoice") == []
        assert field.findall("ProcessGroup") == []
        assert field.findall("ProcessRef") == []
        assert field.findall("StreamRef") == []

    def test_nested_process_choice(self):
        """Nested ProcessChoice within selected group should be resolved."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("outer_choice", "GroupA"),
            E_a("inner_choice", "Inner1"),
            E_process_choice(
                "outer_choice",
                E_process_group(
                    "GroupA",
                    E_process_ref("ProcA"),
                    E_process_choice(
                        "inner_choice",
                        E_process_group("Inner1", E_process_ref("ProcB")),
                        E_process_group("Inner2", E_process_ref("ProcC")),
                    ),
                ),
                E_process_group("GroupB", E_process_ref("ProcD")),
            ),
            E_process("ProcA", name="ProcA"),
            E_process("ProcB", name="ProcB"),
            E_process("ProcC", name="ProcC"),
            E_process("ProcD", name="ProcD"),
            E_stream("Reservoir", "ProcA"),
        )

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_names = [p.get("name") or p.get("class") for p in field.findall("Process")]
        assert "ProcA" in proc_names  # selected in outer
        assert "ProcB" in proc_names  # selected in inner
        assert "ProcC" not in proc_names  # not selected in inner
        assert "ProcD" not in proc_names  # not selected in outer

    def test_aggregator_stripped(self):
        """Aggregator elements should be removed from output."""
        xml = model_with_field(
            E_a("country", "US"),
            E_aggregator("Upstream", E_process("Drilling")),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        )

        resolve_process_choices(xml)

        field = xml.find("Field")
        assert field.findall("Aggregator") == []

    def test_validates_against_core_schema(self, core_schema):
        """Output should validate against opgee_core.xsd."""
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_a("gas_path", "All"),
                E_process_choice(
                    "gas_path",
                    E_process_group("All", E_process_ref("GasGathering")),
                ),
                E_process("GasGathering"),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )

        resolve_process_choices(xml)

        assert core_schema.validate(xml), core_schema.error_log
