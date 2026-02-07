"""Test XSD schema validation for pre-pipeline and post-pipeline XML."""

from lxml import etree

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
    make_model_xml,
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


def _core_model(*extra_field_children: etree._Element,
                field_kw: dict | None = None,
                extra_model_children: tuple = ()) -> etree._Element:
    """Minimal Model valid against core schema, with optional extras."""
    fkw = field_kw or {}
    return E_model(
        E_analysis(E_a("functional_unit", "oil")),
        _valid_field(*extra_field_children, **fkw),
        *extra_model_children,
    )


# =====================================================================
# Core schema (opgee_core.xsd)
# =====================================================================

class TestCoreSchema:
    """Tests for opgee_core.xsd (post-pipeline output, no ProcessChoice)."""

    # ── existing tests (migrated to factories) ──

    def test_validates_clean_output(self, core_schema):
        xml = _core_model()
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_process_choice_in_clean_output(self, core_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <ProcessChoice name="gas_processing_path">
                    <ProcessGroup name="All"/>
                </ProcessChoice>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert not core_schema.validate(xml)

    def test_rejects_aggregator_in_clean_output(self, core_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <Aggregator name="Upstream">
                    <Process class="Drilling"/>
                </Aggregator>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert not core_schema.validate(xml)

    def test_validates_with_explicit_attr(self, core_schema):
        xml = _core_model(E_a("depth", "5000", explicit="true"))
        assert core_schema.validate(xml), core_schema.error_log

    # ── new tests ──

    def test_validates_model_with_schema_version(self, core_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(),
            schema_version="4.0",
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_model_with_multiple_fields(self, core_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(name="field1"),
            _valid_field(name="field2"),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_model_with_multiple_analyses(self, core_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), name="a1"),
            E_analysis(E_a("functional_unit", "gas"), name="a2"),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_model_with_top_level_a(self, core_schema):
        xml = E_model(
            E_a("some_setting", "value"),
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_empty_model(self, core_schema):
        # xs:choice maxOccurs="unbounded" with all minOccurs=0 allows empty
        xml = E_model()
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_valid_core_model_fixture(self, core_schema, valid_core_model):
        assert core_schema.validate(valid_core_model), core_schema.error_log


class TestCoreSchemaAnalysis:
    """Tests for <Analysis> in opgee_core.xsd."""

    def test_validates_with_field_ref(self, core_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), E_field_ref("test")),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_group(self, core_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), E_group("offshore")),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_group_regex(self, core_schema):
        xml = E_model(
            E_analysis(
                E_a("functional_unit", "oil"),
                E_group("field_.*", regex="1"),
            ),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_multiple_a(self, core_schema):
        xml = E_model(
            E_analysis(
                E_a("functional_unit", "oil"),
                E_a("GWP_horizon", "100"),
                E_a("GWP_version", "AR5"),
            ),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_delete_attr(self, core_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), delete="true"),
            _valid_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_empty_analysis(self, core_schema):
        # xs:choice allows zero matches when inner elements have minOccurs=0
        # variants; lxml accepts empty Analysis
        xml = E_model(E_analysis(), _valid_field())
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_invalid_child_element(self, core_schema):
        proc = E_process("Separation")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil"), proc),
            _valid_field(),
        )
        assert not core_schema.validate(xml)


class TestCoreSchemaField:
    """Tests for <Field> in opgee_core.xsd."""

    def test_validates_with_enabled(self, core_schema):
        xml = _core_model(field_kw={"enabled": "1"})
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_extend(self, core_schema):
        xml = _core_model(field_kw={"extend": "1"})
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_delete(self, core_schema):
        xml = _core_model(field_kw={"delete": "true"})
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_group_child(self, core_schema):
        xml = _core_model(E_group("onshore"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_empty_field(self, core_schema):
        # All Field children have minOccurs=0 inside xs:choice
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_field_without_name(self, core_schema):
        field = etree.Element("Field")
        field.append(E_process("Separation"))
        xml = E_model(E_analysis(E_a("functional_unit", "oil")), field)
        assert not core_schema.validate(xml)

    def test_rejects_modifies_attr_in_core(self, core_schema):
        # Core schema does not define modifies/modified attrs
        xml = _core_model(field_kw={"modifies": "base"})
        assert not core_schema.validate(xml)

    def test_rejects_modified_attr_in_core(self, core_schema):
        xml = _core_model(field_kw={"modified": "overlay"})
        assert not core_schema.validate(xml)


class TestCoreSchemaProcess:
    """Tests for <Process> in opgee_core.xsd."""

    def test_validates_minimal(self, core_schema):
        xml = _core_model()  # already has E_process("Separation")
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_name(self, core_schema):
        xml = _core_model(E_process("Drilling", name="drill1"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_enabled(self, core_schema):
        xml = _core_model(E_process("Drilling", enabled="0"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_boundary(self, core_schema):
        xml = _core_model(E_process("Drilling", boundary="Production"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_after(self, core_schema):
        xml = _core_model(E_process("Drilling", after="true"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_impute_start(self, core_schema):
        xml = _core_model(E_process("Drilling", impute_start="1"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_cycle_start(self, core_schema):
        xml = _core_model(E_process("Drilling", cycle_start="1"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_extend(self, core_schema):
        xml = _core_model(E_process("Drilling", extend="1"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_delete(self, core_schema):
        xml = _core_model(E_process("Drilling", delete="true"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_desc(self, core_schema):
        xml = _core_model(E_process("Drilling", desc="A description"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_all_attrs(self, core_schema):
        xml = _core_model(
            E_process(
                "Drilling", name="drill", enabled="1", boundary="Production",
                after="true", impute_start="0", cycle_start="0",
                extend="0", delete="false", desc="fully loaded",
            ),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_a_children(self, core_schema):
        xml = _core_model(
            E_process("Drilling", E_a("fracturing", "true"), E_a("depth", "5000")),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_missing_class(self, core_schema):
        proc = etree.Element("Process")  # no class attr
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), proc, E_stream("Reservoir", "Separation")),
        )
        assert not core_schema.validate(xml)

    def test_rejects_invalid_child(self, core_schema):
        # Stream is not a valid child of Process
        stream = E_stream("A", "B")
        proc = E_process("Separation")
        proc.append(stream)
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), proc, E_stream("Reservoir", "Separation")),
        )
        assert not core_schema.validate(xml)


class TestCoreSchemaStream:
    """Tests for <Stream> in opgee_core.xsd."""

    def test_validates_minimal(self, core_schema):
        xml = _core_model()  # already has minimal stream
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_name(self, core_schema):
        xml = _core_model(E_stream("A", "B", name="gas_flow"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_impute(self, core_schema):
        xml = _core_model(E_stream("A", "B", impute="0"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_boundary(self, core_schema):
        xml = _core_model(E_stream("A", "B", boundary="Production"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_delete(self, core_schema):
        xml = _core_model(E_stream("A", "B", delete="true"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_component(self, core_schema):
        xml = _core_model(
            E_stream("A", "B", E_component("CH4", "gas", "0.95")),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_multiple_components(self, core_schema):
        xml = _core_model(
            E_stream(
                "A", "B",
                E_component("CH4", "gas", "0.85"),
                E_component("C2H6", "gas", "0.10"),
                E_component("C3H8", "liquid", "0.05"),
            ),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_contains(self, core_schema):
        xml = _core_model(
            E_stream("A", "B", E_contains("oil")),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_a_child(self, core_schema):
        xml = _core_model(
            E_stream("A", "B", E_a("temperature", "100")),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_all_children(self, core_schema):
        xml = _core_model(
            E_stream(
                "A", "B",
                E_a("temperature", "100"),
                E_component("CH4", "gas", "0.90"),
                E_contains("gas"),
                name="full_stream", impute="1", boundary="Production",
            ),
        )
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_missing_src(self, core_schema):
        stream = etree.Element("Stream")
        stream.set("dst", "Separation")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), E_process("Separation"), stream),
        )
        assert not core_schema.validate(xml)

    def test_rejects_missing_dst(self, core_schema):
        stream = etree.Element("Stream")
        stream.set("src", "Reservoir")
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(E_a("country", "US"), E_process("Separation"), stream),
        )
        assert not core_schema.validate(xml)


class TestCoreSchemaComponent:
    """Tests for <Component> in opgee_core.xsd."""

    def test_validates_gas_phase(self, core_schema):
        xml = _core_model(E_stream("A", "B", E_component("CH4", "gas", "0.95")))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_liquid_phase(self, core_schema):
        xml = _core_model(E_stream("A", "B", E_component("C5", "liquid", "0.10")))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_solid_phase(self, core_schema):
        xml = _core_model(E_stream("A", "B", E_component("ite", "solid", "0.01")))
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_invalid_phase(self, core_schema):
        xml = _core_model(E_stream("A", "B", E_component("CH4", "plasma", "0.5")))
        assert not core_schema.validate(xml)

    def test_rejects_missing_name(self, core_schema):
        comp = etree.Element("Component")
        comp.set("phase", "gas")
        comp.text = "0.5"
        s = E_stream("A", "B")
        s.append(comp)
        xml = _core_model(s)
        assert not core_schema.validate(xml)

    def test_rejects_missing_phase(self, core_schema):
        comp = etree.Element("Component")
        comp.set("name", "CH4")
        comp.text = "0.5"
        s = E_stream("A", "B")
        s.append(comp)
        xml = _core_model(s)
        assert not core_schema.validate(xml)

    def test_rejects_non_decimal_value(self, core_schema):
        xml = _core_model(E_stream("A", "B", E_component("CH4", "gas", "not_a_number")))
        assert not core_schema.validate(xml)


class TestCoreSchemaA:
    """Tests for <A> in opgee_core.xsd."""

    def test_validates_minimal(self, core_schema):
        xml = _core_model(E_a("depth", "5000"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_explicit_true(self, core_schema):
        xml = _core_model(E_a("depth", "5000", explicit="true"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_explicit_false(self, core_schema):
        xml = _core_model(E_a("depth", "5000", explicit="false"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_validates_with_delete(self, core_schema):
        xml = _core_model(E_a("depth", "5000", delete="true"))
        assert core_schema.validate(xml), core_schema.error_log

    def test_rejects_missing_name(self, core_schema):
        a = etree.Element("A")
        a.text = "value"
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(a, E_process("Separation"), E_stream("Reservoir", "Separation")),
        )
        assert not core_schema.validate(xml)


# =====================================================================
# Ext schema (opgee_ext.xsd)
# =====================================================================

class TestExtSchema:
    """Tests for opgee_ext.xsd (pre-pipeline input with ProcessChoice etc.)"""

    # ── existing tests (preserved) ──

    def test_validates_raw_input_with_process_choice(self, ext_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <ProcessChoice name="gas_processing_path">
                    <ProcessGroup name="All">
                        <ProcessRef name="GasGathering"/>
                        <StreamRef name="gas to dehydration"/>
                    </ProcessGroup>
                    <ProcessGroup name="None"/>
                </ProcessChoice>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_aggregator(self, ext_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Aggregator name="Upstream">
                    <Process class="Drilling"/>
                </Aggregator>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_field_with_modifies(self, ext_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
            field_attrs='modifies="base_field"',
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_rejects_invalid_element(self, ext_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body='<InvalidElement/>',
        )
        assert not ext_schema.validate(xml)

    # ── new tests ──

    def test_validates_field_with_modified(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(modified="overlay_field"),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_field_with_modifies_and_modified(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            _valid_field(modifies="base", modified="overlay"),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_multiple_process_choices(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log


class TestExtSchemaProcessChoice:
    """Tests for <ProcessChoice> in opgee_ext.xsd."""

    def test_validates_minimal(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("gas_path", E_process_group("All")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_default(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "gas_path", E_process_group("All"),
                    default="All",
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_extend(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "gas_path", E_process_group("All"),
                    extend="1",
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_delete(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "gas_path", E_process_group("All"),
                    delete="true",
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_multiple_groups(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_rejects_missing_name(self, ext_schema):
        pc = etree.Element("ProcessChoice")
        pc.append(E_process_group("All"))
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"), pc,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert not ext_schema.validate(xml)

    def test_rejects_no_groups(self, ext_schema):
        # ProcessChoice requires minOccurs=1 ProcessGroup
        pc = E_process_choice("gas_path")  # no groups
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"), pc,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert not ext_schema.validate(xml)


class TestExtSchemaProcessGroup:
    """Tests for <ProcessGroup> in opgee_ext.xsd."""

    def test_validates_with_process_ref_only(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_stream_ref_only(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_nested_process_choice(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_mixed_children(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_empty_group(self, ext_schema):
        # xs:choice with all minOccurs=0 allows empty ProcessGroup
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("path", E_process_group("Empty")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_rejects_missing_name(self, ext_schema):
        pg = etree.Element("ProcessGroup")
        pg.append(E_process_ref("Drilling"))
        pc = E_process_choice("path")
        pc.append(pg)
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"), pc,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert not ext_schema.validate(xml)

    def test_rejects_direct_process_child(self, ext_schema):
        # ProcessGroup only allows ProcessRef/StreamRef/ProcessChoice, not Process
        pg = E_process_group("Bad")
        pg.append(E_process("Drilling"))
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("path", pg),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert not ext_schema.validate(xml)


class TestExtSchemaProcessRef:
    """Tests for <ProcessRef> in opgee_ext.xsd."""

    def test_validates_with_name(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("p", E_process_group("G", E_process_ref("Drill"))),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_class(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_name_and_class(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group(
                        "G", E_process_ref("drill1", cls="Drilling"),
                    ),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_delete(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p",
                    E_process_group(
                        "G", E_process_ref("Drill", delete="true"),
                    ),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_no_attrs(self, ext_schema):
        # All ProcessRef attrs are optional per the XSD
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice("p", E_process_group("G", E_process_ref())),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log


class TestExtSchemaStreamRef:
    """Tests for <StreamRef> in opgee_ext.xsd."""

    def test_validates_minimal(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_process_choice(
                    "p", E_process_group("G", E_stream_ref("gas line")),
                ),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_delete(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_rejects_missing_name(self, ext_schema):
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
        assert not ext_schema.validate(xml)


class TestExtSchemaAggregator:
    """Tests for <Aggregator> in opgee_ext.xsd."""

    def test_validates_with_process(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_process_ref(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process_ref("Drilling")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_nested_aggregator(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_a_child(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_a("weight", "0.5")),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_process_choice(self, ext_schema):
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
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_enabled(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling"), enabled="0"),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_validates_with_delete(self, ext_schema):
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"),
                E_aggregator("Upstream", E_process("Drilling"), delete="true"),
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_rejects_stream_child(self, ext_schema):
        # Aggregator does not allow Stream children per XSD
        agg = E_aggregator("Upstream")
        agg.append(E_stream("A", "B"))
        xml = E_model(
            E_analysis(E_a("functional_unit", "oil")),
            E_field(
                E_a("country", "US"), agg,
                E_process("Separation"),
                E_stream("Reservoir", "Separation"),
            ),
        )
        assert not ext_schema.validate(xml)


class TestExtSchemaCrossValidation:
    """Cross-schema validation tests."""

    def test_core_valid_xml_passes_ext(self, core_schema, ext_schema):
        """Core-valid XML should also pass ext validation (ext is a superset)."""
        xml = _core_model()
        assert core_schema.validate(xml), core_schema.error_log
        assert ext_schema.validate(xml), ext_schema.error_log

    def test_process_ref_rejected_by_core(self, core_schema):
        """ProcessRef is an ext-only element; core should reject it."""
        # ProcessRef can only appear inside ProcessGroup, which is inside
        # ProcessChoice — and ProcessChoice itself is rejected by core.
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <ProcessChoice name="p">
                    <ProcessGroup name="G">
                        <ProcessRef name="Drill"/>
                    </ProcessGroup>
                </ProcessChoice>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert not core_schema.validate(xml)

    def test_stream_ref_rejected_by_core(self, core_schema):
        """StreamRef is an ext-only element; core should reject it."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <ProcessChoice name="p">
                    <ProcessGroup name="G">
                        <StreamRef name="gas line"/>
                    </ProcessGroup>
                </ProcessChoice>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert not core_schema.validate(xml)


# =====================================================================
# Attributes schema (attributes.xsd)
# =====================================================================

class TestAttrSchema:
    """Tests for attributes.xsd."""

    # ── existing tests ──

    def test_validates_attr_defs_structure(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options("oil_type", "conventional",
                          E_option("conventional"),
                          E_option("heavy", label="heavy")),
                E_attr_def("age", "25", type="int", unit="yr"),
                E_attr_def("country", "USA", type="str"),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_rejects_missing_class_name(self, attr_schema):
        ca = etree.Element("ClassAttrs")
        ca.append(E_attr_def("age", "25", type="int"))
        xml = E_attr_defs(ca)
        assert not attr_schema.validate(xml)

    def test_validates_real_attributes_xml(self, attr_schema, attr_defs_elt):
        assert attr_schema.validate(attr_defs_elt), attr_schema.error_log

    # ── new tests ──

    def test_validates_multiple_class_attrs(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("depth", "5000", type="float")),
            E_class_attrs("Analysis", E_attr_def("GWP", "100", type="int")),
            E_class_attrs("Model", E_attr_def("version", "4", type="str")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_empty_class_attrs(self, attr_schema):
        # xs:choice with minOccurs=0 items allows empty ClassAttrs
        xml = E_attr_defs(E_class_attrs("Field"))
        assert attr_schema.validate(xml), attr_schema.error_log


class TestAttrSchemaAttrDef:
    """Tests for <AttrDef> in attributes.xsd."""

    def test_validates_with_type(self, attr_schema):
        xml = E_attr_defs(E_class_attrs("Field", E_attr_def("age", "25", type="int")))
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_unit(self, attr_schema):
        xml = E_attr_defs(E_class_attrs("Field", E_attr_def("depth", "5000", unit="ft")))
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_desc(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("age", "25", desc="Age of field")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_options_ref(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options("oil_type", "conventional", E_option("conventional")),
                E_attr_def("oil_type", "conventional", options="oil_type"),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_exclusive(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("ratio", "0.5", exclusive="true")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_synchronized(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("pair", "A", synchronized="partner")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_GT(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("depth", "100", GT="0")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_GE(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("ratio", "0", GE="0")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_LT(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("fraction", "0.5", LT="1")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_LE(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("fraction", "1.0", LE="1")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_GT_and_LE_combo(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("fraction", "0.5", GT="0", LE="1")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_default_value_as_text(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("name", "default_value")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_with_all_attrs(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_attr_def(
                    "depth", "5000",
                    type="float", unit="ft", desc="Well depth",
                    options="depth_range", exclusive="true",
                    synchronized="partner", GT="0", LE="50000",
                ),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_no_default_value(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("optional_field")),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_rejects_missing_name(self, attr_schema):
        ad = etree.Element("AttrDef")
        ad.text = "25"
        ad.set("type", "int")
        ca = E_class_attrs("Field")
        ca.append(ad)
        xml = E_attr_defs(ca)
        assert not attr_schema.validate(xml)

    def test_rejects_non_decimal_GT(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs("Field", E_attr_def("depth", "100", GT="not_a_number")),
        )
        assert not attr_schema.validate(xml)


class TestAttrSchemaOptions:
    """Tests for <Options> and <Option> in attributes.xsd."""

    def test_validates_minimal(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options("oil_type", "conventional", E_option("conventional")),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_option_with_label(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type", "conventional",
                    E_option("conventional", label="Conventional Oil"),
                ),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_option_with_desc(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type", "conventional",
                    E_option("conventional", desc="Standard crude"),
                ),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_validates_multiple_options(self, attr_schema):
        xml = E_attr_defs(
            E_class_attrs(
                "Field",
                E_options(
                    "oil_type", "conventional",
                    E_option("conventional"),
                    E_option("heavy", label="Heavy"),
                    E_option("light", desc="Light crude"),
                ),
            ),
        )
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_rejects_options_missing_name(self, attr_schema):
        opts = etree.Element("Options")
        opts.set("default", "conventional")
        opts.append(E_option("conventional"))
        ca = E_class_attrs("Field")
        ca.append(opts)
        xml = E_attr_defs(ca)
        assert not attr_schema.validate(xml)

    def test_rejects_options_missing_default(self, attr_schema):
        opts = etree.Element("Options")
        opts.set("name", "oil_type")
        opts.append(E_option("conventional"))
        ca = E_class_attrs("Field")
        ca.append(opts)
        xml = E_attr_defs(ca)
        assert not attr_schema.validate(xml)

    def test_rejects_options_empty(self, attr_schema):
        # Options requires at least one Option child
        opts = etree.Element("Options")
        opts.set("name", "oil_type")
        opts.set("default", "conventional")
        ca = E_class_attrs("Field")
        ca.append(opts)
        xml = E_attr_defs(ca)
        assert not attr_schema.validate(xml)
