"""Tests for Stage 2: Smart defaults."""

import pytest

from opgee.input.xml.static_defaults import apply_static_defaults
from opgee.input.xml.smart_defaults import apply_smart_defaults
from opgee.input.xml.value_resolution import read_attr_value
from tests.xml.conftest import make_model_xml


@pytest.fixture(autouse=True)
def _ensure_attr_defs(loaded_attr_defs):
    """Ensure AttrDefs is loaded for all tests in this module."""
    yield


class TestSmartDefaults:

    def test_explicit_not_overwritten(self):
        """Explicit attributes should not be modified by smart defaults."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <A name="SOR">99.0</A>
            """,
        )
        apply_static_defaults(xml)
        apply_smart_defaults(xml)

        field = xml.find("Field")
        sor_value = read_attr_value(field, "SOR", "Field")
        # Explicit SOR=99.0 should NOT be overwritten by SOR_default
        assert sor_value == 99.0

    def test_non_explicit_computed(self):
        """Non-explicit attributes should be computed from dependencies."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <A name="steam_flooding">1</A>
            """,
        )
        apply_static_defaults(xml)
        apply_smart_defaults(xml)

        field = xml.find("Field")
        sor_value = read_attr_value(field, "SOR", "Field")
        # When steam_flooding=1, SOR_default returns 3.0
        assert sor_value == 3.0

    def test_dependency_chain_resolves(self):
        """SOR -> WOR -> WIR chain should resolve in correct order."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <A name="steam_flooding">0</A>
            """,
        )
        apply_static_defaults(xml)
        apply_smart_defaults(xml)

        field = xml.find("Field")
        sor_value = read_attr_value(field, "SOR", "Field")
        wor_value = read_attr_value(field, "WOR", "Field")
        wir_value = read_attr_value(field, "WIR", "Field")

        # steam_flooding=0 → SOR=1.0
        assert sor_value == 1.0
        # WIR = WOR + 1
        assert wir_value == wor_value + 1

    def test_process_scoped_default(self):
        """CrudeOilDewatering.heater_treater should resolve on the correct Process."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <A name="API">15</A>
                <Process class="CrudeOilDewatering"/>
            """,
        )
        apply_static_defaults(xml)
        apply_smart_defaults(xml)

        # Find the Process element
        proc = xml.find(".//Process[@class='CrudeOilDewatering']")
        assert proc is not None

        # heater_treater should be True (API < 18 → True)
        ht_value = read_attr_value(proc, "heater_treater", "CrudeOilDewatering")
        assert ht_value == 1  # binary coercion

    def test_common_gas_process_choice_default(self):
        """common_gas_process_choice should be 'All' when oil_sands_mine is 'None'."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body='<A name="country">US</A>',
        )
        apply_static_defaults(xml)
        apply_smart_defaults(xml)

        field = xml.find("Field")
        value = read_attr_value(field, "common_gas_process_choice", "Field")
        # Default oil_sands_mine is "None" → common_gas_process_choice = "All"
        assert value == "All"

    def test_offshore_defaults(self):
        """Offshore=1 should trigger fraction_elec_onsite=1.0, etc."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <A name="offshore">1</A>
            """,
        )
        apply_static_defaults(xml)
        apply_smart_defaults(xml)

        field = xml.find("Field")
        frac = read_attr_value(field, "fraction_elec_onsite", "Field")
        assert frac == 1.0

        eco = read_attr_value(field, "ecosystem_richness", "Field")
        assert eco == "Low carbon"


class TestRunOrder:

    def test_dependencies_before_dependents(self):
        """In the run order, SOR should appear before WOR."""
        from opgee.input.xml.smart_defaults import run_order

        order = run_order()
        # SOR depends on steam_flooding; WOR depends on SOR
        if "SOR" in order and "WOR" in order:
            assert order.index("SOR") < order.index("WOR")
