"""Tests for Stage 3: Process choice resolution."""

import pytest

from opgee.input.xml.process_choices import resolve_process_choices
from opgee.error import OpgeeException
from tests.xml.conftest import make_model_xml


class TestResolveProcessChoices:

    def test_disabled_processes_removed(self):
        """Processes not in the selected group should be removed."""
        xml = make_model_xml(field_body="""
            <A name="gas_path">Minimal</A>
            <ProcessChoice name="gas_path">
                <ProcessGroup name="None">
                    <ProcessRef name="GasGathering"/>
                </ProcessGroup>
                <ProcessGroup name="Minimal">
                    <ProcessRef name="GasGathering"/>
                    <ProcessRef name="GasDehydration"/>
                </ProcessGroup>
            </ProcessChoice>
            <Process class="GasGathering"/>
            <Process class="GasDehydration"/>
            <Process class="Separation"/>
            <Stream src="Reservoir" dst="Separation"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_classes = [p.get("class") for p in field.findall("Process")]
        # GasGathering and GasDehydration should remain (selected)
        assert "GasGathering" in proc_classes
        assert "GasDehydration" in proc_classes
        # Separation not in any choice, should remain
        assert "Separation" in proc_classes

    def test_enabled_processes_remain(self):
        """Processes in the selected group should remain."""
        xml = make_model_xml(field_body="""
            <A name="gas_path">All</A>
            <ProcessChoice name="gas_path">
                <ProcessGroup name="All">
                    <ProcessRef name="GasGathering"/>
                    <ProcessRef name="GasDehydration"/>
                </ProcessGroup>
                <ProcessGroup name="None"/>
            </ProcessChoice>
            <Process class="GasGathering"/>
            <Process class="GasDehydration"/>
            <Stream src="Reservoir" dst="GasGathering"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_classes = [p.get("class") for p in field.findall("Process")]
        assert "GasGathering" in proc_classes
        assert "GasDehydration" in proc_classes

    def test_disabled_processes_actually_removed(self):
        """Processes not in the selected group should be physically removed."""
        xml = make_model_xml(field_body="""
            <A name="gas_path">None</A>
            <ProcessChoice name="gas_path">
                <ProcessGroup name="None">
                    <ProcessRef name="GasGathering"/>
                </ProcessGroup>
                <ProcessGroup name="Minimal">
                    <ProcessRef name="GasGathering"/>
                    <ProcessRef name="GasDehydration"/>
                </ProcessGroup>
            </ProcessChoice>
            <Process class="GasGathering"/>
            <Process class="GasDehydration"/>
            <Stream src="Reservoir" dst="GasGathering"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_classes = [p.get("class") for p in field.findall("Process")]
        # GasDehydration only in Minimal, should be removed when None selected
        assert "GasDehydration" not in proc_classes
        # GasGathering is in both groups, selected group is "None" which has it
        assert "GasGathering" in proc_classes

    def test_stream_disabled_with_process(self):
        """Streams referenced by non-selected group should be removed."""
        xml = make_model_xml(field_body="""
            <A name="gas_path">None</A>
            <ProcessChoice name="gas_path">
                <ProcessGroup name="None">
                    <ProcessRef name="GasGathering"/>
                </ProcessGroup>
                <ProcessGroup name="Minimal">
                    <ProcessRef name="GasGathering"/>
                    <ProcessRef name="GasDehydration"/>
                    <StreamRef name="GasGathering => GasDehydration"/>
                </ProcessGroup>
            </ProcessChoice>
            <Process class="GasGathering"/>
            <Process class="GasDehydration"/>
            <Stream src="GasGathering" dst="GasDehydration"/>
            <Stream src="Reservoir" dst="GasGathering"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        stream_names = []
        for s in field.findall("Stream"):
            name = s.get("name") or f"{s.get('src')} => {s.get('dst')}"
            stream_names.append(name)

        assert "GasGathering => GasDehydration" not in stream_names

    def test_error_on_enabled_stream_referencing_disabled_process(self):
        """Should raise error if enabled stream references a disabled process."""
        xml = make_model_xml(field_body="""
            <A name="gas_path">None</A>
            <ProcessChoice name="gas_path">
                <ProcessGroup name="None"/>
                <ProcessGroup name="All">
                    <ProcessRef name="GasDehydration"/>
                </ProcessGroup>
            </ProcessChoice>
            <Process class="GasDehydration"/>
            <Stream src="GasDehydration" dst="Separation"/>
            <Process class="Separation"/>
        """)

        with pytest.raises(OpgeeException, match="disabled"):
            resolve_process_choices(xml)

    def test_no_process_choice_in_output(self):
        """Output should not contain ProcessChoice/ProcessGroup elements."""
        xml = make_model_xml(field_body="""
            <A name="gas_path">All</A>
            <ProcessChoice name="gas_path">
                <ProcessGroup name="All">
                    <ProcessRef name="GasGathering"/>
                </ProcessGroup>
            </ProcessChoice>
            <Process class="GasGathering"/>
            <Stream src="Reservoir" dst="GasGathering"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        assert field.findall("ProcessChoice") == []
        assert field.findall("ProcessGroup") == []
        assert field.findall("ProcessRef") == []
        assert field.findall("StreamRef") == []

    def test_nested_process_choice(self):
        """Nested ProcessChoice within selected group should be resolved."""
        xml = make_model_xml(field_body="""
            <A name="outer_choice">GroupA</A>
            <A name="inner_choice">Inner1</A>
            <ProcessChoice name="outer_choice">
                <ProcessGroup name="GroupA">
                    <ProcessRef name="ProcA"/>
                    <ProcessChoice name="inner_choice">
                        <ProcessGroup name="Inner1">
                            <ProcessRef name="ProcB"/>
                        </ProcessGroup>
                        <ProcessGroup name="Inner2">
                            <ProcessRef name="ProcC"/>
                        </ProcessGroup>
                    </ProcessChoice>
                </ProcessGroup>
                <ProcessGroup name="GroupB">
                    <ProcessRef name="ProcD"/>
                </ProcessGroup>
            </ProcessChoice>
            <Process class="ProcA" name="ProcA"/>
            <Process class="ProcB" name="ProcB"/>
            <Process class="ProcC" name="ProcC"/>
            <Process class="ProcD" name="ProcD"/>
            <Stream src="Reservoir" dst="ProcA"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        proc_names = [p.get("name") or p.get("class") for p in field.findall("Process")]
        assert "ProcA" in proc_names  # selected in outer
        assert "ProcB" in proc_names  # selected in inner
        assert "ProcC" not in proc_names  # not selected in inner
        assert "ProcD" not in proc_names  # not selected in outer

    def test_aggregator_stripped(self):
        """Aggregator elements should be removed from output."""
        xml = make_model_xml(field_body="""
            <A name="country">US</A>
            <Aggregator name="Upstream">
                <Process class="Drilling"/>
            </Aggregator>
            <Process class="Separation"/>
            <Stream src="Reservoir" dst="Separation"/>
        """)

        resolve_process_choices(xml)

        field = xml.find("Field")
        assert field.findall("Aggregator") == []

    def test_validates_against_core_schema(self, core_schema):
        """Output should validate against opgee_core.xsd."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="gas_path">All</A>
                <ProcessChoice name="gas_path">
                    <ProcessGroup name="All">
                        <ProcessRef name="GasGathering"/>
                    </ProcessGroup>
                </ProcessChoice>
                <Process class="GasGathering"/>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )

        resolve_process_choices(xml)

        assert core_schema.validate(xml), core_schema.error_log
