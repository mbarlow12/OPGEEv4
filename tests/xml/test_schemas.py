"""Test pydantic-xml model validation for pre-pipeline and post-pipeline XML."""

import pytest
from lxml import etree
from pydantic import ValidationError

from opgee.input.xml.models import (
    AttrDefsElement,
    CoreModel,
    ExtModel,
)
from tests.xml.conftest import (
    E_a,
    E_aggregator,
    E_analysis,
    E_attr_def,
    E_attr_defs,
    E_class_attrs,
    E_component,
    E_contains,
    E_field,
    E_field_ref,
    E_group,
    E_model,
    E_option,
    E_options,
    E_process,
    E_process_choice,
    E_process_group,
    E_process_ref,
    E_stream,
    E_stream_ref,
)
from tests.xml.fixture_data import (
    ATTRDEF_CONSTRAINTS,
    ATTRDEF_SINGLE_ATTRS,
    COMPONENT_PHASES,
    FIELD_OPTIONAL_ATTRS,
    PROCESS_CHOICE_ATTRS,
    PROCESS_OPTIONAL_ATTRS,
    STREAM_OPTIONAL_ATTRS,
)


# ── helpers ────────────────────────────────────────────────────


def _valid_field(*extra_children: etree._Element, **kw) -> etree._Element:
    """Field with the minimum children to be valid in both schemas."""
    return E_field(
        E_a("country", "US"),
        E_process("Separation"),
        E_stream("Reservoir", "Separation"),
        *extra_children,
        **kw,
    )


def _core_model(
    *extra_field_children: etree._Element,
    field_kw: dict | None = None,
    extra_model_children: tuple = (),
) -> etree._Element:
    """Minimal Model valid against core schema, with optional extras."""
    fkw = field_kw or {}
    return E_model(
        E_analysis(E_a("functional_unit", "oil")),
        _valid_field(*extra_field_children, **fkw),
        *extra_model_children,
    )


# =====================================================================
# Core model (CoreModel — post-pipeline, no ProcessChoice)
# =====================================================================


class TestCoreModel:
    """Tests for CoreModel (post-pipeline output, no ProcessChoice)."""

    def test_validates_clean_output(self):
        xml = _core_model()
        CoreModel.from_xml_tree(xml)

    def test_rejects_process_choice_in_clean_output(self):
        xml = _core_model(
            E_process_choice("gas_processing_path", E_process_group("All")),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_aggregator_in_clean_output(self):
        xml = _core_model(E_aggregator("Upstream", E_process("Drilling")))
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_validates_with_explicit_attr(self):
        xml = _core_model(E_a("depth", "5000", explicit="true"))
        CoreModel.from_xml_tree(xml)

    def test_validates_model_with_schema_version(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(),
            schema_version="4.0",
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_model_with_multiple_fields(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(name="field1"),
            _valid_field(name="field2"),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_model_with_multiple_analyses(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), name="a1"),
            E_analysis(E_a("functional_unit", "gas"), name="a2"),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_model_with_top_level_a(self):
        xml = E_model(
            E_a("some_setting", "value"),
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_empty_model(self):
        xml = E_model()
        CoreModel.from_xml_tree(xml)

    def test_validates_with_valid_core_model_fixture(self, valid_core_model):
        CoreModel.from_xml_tree(valid_core_model)


class TestCoreModelAnalysis:
    """Tests for <Analysis> in CoreModel."""

    def test_validates_with_field_ref(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), E_field_ref("test")),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_group(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), E_group("offshore")),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_group_regex(self):
        xml = E_model(
            E_analysis(
                E_a("functional_unit", "oil"),
                E_group("field_.*", regex="1"),
            ),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_multiple_a(self):
        xml = E_model(
            E_analysis(
                E_a("functional_unit", "oil"),
                E_a("GWP_horizon", "100"),
                E_a("GWP_version", "AR5"),
            ),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_delete_attr(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), delete="true"),
            _valid_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_empty_analysis(self):
        xml = E_model(E_analysis(), _valid_field())
        CoreModel.from_xml_tree(xml)

    def test_rejects_invalid_child_element(self):
        proc = E_process("Separation")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), proc),
            _valid_field(),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


class TestCoreModelField:
    """Tests for <Field> in CoreModel."""

    @pytest.mark.parametrize(
        "attr_id,kw",
        FIELD_OPTIONAL_ATTRS,
        ids=[x[0] for x in FIELD_OPTIONAL_ATTRS],
    )
    def test_validates_with_optional_attr(self, attr_id, kw):
        xml = _core_model(field_kw=kw)
        CoreModel.from_xml_tree(xml)

    def test_validates_with_group_child(self):
        xml = _core_model(E_group("onshore"))
        CoreModel.from_xml_tree(xml)

    def test_validates_empty_field(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(),
        )
        CoreModel.from_xml_tree(xml)

    def test_rejects_field_without_name(self):
        field = etree.Element("Field")
        field.append(E_process("Separation"))
        xml = E_model(E_analysis(E_a("functional_unit", "oil")), field)
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_modifies_attr_in_core(self):
        xml = _core_model(field_kw={"modifies": "base"})
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_modified_attr_in_core(self):
        xml = _core_model(field_kw={"modified": "overlay"})
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


class TestCoreModelProcess:
    """Tests for <Process> in CoreModel."""

    def test_validates_minimal(self):
        xml = _core_model()
        CoreModel.from_xml_tree(xml)

    @pytest.mark.parametrize(
        "attr_id,kw",
        PROCESS_OPTIONAL_ATTRS,
        ids=[x[0] for x in PROCESS_OPTIONAL_ATTRS],
    )
    def test_validates_with_optional_attr(self, attr_id, kw):
        xml = _core_model(E_process("Drilling", **kw))
        CoreModel.from_xml_tree(xml)

    def test_validates_with_all_attrs(self):
        xml = _core_model(
            E_process(
                "Drilling",
                name="drill",
                enabled="1",
                boundary="Production",
                after="true",
                impute_start="0",
                cycle_start="0",
                extend="0",
                delete="false",
                desc="fully loaded",
            ),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_a_children(self):
        xml = _core_model(
            E_process("Drilling", E_a("fracturing", "true"), E_a("depth", "5000")),
        )
        CoreModel.from_xml_tree(xml)

    def test_rejects_missing_class(self):
        proc = etree.Element("Process")  # no class attr
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), proc, E_stream("Reservoir", "Separation")),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_invalid_class(self):
        proc = etree.Element("Process")
        proc.set("class", "NotARealProcess")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), proc, E_stream("Reservoir", "Separation")),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


class TestCoreModelStream:
    """Tests for <Stream> in CoreModel."""

    def test_validates_minimal(self):
        xml = _core_model()
        CoreModel.from_xml_tree(xml)

    @pytest.mark.parametrize(
        "attr_id,kw",
        STREAM_OPTIONAL_ATTRS,
        ids=[x[0] for x in STREAM_OPTIONAL_ATTRS],
    )
    def test_validates_with_optional_attr(self, attr_id, kw):
        xml = _core_model(E_stream("A", "B", **kw))
        CoreModel.from_xml_tree(xml)

    def test_validates_with_component(self):
        xml = _core_model(
            E_stream("A", "B", E_component("CH4", "gas", "0.95")),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_multiple_components(self):
        xml = _core_model(
            E_stream(
                "A",
                "B",
                E_component("CH4", "gas", "0.85"),
                E_component("C2H6", "gas", "0.10"),
                E_component("C3H8", "liquid", "0.05"),
            ),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_contains(self):
        xml = _core_model(
            E_stream("A", "B", E_contains("oil")),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_a_child(self):
        xml = _core_model(
            E_stream("A", "B", E_a("temperature", "100")),
        )
        CoreModel.from_xml_tree(xml)

    def test_validates_with_all_children(self):
        xml = _core_model(
            E_stream(
                "A",
                "B",
                E_a("temperature", "100"),
                E_component("CH4", "gas", "0.90"),
                E_contains("gas"),
                name="full_stream",
                impute="1",
                boundary="Production",
            ),
        )
        CoreModel.from_xml_tree(xml)

    def test_rejects_missing_src(self):
        stream = etree.Element("Stream")
        stream.set("dst", "Separation")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), E_process("Separation"), stream),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_missing_dst(self):
        stream = etree.Element("Stream")
        stream.set("src", "Reservoir")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), E_process("Separation"), stream),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_stream_with_too_many_a_children(self):
        """Issue 6: Stream with >3 A children should fail validation."""
        xml = _core_model(
            E_stream(
                "A", "B",
                E_a("t1", "1"), E_a("t2", "2"), E_a("t3", "3"), E_a("t4", "4"),
            ),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


class TestCoreModelComponent:
    """Tests for <Component> in CoreModel."""

    @pytest.mark.parametrize(
        "phase_id,name,phase,value",
        COMPONENT_PHASES,
        ids=[x[0] for x in COMPONENT_PHASES],
    )
    def test_validates_phase(self, phase_id, name, phase, value):
        xml = _core_model(E_stream("A", "B", E_component(name, phase, value)))
        CoreModel.from_xml_tree(xml)

    def test_rejects_invalid_phase(self):
        xml = _core_model(E_stream("A", "B", E_component("CH4", "plasma", "0.5")))
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_missing_name(self):
        comp = etree.Element("Component")
        comp.set("phase", "gas")
        comp.text = "0.5"
        s = E_stream("A", "B")
        s.append(comp)
        xml = _core_model(s)
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_rejects_missing_phase(self):
        comp = etree.Element("Component")
        comp.set("name", "CH4")
        comp.text = "0.5"
        s = E_stream("A", "B")
        s.append(comp)
        xml = _core_model(s)
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


class TestCoreModelA:
    """Tests for <A> in CoreModel."""

    def test_validates_minimal(self):
        xml = _core_model(E_a("depth", "5000"))
        CoreModel.from_xml_tree(xml)

    def test_validates_explicit_true(self):
        xml = _core_model(E_a("depth", "5000", explicit="true"))
        CoreModel.from_xml_tree(xml)

    def test_validates_explicit_false(self):
        xml = _core_model(E_a("depth", "5000", explicit="false"))
        CoreModel.from_xml_tree(xml)

    def test_validates_with_delete(self):
        xml = _core_model(E_a("depth", "5000", delete="true"))
        CoreModel.from_xml_tree(xml)

    def test_rejects_missing_name(self):
        a = etree.Element("A")
        a.text = "value"
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(a, E_process("Separation"), E_stream("Reservoir", "Separation")),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


# =====================================================================
# Ext model (ExtModel — pre-pipeline, with ProcessChoice/Aggregator)
# =====================================================================


class TestExtModel:
    """Tests for ExtModel (pre-pipeline input with ProcessChoice etc.)"""

    def test_validates_raw_input_with_process_choice(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "gas_processing_path",
                    E_process_group(
                        "All",
                        E_process_ref("GasGathering"),
                        E_stream_ref("gas to dehydration"),
                    ),
                    E_process_group("None"),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_aggregator(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_field_with_modifies(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(modifies="base_field"),
        )
        ExtModel.from_xml_tree(xml)

    def test_rejects_invalid_element_with_content(self):
        field = E_field()
        inv = etree.SubElement(field, "InvalidElement")
        inv.set("foo", "bar")
        xml = E_model(E_analysis(E_a("functional_unit", "oil")), field)
        with pytest.raises(ValidationError):
            ExtModel.from_xml_tree(xml)

    def test_validates_field_with_modified(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(modified="overlay_field"),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_field_with_modifies_and_modified(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(modifies="base", modified="overlay"),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_multiple_process_choices(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("gas_path", E_process_group("All")),
                E_process_choice("oil_path", E_process_group("Heavy")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)


class TestExtModelProcessChoice:
    """Tests for <ProcessChoice> in ExtModel."""

    def test_validates_minimal(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("gas_path", E_process_group("All")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    @pytest.mark.parametrize(
        "attr_id,kw",
        PROCESS_CHOICE_ATTRS,
        ids=[x[0] for x in PROCESS_CHOICE_ATTRS],
    )
    def test_validates_with_optional_attr(self, attr_id, kw):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("gas_path", E_process_group("All"), **kw),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_multiple_groups(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "gas_path",
                    E_process_group("All"),
                    E_process_group("None"),
                    E_process_group("Partial"),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_rejects_missing_name(self):
        pc = etree.Element("ProcessChoice")
        pc.append(E_process_group("All"))
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                pc,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        with pytest.raises(ValidationError):
            ExtModel.from_xml_tree(xml)

    def test_rejects_no_groups(self):
        pc = E_process_choice("gas_path")  # no groups
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                pc,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        with pytest.raises(ValidationError):
            ExtModel.from_xml_tree(xml)


class TestExtModelProcessGroup:
    """Tests for <ProcessGroup> in ExtModel."""

    def test_validates_with_process_ref_only(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "path",
                    E_process_group("All", E_process_ref("Separation")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_stream_ref_only(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "path",
                    E_process_group("All", E_stream_ref("gas to dehydration")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_nested_process_choice(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "outer",
                    E_process_group(
                        "All",
                        E_process_choice(
                            "inner",
                            E_process_group("SubAll", E_process_ref("Drilling")),
                        ),
                    ),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_mixed_children(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "path",
                    E_process_group(
                        "All",
                        E_process_ref("Drilling"),
                        E_stream_ref("gas line"),
                        E_process_ref("Separation"),
                    ),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_empty_group(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("path", E_process_group("Empty")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_rejects_missing_name(self):
        pg = etree.Element("ProcessGroup")
        pg.append(E_process_ref("Drilling"))
        pc = E_process_choice("path")
        pc.append(pg)
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                pc,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        with pytest.raises(ValidationError):
            ExtModel.from_xml_tree(xml)


class TestExtModelProcessRef:
    """Tests for <ProcessRef> in ExtModel."""

    def test_validates_with_name(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("p", E_process_group("G", E_process_ref("Drill"))),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_class(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group("G", E_process_ref(cls="Drilling")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_name_and_class(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group(
                        "G",
                        E_process_ref("drill1", cls="Drilling"),
                    ),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_delete(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group(
                        "G",
                        E_process_ref("Drill", delete="true"),
                    ),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_no_attrs(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("p", E_process_group("G", E_process_ref())),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)


class TestExtModelStreamRef:
    """Tests for <StreamRef> in ExtModel."""

    def test_validates_minimal(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group("G", E_stream_ref("gas line")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_delete(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group("G", E_stream_ref("gas line", delete="true")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_rejects_missing_name(self):
        sr = etree.Element("StreamRef")
        pg = E_process_group("G")
        pg.append(sr)
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("p", pg),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        with pytest.raises(ValidationError):
            ExtModel.from_xml_tree(xml)


class TestExtModelAggregator:
    """Tests for <Aggregator> in ExtModel."""

    def test_validates_with_process(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_process_ref(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process_ref("Drilling")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_nested_aggregator(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator(
                    "Outer",
                    E_aggregator("Inner", E_process("Drilling")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_a_child(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_a("weight", "0.5")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_process_choice(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator(
                    "Upstream",
                    E_process_choice("sub", E_process_group("All")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_enabled(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling"), enabled="0"),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)

    def test_validates_with_delete(self):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling"), delete="true"),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        ExtModel.from_xml_tree(xml)


class TestExtModelCrossValidation:
    """Cross-model validation tests."""

    def test_core_valid_xml_passes_ext(self):
        """Core-valid XML should also pass ext validation (ext is a superset)."""
        xml = _core_model()
        CoreModel.from_xml_tree(xml)
        ExtModel.from_xml_tree(xml)

    def test_process_choice_rejected_by_core(self):
        """ProcessChoice is an ext-only element; core should reject it."""
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("p", E_process_group("G", E_process_ref("Drill"))),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)

    def test_aggregator_rejected_by_core(self):
        """Aggregator is an ext-only element; core should reject it."""
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        with pytest.raises(ValidationError):
            CoreModel.from_xml_tree(xml)


# =====================================================================
# AttrDefs model (AttrDefsElement)
# =====================================================================


class TestAttrDefsModel:
    """Tests for AttrDefsElement."""

    def test_validates_attr_defs_structure(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type",
                    "conventional",
                    E_option("conventional"),
                    E_option("heavy", label="heavy"),
                ),
                E_attr_def("age", "25", type="int", unit="yr"),
                E_attr_def("country", "USA", type="str"),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_rejects_missing_class_name(self):
        ca = etree.Element("ClassAttrs")
        ca.append(E_attr_def("age", "25", type="int"))
        xml = E_attr_defs(ca)
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)

    def test_validates_real_attributes_xml(self, attr_defs_elt):
        AttrDefsElement.from_xml_tree(attr_defs_elt)

    def test_validates_multiple_class_attrs(self):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("depth", "5000", type="float")),
            E_class_attrs("Analysis", E_attr_def("GWP", "100", type="int")),
            E_class_attrs("Model", E_attr_def("version", "4", type="str")),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_empty_class_attrs(self):
        xml = E_attr_defs(E_class_attrs("Field"))
        AttrDefsElement.from_xml_tree(xml)


class TestAttrDefsModelAttrDef:
    """Tests for <AttrDef> in AttrDefsElement."""

    @pytest.mark.parametrize(
        "attr_id,kw",
        ATTRDEF_SINGLE_ATTRS,
        ids=[x[0] for x in ATTRDEF_SINGLE_ATTRS],
    )
    def test_validates_with_single_attr(self, attr_id, kw):
        xml = E_attr_defs(E_class_attrs("Field", E_attr_def("test_field", "25", **kw)))
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_with_options_ref(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options("oil_type", "conventional", E_option("conventional")),
                E_attr_def("oil_type", "conventional", options="oil_type"),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    @pytest.mark.parametrize(
        "constraint_id,kw",
        ATTRDEF_CONSTRAINTS,
        ids=[x[0] for x in ATTRDEF_CONSTRAINTS],
    )
    def test_validates_with_constraint(self, constraint_id, kw):
        xml = E_attr_defs(E_class_attrs("Field", E_attr_def("depth", "100", **kw)))
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_default_value_as_text(self):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("name", "default_value")),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_with_all_attrs(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_attr_def(
                    "depth",
                    "5000",
                    type="float",
                    unit="ft",
                    desc="Well depth",
                    options="depth_range",
                    exclusive="true",
                    synchronized="partner",
                    GT="0",
                    LE="50000",
                ),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_no_default_value(self):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("optional_field")),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_rejects_missing_name(self):
        ad = etree.Element("AttrDef")
        ad.text = "25"
        ad.set("type", "int")
        ca = E_class_attrs("Field")
        ca.append(ad)
        xml = E_attr_defs(ca)
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)

    def test_rejects_non_decimal_GT(self):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("depth", "100", GT="not_a_number")),
        )
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)

    def test_rejects_invalid_attrdef_type(self):
        """Issue 9: AttrDef with type='bogus' should fail."""
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("depth", "100", type="bogus")),
        )
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)


class TestAttrDefsModelOptions:
    """Tests for <Options> and <Option> in AttrDefsElement."""

    def test_validates_minimal(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options("oil_type", "conventional", E_option("conventional")),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_option_with_label(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type",
                    "conventional",
                    E_option("conventional", label="Conventional Oil"),
                ),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_option_with_desc(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type",
                    "conventional",
                    E_option("conventional", desc="Standard crude"),
                ),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_validates_multiple_options(self):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type",
                    "conventional",
                    E_option("conventional"),
                    E_option("heavy", label="Heavy"),
                    E_option("light", desc="Light crude"),
                ),
            ),
        )
        AttrDefsElement.from_xml_tree(xml)

    def test_rejects_options_missing_name(self):
        opts = etree.Element("Options")
        opts.set("default", "conventional")
        opts.append(E_option("conventional"))
        ca = E_class_attrs("Field")
        ca.append(opts)
        xml = E_attr_defs(ca)
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)

    def test_rejects_options_missing_default(self):
        opts = etree.Element("Options")
        opts.set("name", "oil_type")
        opts.append(E_option("conventional"))
        ca = E_class_attrs("Field")
        ca.append(opts)
        xml = E_attr_defs(ca)
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)

    def test_rejects_options_empty(self):
        opts = etree.Element("Options")
        opts.set("name", "oil_type")
        opts.set("default", "conventional")
        ca = E_class_attrs("Field")
        ca.append(opts)
        xml = E_attr_defs(ca)
        with pytest.raises(ValidationError):
            AttrDefsElement.from_xml_tree(xml)
