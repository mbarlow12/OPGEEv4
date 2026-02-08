"""Tests for the smart defaults system at opgee/input/smart_defaults/."""
from __future__ import annotations

import importlib
from math import exp

import pytest
from lxml import etree

from opgee.input.models.field import FieldModel
from opgee.input.smart_defaults import (
    _registry,
    apply_defaults,
    clear_registry,
    register,
    run_order,
)
from opgee.input.smart_defaults.field_defaults import (
    GOR_default,
    WOR_default,
    depth_default,
    res_press_default,
    res_temp_default,
    SOR_default,
    WIR_default,
    stabilizer_default,
    GFIR_default,
    num_producing_wells_default,
    num_water_inj_wells_default,
    num_gas_inj_wells_default,
    fraction_elec_onsite_default,
    fraction_remaining_gas_inj_default,
    ecosystem_richness_default,
    field_development_intensity_default,
    common_gas_process_choice_default,
    prod_water_inlet_temp_default,
)
from opgee.input.smart_defaults.process_defaults import (
    heater_treater_default,
    fraction_diluent_default,
)

import opgee.input.smart_defaults.field_defaults as _field_defaults_mod
import opgee.input.smart_defaults.process_defaults as _process_defaults_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_field(xml_str: str) -> FieldModel:
    """Parse an XML string into a FieldModel via from_xml_tree."""
    return FieldModel.from_xml_tree(etree.fromstring(xml_str))


def _minimal_field(**extra_elements: str) -> FieldModel:
    """Build a minimal FieldModel with Separation process and optional extra elements.

    Extra keyword args become child elements, e.g. ``GOR="500"`` -> ``<GOR>500</GOR>``.
    Automatically adds ``<oil_sands_mine>None</oil_sands_mine>`` unless overridden.
    """
    if "oil_sands_mine" not in extra_elements:
        extra_elements = {"oil_sands_mine": "None", **extra_elements}
    children = "".join(f"<{tag}>{val}</{tag}>" for tag, val in extra_elements.items())
    xml = f'<Field name="test">{children}<Separation/></Field>'
    return _make_field(xml)


def _reload_defaults():
    """Reload the defaults modules to re-trigger @register decorators."""
    importlib.reload(_field_defaults_mod)
    importlib.reload(_process_defaults_mod)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_defaults():
    """Clear the global registry after each test to avoid cross-test contamination."""
    yield
    clear_registry()


@pytest.fixture()
def _empty_registry():
    """Ensure the registry is empty before the test (for registry unit tests)."""
    clear_registry()


@pytest.fixture()
def _loaded_defaults():
    """Ensure the real default functions are registered (for apply_defaults tests)."""
    clear_registry()
    _reload_defaults()


# ===========================================================================
# 1. Registry tests
# ===========================================================================


@pytest.mark.usefixtures("_empty_registry")
class TestRegistry:
    """Tests for register(), run_order(), and clear_registry()."""

    def test_register_adds_to_registry(self):
        @register("alpha", ["beta"])
        def alpha_fn(beta):
            return beta + 1

        assert "alpha" in _registry
        func, deps = _registry["alpha"]
        assert func is alpha_fn
        assert deps == ["beta"]

    def test_run_order_returns_topological_sort(self):
        """Topological sort: beta -> alpha -> gamma."""

        @register("alpha", ["beta"])
        def alpha_fn(beta):
            return beta

        @register("gamma", ["alpha"])
        def gamma_fn(alpha):
            return alpha

        order = run_order()
        assert order.index("beta") < order.index("alpha")
        assert order.index("alpha") < order.index("gamma")

    def test_run_order_is_cached(self):
        @register("x", ["y"])
        def x_fn(y):
            return y

        order1 = run_order()
        order2 = run_order()
        assert order1 is order2

    def test_clear_registry_empties_everything(self):
        @register("foo", [])
        def foo_fn():
            return 42

        assert len(_registry) > 0
        clear_registry()
        assert len(_registry) == 0

    def test_clear_registry_invalidates_run_order(self):
        @register("p", ["q"])
        def p_fn(q):
            return q

        run_order()  # populate cache
        clear_registry()

        # After clear, registering new entries and computing order should work
        @register("m", ["n"])
        def m_fn(n):
            return n

        order = run_order()
        assert "m" in order

    def test_cycle_detection(self):
        from opgee.error import OpgeeException

        @register("a", ["b"])
        def a_fn(b):
            return b

        @register("b", ["a"])
        def b_fn(a):
            return a

        with pytest.raises(OpgeeException, match="cycles"):
            run_order()


# ===========================================================================
# 2. apply_defaults on FieldModel
# ===========================================================================


@pytest.mark.usefixtures("_loaded_defaults")
class TestApplyDefaultsFieldModel:
    """Test that apply_defaults computes smart-defaulted fields correctly."""

    def test_gor_computed_from_api_default(self):
        """With default API=32.8 (> 30), GOR should be 2429.3."""
        field = _minimal_field()
        assert field.GOR is None  # not yet computed
        apply_defaults(field)
        assert field.GOR == 2429.3

    def test_depth_computed_from_gor(self):
        """GOR=2429.3 < 10000 -> depth=7122.0."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.depth == 7122.0

    def test_res_press_computed_from_depth(self):
        """res_press = 0.5 * depth * 0.43 for non-California, non-steam-flooding."""
        field = _minimal_field()
        apply_defaults(field)
        expected_depth = 7122.0
        expected = 0.5 * expected_depth * 0.43
        assert field.res_press == pytest.approx(expected)

    def test_res_temp_computed_from_depth(self):
        """res_temp = 70 + 1.8 * depth / 100."""
        field = _minimal_field()
        apply_defaults(field)
        expected = 70 + 1.8 * 7122.0 / 100.0
        assert field.res_temp == pytest.approx(expected)

    def test_dependency_chain_gor_depth_res_press_res_temp(self):
        """The full chain: API -> GOR -> depth -> res_press, res_temp."""
        field = _minimal_field()
        apply_defaults(field)

        # GOR from API=32.8
        assert field.GOR == 2429.3
        # depth from GOR
        assert field.depth == 7122.0
        # res_press from country=Generic, depth, steam_flooding=0
        assert field.res_press == pytest.approx(0.5 * 7122.0 * 0.43)
        # res_temp from depth
        assert field.res_temp == pytest.approx(70 + 1.8 * 7122.0 / 100.0)

    def test_sor_default_no_steam_flooding(self):
        """Without steam flooding, SOR=1.0."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.SOR == 1.0

    def test_sor_default_with_steam_flooding(self):
        """With steam flooding, SOR=3.0."""
        field = _minimal_field(steam_flooding="1")
        apply_defaults(field)
        assert field.SOR == 3.0

    def test_wor_default_no_steam_flooding(self):
        """WOR computed from age=38, steam_flooding=0."""
        field = _minimal_field()
        apply_defaults(field)
        expected = min(4.021 * exp(0.024 * 38.0) - 4.021, 100.0)
        assert field.WOR == pytest.approx(expected)

    def test_wir_default(self):
        """WIR = WOR + 1."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.WIR == pytest.approx(field.WOR + 1)

    def test_num_prod_wells_default(self):
        """num_prod_wells = max(1, round(oil_prod / 87.5)) for non-mine."""
        field = _minimal_field()
        apply_defaults(field)
        expected = max(1, round(2098.0 / 87.5))
        assert field.num_prod_wells == expected

    def test_num_water_inj_wells_default(self):
        """num_water_inj_wells depends on oil_prod and num_prod_wells."""
        field = _minimal_field()
        apply_defaults(field)
        # oil_prod=2098.0 > 1000 -> fraction=0.829
        from opgee.utils import roundup
        expected = int(roundup(field.num_prod_wells * 0.829, 0))
        assert field.num_water_inj_wells == expected

    def test_num_gas_inj_wells_default(self):
        """num_gas_inj_wells = int(num_prod_wells * 0.25)."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.num_gas_inj_wells == int(field.num_prod_wells * 0.25)

    def test_fraction_elec_onsite_default_not_offshore(self):
        """offshore=0 -> fraction_elec_onsite=0.0."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.fraction_elec_onsite == 0.0

    def test_fraction_elec_onsite_default_offshore(self):
        """offshore=1 -> fraction_elec_onsite=1.0."""
        field = _minimal_field(offshore="1")
        apply_defaults(field)
        assert field.fraction_elec_onsite == 1.0

    def test_ecosystem_richness_not_offshore(self):
        field = _minimal_field()
        apply_defaults(field)
        assert field.ecosystem_richness == "Med carbon"

    def test_ecosystem_richness_offshore(self):
        field = _minimal_field(offshore="1")
        apply_defaults(field)
        assert field.ecosystem_richness == "Low carbon"

    def test_field_development_intensity_not_offshore(self):
        field = _minimal_field()
        apply_defaults(field)
        assert field.field_development_intensity == "Med"

    def test_field_development_intensity_offshore(self):
        field = _minimal_field(offshore="1")
        apply_defaults(field)
        assert field.field_development_intensity == "Low"

    def test_common_gas_process_choice_no_mine(self):
        """oil_sands_mine='None' -> 'All'."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.common_gas_process_choice == "All"

    def test_common_gas_process_choice_with_mine(self):
        """oil_sands_mine='Integrated with upgrader' -> 'None'."""
        field = _minimal_field(oil_sands_mine="Integrated with upgrader")
        apply_defaults(field)
        assert field.common_gas_process_choice == "None"

    def test_prod_water_inlet_temp_generic(self):
        """country='Generic' (not Canada) -> 140.0."""
        field = _minimal_field()
        apply_defaults(field)
        assert field.prod_water_inlet_temp == 140.0

    def test_prod_water_inlet_temp_canada(self):
        """country='Canada' -> 340.0."""
        field = _minimal_field(country="Canada")
        apply_defaults(field)
        assert field.prod_water_inlet_temp == 340.0

    def test_stabilizer_column_default(self):
        """oil_sands_mine='None', gas_lifting=0, GOR > 500 -> 1."""
        field = _minimal_field()
        apply_defaults(field)
        # GOR=2429.3 > 500, gas_lifting=0, oil_sands_mine='None' -> 1
        assert field.stabilizer_column == 1

    def test_stabilizer_column_low_gor(self):
        """GOR <= 500, gas_lifting=0 -> 0."""
        field = _minimal_field(GOR="400")
        apply_defaults(field)
        assert field.stabilizer_column == 0

    def test_fraction_remaining_gas_inj_defaults(self):
        """natural_gas_reinjection=1, gas_flooding=0 -> 0.5."""
        field = _minimal_field()
        apply_defaults(field)
        # Defaults: natural_gas_reinjection=1, gas_flooding=0
        assert field.fraction_remaining_gas_inj == 0.5


# ===========================================================================
# 3. Explicit skip — apply_defaults should not overwrite explicit values
# ===========================================================================


@pytest.mark.usefixtures("_loaded_defaults")
class TestExplicitSkip:
    """Attributes explicitly set in XML should not be overwritten."""

    def test_explicit_gor_not_overwritten(self):
        """GOR explicitly set to 500.0 should remain 500.0."""
        field = _minimal_field(GOR="500.0")
        assert field.GOR == 500.0
        assert "GOR" in field.model_fields_set

        apply_defaults(field)
        assert field.GOR == 500.0  # unchanged

    def test_explicit_gor_dependents_still_computed(self):
        """Even with explicit GOR=500, depth etc. are still computed from it."""
        field = _minimal_field(GOR="500.0")
        apply_defaults(field)

        # depth computed from explicit GOR=500 (< 10000)
        assert field.depth == 7122.0
        assert field.res_temp == pytest.approx(70 + 1.8 * 7122.0 / 100.0)

    def test_explicit_depth_not_overwritten(self):
        """Explicitly set depth stays, even if GOR is computed."""
        field = _minimal_field(depth="5000.0")
        apply_defaults(field)
        assert field.depth == 5000.0

    def test_explicit_depth_affects_dependents(self):
        """Explicit depth=5000 -> res_temp uses 5000."""
        field = _minimal_field(depth="5000.0")
        apply_defaults(field)
        assert field.res_temp == pytest.approx(70 + 1.8 * 5000.0 / 100.0)

    def test_explicit_res_press_not_overwritten(self):
        field = _minimal_field(res_press="1234.0")
        apply_defaults(field)
        assert field.res_press == 1234.0

    def test_explicit_sor_not_overwritten(self):
        field = _minimal_field(SOR="5.0")
        apply_defaults(field)
        assert field.SOR == 5.0

    def test_multiple_explicit_values(self):
        """Multiple explicit values all preserved."""
        field = _minimal_field(GOR="800.0", depth="3000.0", res_temp="200.0")
        apply_defaults(field)
        assert field.GOR == 800.0
        assert field.depth == 3000.0
        assert field.res_temp == 200.0


# ===========================================================================
# 4. Process-scoped defaults
# ===========================================================================


@pytest.mark.usefixtures("_loaded_defaults")
class TestProcessScopedDefaults:
    """Test apply_defaults on process-level attributes."""

    def test_heater_treater_api_below_18(self):
        """API < 18 -> CrudeOilDewatering.heater_treater = 1."""
        xml = (
            '<Field name="test">'
            "<oil_sands_mine>None</oil_sands_mine>"
            "<API>15.0</API>"
            "<CrudeOilDewatering/>"
            "<Separation/>"
            "</Field>"
        )
        field = _make_field(xml)
        apply_defaults(field)

        proc = next(p for p in field.processes if type(p).__name__ == "CrudeOilDewatering")
        assert proc.heater_treater == 1

    def test_heater_treater_api_above_18(self):
        """API >= 18 -> CrudeOilDewatering.heater_treater = 0."""
        xml = (
            '<Field name="test">'
            "<oil_sands_mine>None</oil_sands_mine>"
            "<API>32.8</API>"
            "<CrudeOilDewatering/>"
            "<Separation/>"
            "</Field>"
        )
        field = _make_field(xml)
        apply_defaults(field)

        proc = next(p for p in field.processes if type(p).__name__ == "CrudeOilDewatering")
        assert proc.heater_treater == 0

    def test_heater_treater_explicit_not_overwritten(self):
        """Explicit <heater_treater>1</heater_treater> should not be overwritten."""
        xml = (
            '<Field name="test">'
            "<oil_sands_mine>None</oil_sands_mine>"
            "<API>32.8</API>"
            "<CrudeOilDewatering>"
            "  <heater_treater>1</heater_treater>"
            "</CrudeOilDewatering>"
            "<Separation/>"
            "</Field>"
        )
        field = _make_field(xml)
        apply_defaults(field)

        proc = next(p for p in field.processes if type(p).__name__ == "CrudeOilDewatering")
        assert proc.heater_treater == 1

    def test_fraction_diluent_integrated_no_upgrader(self):
        """oil_sands_mine='Integrated with diluent', upgrader_type='None' -> 0.3."""
        xml = (
            '<Field name="test">'
            "<oil_sands_mine>Integrated with diluent</oil_sands_mine>"
            "<upgrader_type>None</upgrader_type>"
            "<HeavyOilDilution/>"
            "<Separation/>"
            "</Field>"
        )
        field = _make_field(xml)
        apply_defaults(field)

        proc = next(p for p in field.processes if type(p).__name__ == "HeavyOilDilution")
        assert proc.fraction_diluent == 0.3

    def test_fraction_diluent_no_mine(self):
        """oil_sands_mine='None' -> fraction_diluent=0.0."""
        xml = (
            '<Field name="test">'
            "<oil_sands_mine>None</oil_sands_mine>"
            "<upgrader_type>None</upgrader_type>"
            "<HeavyOilDilution/>"
            "<Separation/>"
            "</Field>"
        )
        field = _make_field(xml)
        apply_defaults(field)

        proc = next(p for p in field.processes if type(p).__name__ == "HeavyOilDilution")
        assert proc.fraction_diluent == 0.0

    def test_process_not_present_skipped(self):
        """If CrudeOilDewatering not in processes, its default is silently skipped."""
        field = _minimal_field()  # only has Separation
        apply_defaults(field)
        # Should not raise; just verify field-level defaults are computed
        assert field.GOR is not None


# ===========================================================================
# 5. Individual default functions (unit tests)
# ===========================================================================


class TestGORDefault:
    def test_api_below_20(self):
        assert GOR_default(10.0) == 1122.4

    def test_api_exactly_20(self):
        assert GOR_default(20.0) == 1205.4

    def test_api_between_20_and_30(self):
        assert GOR_default(25.0) == 1205.4

    def test_api_exactly_30(self):
        assert GOR_default(30.0) == 1205.4

    def test_api_above_30(self):
        assert GOR_default(32.8) == 2429.3


class TestWORDefault:
    def test_with_steam_flooding(self):
        """When steam_flooding=1, WOR = SOR."""
        assert WOR_default(1, 38.0, 3.0) == 3.0

    def test_without_steam_flooding(self):
        expected = min(4.021 * exp(0.024 * 38.0) - 4.021, 100.0)
        assert WOR_default(0, 38.0, 1.0) == pytest.approx(expected)

    def test_without_steam_flooding_capped_at_100(self):
        """Very old fields should have WOR capped at 100."""
        assert WOR_default(0, 500.0, 1.0) == 100.0


class TestDepthDefault:
    def test_gor_above_10000(self):
        assert depth_default(15000.0) == 8285.0

    def test_gor_below_10000(self):
        assert depth_default(5000.0) == 7122.0

    def test_gor_exactly_10000(self):
        assert depth_default(10000.0) == 7122.0


class TestResPressDefault:
    def test_california_steam_flooding(self):
        assert res_press_default("California", 7122.0, 1) == 100.0

    def test_generic_no_steam_flooding(self):
        expected = 0.5 * 7122.0 * 0.43
        assert res_press_default("Generic", 7122.0, 0) == pytest.approx(expected)

    def test_california_no_steam_flooding(self):
        """California without steam flooding uses normal formula."""
        expected = 0.5 * 7122.0 * 0.43
        assert res_press_default("California", 7122.0, 0) == pytest.approx(expected)


class TestResTempDefault:
    def test_standard_depth(self):
        assert res_temp_default(7122.0) == pytest.approx(70 + 1.8 * 7122.0 / 100.0)

    def test_zero_depth(self):
        assert res_temp_default(0.0) == pytest.approx(70.0)


class TestSORDefault:
    def test_steam_flooding(self):
        assert SOR_default(1) == 3.0

    def test_no_steam_flooding(self):
        assert SOR_default(0) == 1.0


class TestWIRDefault:
    def test_wir_is_wor_plus_one(self):
        assert WIR_default(5.0) == 6.0


class TestStabilizerDefault:
    def test_oil_sands_mine(self):
        """oil_sands_mine != 'None' -> 0."""
        assert stabilizer_default(2429.3, 0, "Integrated with upgrader") == 0

    def test_low_gor_no_gas_lifting(self):
        """GOR <= 500 and gas_lifting=0 -> 0."""
        assert stabilizer_default(400.0, 0, "None") == 0

    def test_high_gor_no_gas_lifting(self):
        """GOR > 500 and gas_lifting=0 -> 1."""
        assert stabilizer_default(600.0, 0, "None") == 1

    def test_gas_lifting_enabled(self):
        """gas_lifting=1 -> 1 (even with low GOR)."""
        assert stabilizer_default(400.0, 1, "None") == 1


class TestGFIRDefault:
    def test_ng_flood(self):
        assert GFIR_default("NG", 2000.0) == 3000.0

    def test_n2_flood(self):
        assert GFIR_default("N2", 2000.0) == 1200.0

    def test_co2_flood(self):
        assert GFIR_default("CO2", 2000.0) == 10000.0

    def test_other_flood(self):
        assert GFIR_default("other", 2000.0) == 3000.0


class TestNumProducingWellsDefault:
    def test_oil_sands_mine(self):
        assert num_producing_wells_default("Integrated with upgrader", 2098.0) == 1

    def test_no_mine(self):
        assert num_producing_wells_default("None", 2098.0) == max(1, round(2098.0 / 87.5))

    def test_no_mine_small_production(self):
        assert num_producing_wells_default("None", 50.0) == max(1, round(50.0 / 87.5))


class TestNumWaterInjWellsDefault:
    def test_oil_sands_mine(self):
        assert num_water_inj_wells_default("Integrated with upgrader", 2098.0, 24) == 0

    def test_large_production(self):
        from opgee.utils import roundup
        n_prod = 24
        expected = int(roundup(n_prod * 0.829, 0))
        assert num_water_inj_wells_default("None", 2098.0, n_prod) == expected

    def test_small_production(self):
        from opgee.utils import roundup
        n_prod = 1
        expected = int(roundup(n_prod * 0.143, 0))
        assert num_water_inj_wells_default("None", 5.0, n_prod) == expected


class TestNumGasInjWellsDefault:
    def test_basic(self):
        assert num_gas_inj_wells_default(24) == 6

    def test_small(self):
        assert num_gas_inj_wells_default(3) == 0


class TestFractionElecOnsiteDefault:
    def test_offshore(self):
        assert fraction_elec_onsite_default(1) == 1.0

    def test_onshore(self):
        assert fraction_elec_onsite_default(0) == 0.0


class TestFractionRemainingGasInjDefault:
    def test_gas_flooding(self):
        assert fraction_remaining_gas_inj_default(0, 1) == 1.0

    def test_natural_gas_reinjection(self):
        assert fraction_remaining_gas_inj_default(1, 0) == 0.5

    def test_neither(self):
        assert fraction_remaining_gas_inj_default(0, 0) == 0.0


class TestEcosystemRichnessDefault:
    def test_offshore(self):
        assert ecosystem_richness_default(1) == "Low carbon"

    def test_onshore(self):
        assert ecosystem_richness_default(0) == "Med carbon"


class TestFieldDevelopmentIntensityDefault:
    def test_offshore(self):
        assert field_development_intensity_default(1) == "Low"

    def test_onshore(self):
        assert field_development_intensity_default(0) == "Med"


class TestCommonGasProcessChoiceDefault:
    def test_mine(self):
        assert common_gas_process_choice_default("Integrated with upgrader") == "None"

    def test_no_mine(self):
        assert common_gas_process_choice_default("None") == "All"


class TestProdWaterInletTempDefault:
    def test_canada(self):
        assert prod_water_inlet_temp_default("Canada") == 340.0

    def test_other(self):
        assert prod_water_inlet_temp_default("Generic") == 140.0


class TestHeaterTreaterDefault:
    def test_api_below_18(self):
        assert heater_treater_default(15.0) == 1

    def test_api_exactly_18(self):
        assert heater_treater_default(18.0) == 0

    def test_api_above_18(self):
        assert heater_treater_default(32.8) == 0


class TestFractionDiluentDefault:
    def test_integrated_diluent_no_upgrader(self):
        assert fraction_diluent_default("Integrated with diluent", "None") == 0.3

    def test_no_mine(self):
        assert fraction_diluent_default("None", "None") == 0.0

    def test_mine_with_upgrader(self):
        assert fraction_diluent_default("Integrated with diluent", "Delayed coking") == 0.0
