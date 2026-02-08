"""Tests for pydantic-xml models in opgee.input.models."""
from __future__ import annotations

import pytest
from lxml import etree

from opgee.input.models import (
    AnalysisModel,
    ContainsElement,
    FieldModel,
    GroupElement,
    ModelModel,
    StreamModel,
)
from opgee.input.models.processes import (
    AcidGasRemoval,
    Boundary,
    Drilling,
    Flaring,
    Separation,
    Venting,
)


# ---------------------------------------------------------------------------
# StreamModel
# ---------------------------------------------------------------------------
class TestContainsElement:
    def test_parse_contains_with_text(self):
        xml = etree.fromstring('<Contains>oil</Contains>')
        m = ContainsElement.from_xml_tree(xml)
        assert m.value == "oil"
        assert m.delete is None

    def test_parse_contains_empty(self):
        xml = etree.fromstring('<Contains/>')
        m = ContainsElement.from_xml_tree(xml)
        assert m.value is None
        assert m.delete is None

    def test_parse_contains_with_delete_attr(self):
        xml = etree.fromstring('<Contains delete="true">gas</Contains>')
        m = ContainsElement.from_xml_tree(xml)
        assert m.value == "gas"
        assert m.delete is True

    def test_parse_contains_delete_false(self):
        xml = etree.fromstring('<Contains delete="false"/>')
        m = ContainsElement.from_xml_tree(xml)
        assert m.delete is False


class TestStreamModel:
    def test_minimal_stream(self):
        xml = etree.fromstring('<Stream src="A" dst="B"/>')
        m = StreamModel.from_xml_tree(xml)
        assert m.src == "A"
        assert m.dst == "B"
        assert m.name is None
        assert m.impute is None
        assert m.boundary is None
        assert m.delete is None
        assert m.contains == []

    def test_stream_with_all_attrs(self):
        xml = etree.fromstring(
            '<Stream src="Reservoir" dst="Separation" '
            'name="crude" impute="true" boundary="Production" delete="false"/>'
        )
        m = StreamModel.from_xml_tree(xml)
        assert m.src == "Reservoir"
        assert m.dst == "Separation"
        assert m.name == "crude"
        assert m.impute is True
        assert m.boundary == "Production"
        assert m.delete is False

    def test_stream_with_contains_children(self):
        xml = etree.fromstring(
            '<Stream src="A" dst="B">'
            '  <Contains>oil</Contains>'
            '  <Contains>gas</Contains>'
            '</Stream>'
        )
        m = StreamModel.from_xml_tree(xml)
        assert len(m.contains) == 2
        assert m.contains[0].value == "oil"
        assert m.contains[1].value == "gas"

    def test_stream_with_contains_delete(self):
        xml = etree.fromstring(
            '<Stream src="A" dst="B">'
            '  <Contains delete="true">oil</Contains>'
            '</Stream>'
        )
        m = StreamModel.from_xml_tree(xml)
        assert len(m.contains) == 1
        assert m.contains[0].delete is True
        assert m.contains[0].value == "oil"

    def test_stream_missing_src_raises(self):
        xml = etree.fromstring('<Stream dst="B"/>')
        with pytest.raises(Exception):
            StreamModel.from_xml_tree(xml)

    def test_stream_missing_dst_raises(self):
        xml = etree.fromstring('<Stream src="A"/>')
        with pytest.raises(Exception):
            StreamModel.from_xml_tree(xml)


# ---------------------------------------------------------------------------
# Process models
# ---------------------------------------------------------------------------
class TestProcessBase:
    def test_empty_separation(self):
        xml = etree.fromstring('<Separation/>')
        m = Separation.from_xml_tree(xml)
        assert m.enabled is None
        assert m.boundary is None
        assert m.after is None
        assert m.impute_start is None
        assert m.cycle_start is None
        assert m.leak_rate == 0.0

    def test_separation_defaults(self):
        xml = etree.fromstring('<Separation/>')
        m = Separation.from_xml_tree(xml)
        assert m.number_stages == 2
        assert m.pressure_first_stage == 500.0
        assert m.pressure_second_stage == 250.0
        assert m.pressure_third_stage == 100.0
        assert m.prime_mover_type == "NG_engine"
        assert m.eta_compressor == 75.0

    def test_separation_with_custom_element(self):
        xml = etree.fromstring(
            '<Separation>'
            '  <number_stages>3</number_stages>'
            '  <pressure_first_stage>600</pressure_first_stage>'
            '</Separation>'
        )
        m = Separation.from_xml_tree(xml)
        assert m.number_stages == 3
        assert m.pressure_first_stage == 600.0
        # Non-specified fields keep defaults
        assert m.pressure_second_stage == 250.0

    def test_process_with_boundary_attr(self):
        xml = etree.fromstring('<Separation boundary="Production"/>')
        m = Separation.from_xml_tree(xml)
        assert m.boundary == "Production"

    def test_process_with_enabled_attr(self):
        xml = etree.fromstring('<Drilling enabled="false"/>')
        m = Drilling.from_xml_tree(xml)
        assert m.enabled is False

    def test_process_with_impute_start_attr(self):
        xml = etree.fromstring('<Flaring impute-start="true"/>')
        m = Flaring.from_xml_tree(xml)
        assert m.impute_start is True

    def test_process_with_cycle_start_attr(self):
        xml = etree.fromstring('<Venting cycle-start="true"/>')
        m = Venting.from_xml_tree(xml)
        assert m.cycle_start is True

    def test_process_with_leak_rate(self):
        xml = etree.fromstring(
            '<Boundary><leak_rate>0.05</leak_rate></Boundary>'
        )
        m = Boundary.from_xml_tree(xml)
        assert m.leak_rate == 0.05

    def test_empty_boundary(self):
        xml = etree.fromstring('<Boundary/>')
        m = Boundary.from_xml_tree(xml)
        assert isinstance(m, Boundary)
        assert m.leak_rate == 0.0

    def test_acid_gas_removal_defaults(self):
        xml = etree.fromstring('<AcidGasRemoval/>')
        m = AcidGasRemoval.from_xml_tree(xml)
        assert m.eta_reboiler == 1.25
        assert m.type_amine == "MDEA"
        assert m.prime_mover_type == "NG_engine"

    def test_acid_gas_removal_custom_values(self):
        # Elements must appear in class-definition order (ordered search mode)
        # eta_compressor is defined before type_amine in AcidGasRemoval
        xml = etree.fromstring(
            '<AcidGasRemoval>'
            '  <eta_compressor>80</eta_compressor>'
            '  <type_amine>MEA</type_amine>'
            '</AcidGasRemoval>'
        )
        m = AcidGasRemoval.from_xml_tree(xml)
        assert m.eta_compressor == 80.0
        assert m.type_amine == "MEA"


# ---------------------------------------------------------------------------
# ProcessUnion discrimination
# ---------------------------------------------------------------------------
class TestProcessUnionDiscrimination:
    """Verify that a parent element with mixed process tags deserializes
    each child to the correct Python type."""

    def test_field_with_mixed_processes(self):
        xml = etree.fromstring(
            '<Field name="mixed">'
            '  <Separation/>'
            '  <Drilling/>'
            '  <Flaring/>'
            '  <AcidGasRemoval/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert len(m.processes) == 4
        type_names = {type(p).__name__ for p in m.processes}
        assert type_names == {"Separation", "Drilling", "Flaring", "AcidGasRemoval"}

    def test_process_union_preserves_attrs(self):
        xml = etree.fromstring(
            '<Field name="attrs">'
            '  <Separation boundary="Production">'
            '    <number_stages>4</number_stages>'
            '  </Separation>'
            '  <Drilling enabled="false"/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        by_type = {type(p).__name__: p for p in m.processes}

        sep = by_type["Separation"]
        assert isinstance(sep, Separation)
        assert sep.boundary == "Production"
        assert sep.number_stages == 4

        drill = by_type["Drilling"]
        assert isinstance(drill, Drilling)
        assert drill.enabled is False


# ---------------------------------------------------------------------------
# FieldModel
# ---------------------------------------------------------------------------
class TestFieldModel:
    def test_minimal_field(self):
        xml = etree.fromstring('<Field name="test"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        assert m.name == "test"
        assert len(m.processes) == 1
        assert isinstance(m.processes[0], Separation)

    def test_field_name_required(self):
        xml = etree.fromstring('<Field><Separation/></Field>')
        with pytest.raises(Exception):
            FieldModel.from_xml_tree(xml)

    def test_field_defaults(self):
        """Non-smart-default fields get their default values when absent."""
        xml = etree.fromstring('<Field name="defaults"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        assert m.downhole_pump == 1
        assert m.API == 32.8
        assert m.age == 38.0
        assert m.country == "Generic"
        assert m.offshore == 0
        assert m.oil_prod == 2098.0

    def test_smart_default_fields_are_none_when_absent(self):
        """Fields marked as smart defaults should be None when not in XML."""
        xml = etree.fromstring('<Field name="smart"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        assert m.GOR is None
        assert m.WOR is None
        assert m.WIR is None
        assert m.depth is None
        assert m.res_press is None
        assert m.res_temp is None
        assert m.num_prod_wells is None
        assert m.GFIR is None
        assert m.SOR is None
        assert m.fraction_elec_onsite is None
        assert m.fraction_remaining_gas_inj is None
        assert m.stabilizer_column is None

    def test_explicit_values_set(self):
        """Values explicitly set in XML should appear in the model."""
        xml = etree.fromstring(
            '<Field name="explicit">'
            '  <GOR>500</GOR>'
            '  <depth>8000</depth>'
            '  <API>28.5</API>'
            '  <Separation/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert m.GOR == 500.0
        assert m.depth == 8000.0
        assert m.API == 28.5

    def test_model_fields_set_tracks_explicit(self):
        """model_fields_set should include fields from XML, not defaulted ones."""
        xml = etree.fromstring(
            '<Field name="tracking">'
            '  <GOR>300</GOR>'
            '  <offshore>1</offshore>'
            '  <Separation/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert "name" in m.model_fields_set
        assert "GOR" in m.model_fields_set
        assert "offshore" in m.model_fields_set
        # Smart default fields not in XML should NOT be in model_fields_set
        assert "depth" not in m.model_fields_set
        assert "WOR" not in m.model_fields_set

    def test_field_with_streams(self):
        xml = etree.fromstring(
            '<Field name="streamed">'
            '  <Separation/>'
            '  <Stream src="Reservoir" dst="Separation"/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert len(m.streams) == 1
        assert m.streams[0].src == "Reservoir"
        assert m.streams[0].dst == "Separation"

    def test_field_with_multiple_streams(self):
        xml = etree.fromstring(
            '<Field name="multi-stream">'
            '  <Separation/>'
            '  <Drilling/>'
            '  <Stream src="Reservoir" dst="Separation"/>'
            '  <Stream src="Separation" dst="Drilling" name="gas-out"/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert len(m.streams) == 2
        assert len(m.processes) == 2

    def test_field_unordered_elements(self):
        """Elements can appear in any order due to search_mode=UNORDERED."""
        xml = etree.fromstring(
            '<Field name="unordered">'
            '  <Stream src="A" dst="B"/>'
            '  <API>30.0</API>'
            '  <Separation/>'
            '  <GOR>200</GOR>'
            '  <Drilling/>'
            '  <Stream src="C" dst="D"/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert m.API == 30.0
        assert m.GOR == 200.0
        assert len(m.processes) == 2
        assert len(m.streams) == 2

    def test_field_enabled_attr(self):
        xml = etree.fromstring(
            '<Field name="disabled" enabled="false"><Separation/></Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert m.enabled is False

    def test_field_enabled_default_none(self):
        xml = etree.fromstring('<Field name="default"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        assert m.enabled is None

    def test_field_group_attr(self):
        xml = etree.fromstring('<Field name="grouped" group="oil"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        assert m.group == "oil"

    def test_field_group_default_none(self):
        xml = etree.fromstring('<Field name="ungrouped"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        assert m.group is None

    def test_field_literal_values(self):
        """Literal-typed fields accept valid enum values."""
        xml = etree.fromstring(
            '<Field name="literals">'
            '  <oil_sands_mine>Integrated with upgrader</oil_sands_mine>'
            '  <gas_processing_path>Acid Gas</gas_processing_path>'
            '  <upgrader_type>Delayed coking</upgrader_type>'
            '  <ecosystem_richness>High carbon</ecosystem_richness>'
            '  <Separation/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert m.oil_sands_mine == "Integrated with upgrader"
        assert m.gas_processing_path == "Acid Gas"
        assert m.upgrader_type == "Delayed coking"
        assert m.ecosystem_richness == "High carbon"

    def test_field_gas_composition(self):
        xml = etree.fromstring(
            '<Field name="gas">'
            '  <gas_comp_C1>85.0</gas_comp_C1>'
            '  <gas_comp_CO2>1.5</gas_comp_CO2>'
            '  <gas_comp_H2S>0.5</gas_comp_H2S>'
            '  <Separation/>'
            '</Field>'
        )
        m = FieldModel.from_xml_tree(xml)
        assert m.gas_comp_C1 == 85.0
        assert m.gas_comp_CO2 == 1.5
        assert m.gas_comp_H2S == 0.5
        # Defaults for unspecified components
        assert m.gas_comp_N2 == 2.86
        assert m.gas_comp_C2 == 5.3

    def test_frozen_is_false(self):
        """OPGEEBaseModel has frozen=False, so field assignment is allowed."""
        xml = etree.fromstring('<Field name="mutable"><Separation/></Field>')
        m = FieldModel.from_xml_tree(xml)
        m.API = 25.0
        assert m.API == 25.0


# ---------------------------------------------------------------------------
# AnalysisModel
# ---------------------------------------------------------------------------
class TestAnalysisModel:
    def test_minimal_analysis(self):
        xml = etree.fromstring('<Analysis name="test"/>')
        m = AnalysisModel.from_xml_tree(xml)
        assert m.name == "test"
        assert m.GWP_horizon is None
        assert m.GWP_version is None
        assert m.functional_unit is None
        assert m.boundary is None
        assert m.groups == []

    def test_analysis_with_all_elements(self):
        xml = etree.fromstring(
            '<Analysis name="full">'
            '  <GWP_horizon>100</GWP_horizon>'
            '  <GWP_version>AR5</GWP_version>'
            '  <functional_unit>oil</functional_unit>'
            '  <boundary>Production</boundary>'
            '</Analysis>'
        )
        m = AnalysisModel.from_xml_tree(xml)
        assert m.GWP_horizon == "100"
        assert m.GWP_version == "AR5"
        assert m.functional_unit == "oil"
        assert m.boundary == "Production"

    def test_analysis_with_groups(self):
        xml = etree.fromstring(
            '<Analysis name="grps">'
            '  <Group>oil</Group>'
            '  <Group>gas</Group>'
            '</Analysis>'
        )
        m = AnalysisModel.from_xml_tree(xml)
        assert len(m.groups) == 2
        assert m.groups[0].text == "oil"
        assert m.groups[1].text == "gas"

    def test_analysis_name_required(self):
        xml = etree.fromstring('<Analysis/>')
        with pytest.raises(Exception):
            AnalysisModel.from_xml_tree(xml)

    def test_analysis_unordered(self):
        """Analysis uses search_mode=unordered, so element order is flexible."""
        xml = etree.fromstring(
            '<Analysis name="unord">'
            '  <Group>oil</Group>'
            '  <GWP_version>AR6</GWP_version>'
            '  <Group>gas</Group>'
            '  <GWP_horizon>20</GWP_horizon>'
            '</Analysis>'
        )
        m = AnalysisModel.from_xml_tree(xml)
        assert m.GWP_horizon == "20"
        assert m.GWP_version == "AR6"
        assert len(m.groups) == 2


class TestGroupElement:
    def test_parse_group_with_text(self):
        xml = etree.fromstring('<Group>oil</Group>')
        m = GroupElement.from_xml_tree(xml)
        assert m.text == "oil"
        assert m.regex is False

    def test_parse_group_regex_true(self):
        xml = etree.fromstring('<Group regex="true">oil.*</Group>')
        m = GroupElement.from_xml_tree(xml)
        assert m.text == "oil.*"
        assert m.regex is True

    def test_parse_group_regex_default_false(self):
        xml = etree.fromstring('<Group>gas</Group>')
        m = GroupElement.from_xml_tree(xml)
        assert m.regex is False

    def test_parse_group_empty(self):
        xml = etree.fromstring('<Group/>')
        m = GroupElement.from_xml_tree(xml)
        assert m.text is None
        assert m.regex is False


# ---------------------------------------------------------------------------
# ModelModel
# ---------------------------------------------------------------------------
class TestModelModel:
    def test_empty_model(self):
        xml = etree.fromstring('<Model/>')
        m = ModelModel.from_xml_tree(xml)
        assert m.schema_version is None
        assert m.analyses == []
        assert m.fields == []

    def test_model_with_schema_version(self):
        xml = etree.fromstring('<Model schema_version="4.0"/>')
        m = ModelModel.from_xml_tree(xml)
        assert m.schema_version == "4.0"

    def test_model_with_analysis_and_field(self):
        xml = etree.fromstring(
            '<Model>'
            '  <Analysis name="a1">'
            '    <Group>oil</Group>'
            '  </Analysis>'
            '  <Field name="f1" group="oil">'
            '    <Separation/>'
            '  </Field>'
            '</Model>'
        )
        m = ModelModel.from_xml_tree(xml)
        assert len(m.analyses) == 1
        assert len(m.fields) == 1
        assert m.analyses[0].name == "a1"
        assert m.fields[0].name == "f1"

    def test_model_field_property(self):
        xml = etree.fromstring(
            '<Model><Field name="f1"><Separation/></Field></Model>'
        )
        m = ModelModel.from_xml_tree(xml)
        assert m.field is not None
        assert m.field.name == "f1"

    def test_model_field_property_empty(self):
        xml = etree.fromstring('<Model/>')
        m = ModelModel.from_xml_tree(xml)
        assert m.field is None

    def test_model_analysis_property(self):
        xml = etree.fromstring(
            '<Model><Analysis name="a1"/></Model>'
        )
        m = ModelModel.from_xml_tree(xml)
        assert m.analysis is not None
        assert m.analysis.name == "a1"

    def test_model_analysis_property_empty(self):
        xml = etree.fromstring('<Model/>')
        m = ModelModel.from_xml_tree(xml)
        assert m.analysis is None

    def test_model_multiple_fields(self):
        xml = etree.fromstring(
            '<Model>'
            '  <Field name="f1"><Separation/></Field>'
            '  <Field name="f2"><Drilling/></Field>'
            '</Model>'
        )
        m = ModelModel.from_xml_tree(xml)
        assert len(m.fields) == 2
        assert m.fields[0].name == "f1"
        assert m.fields[1].name == "f2"

    def test_model_multiple_analyses(self):
        xml = etree.fromstring(
            '<Model>'
            '  <Analysis name="a1"/>'
            '  <Analysis name="a2"/>'
            '</Model>'
        )
        m = ModelModel.from_xml_tree(xml)
        assert len(m.analyses) == 2

    def test_model_unordered(self):
        """Fields and analyses can appear in any order."""
        xml = etree.fromstring(
            '<Model>'
            '  <Field name="f1"><Separation/></Field>'
            '  <Analysis name="a1"/>'
            '  <Field name="f2"><Drilling/></Field>'
            '</Model>'
        )
        m = ModelModel.from_xml_tree(xml)
        assert len(m.fields) == 2
        assert len(m.analyses) == 1

    def test_model_full_structure(self):
        """End-to-end: Model with analysis referencing a field via Group,
        field with processes and streams."""
        xml = etree.fromstring(
            '<Model schema_version="4.0">'
            '  <Analysis name="base-case">'
            '    <GWP_horizon>100</GWP_horizon>'
            '    <GWP_version>AR5</GWP_version>'
            '    <functional_unit>oil</functional_unit>'
            '    <Group>oil-fields</Group>'
            '  </Analysis>'
            '  <Field name="my-field" group="oil-fields">'
            '    <API>28.0</API>'
            '    <GOR>400</GOR>'
            '    <depth>10000</depth>'
            '    <Separation>'
            '      <number_stages>3</number_stages>'
            '    </Separation>'
            '    <Drilling/>'
            '    <Flaring/>'
            '    <Stream src="Reservoir" dst="Separation">'
            '      <Contains>oil</Contains>'
            '      <Contains>gas</Contains>'
            '    </Stream>'
            '    <Stream src="Separation" dst="Flaring"/>'
            '  </Field>'
            '</Model>'
        )
        m = ModelModel.from_xml_tree(xml)

        # Model level
        assert m.schema_version == "4.0"

        # Analysis
        assert m.analysis.name == "base-case"
        assert m.analysis.GWP_horizon == "100"
        assert m.analysis.GWP_version == "AR5"
        assert len(m.analysis.groups) == 1
        assert m.analysis.groups[0].text == "oil-fields"

        # Field
        field = m.field
        assert field.name == "my-field"
        assert field.group == "oil-fields"
        assert field.API == 28.0
        assert field.GOR == 400.0
        assert field.depth == 10000.0

        # Processes
        assert len(field.processes) == 3
        proc_by_type = {type(p).__name__: p for p in field.processes}
        sep = proc_by_type["Separation"]
        assert isinstance(sep, Separation)
        assert sep.number_stages == 3

        # Streams
        assert len(field.streams) == 2
        assert field.streams[0].src == "Reservoir"
        assert len(field.streams[0].contains) == 2
