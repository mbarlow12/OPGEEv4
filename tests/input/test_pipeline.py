"""Integration tests for the full XML pipeline entry point.

Tests exercise ``process_field_xml()`` from ``opgee/input/xml/__init__.py``,
which parses an XML file, resolves XIncludes, deserializes to pydantic models,
applies smart defaults, and validates.
"""
from __future__ import annotations

import importlib

import pytest
from lxml import etree
from lxml.builder import E

from opgee.input.models.field import FieldModel
from opgee.input.smart_defaults import clear_registry
from opgee.input.xml import process_field_xml

from .conftest import make_field_xml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model_xml(*fields: etree._Element) -> str:
    """Wrap one or more <Field> elements in a <Model> and return XML string."""
    model = E.Model(*fields)
    return etree.tostring(model, xml_declaration=True, encoding="UTF-8")


def _reload_defaults() -> None:
    """Re-register all smart default functions.

    ``clear_registry()`` empties the global registry, but the
    ``@register`` decorators in the defaults modules have already executed
    (Python caches imported modules).  Reloading the modules forces the
    decorators to run again and re-populate the registry.
    """
    from opgee.input.smart_defaults import field_defaults, process_defaults

    importlib.reload(field_defaults)
    importlib.reload(process_defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure the smart-defaults registry is reset between tests.

    Clears the registry after each test, then reloads the default-function
    modules so ``@register`` decorators re-execute for the next test.
    """
    yield
    clear_registry()
    _reload_defaults()


# ---------------------------------------------------------------------------
# 1. Minimal field — basic round-trip
# ---------------------------------------------------------------------------

class TestMinimalField:
    """Write a minimal XML file and verify a FieldModel is returned."""

    def test_returns_field_model_with_correct_name(self, tmp_xml_file):
        field = make_field_xml("my_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)

        assert len(results) == 1
        assert isinstance(results[0], FieldModel)
        assert results[0].name == "my_field"

    def test_returns_separation_process(self, tmp_xml_file):
        field = make_field_xml("proc_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)

        assert len(results[0].processes) >= 1
        proc_types = [type(p).__name__ for p in results[0].processes]
        assert "Separation" in proc_types


# ---------------------------------------------------------------------------
# 2. Smart defaults applied
# ---------------------------------------------------------------------------

class TestSmartDefaults:
    """Verify that smart-defaulted fields are populated after the pipeline."""

    def test_GOR_is_populated(self, tmp_xml_file):
        field = make_field_xml("defaults_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.GOR is not None
        # Default API is 32.8 (> 30), so GOR should be 2429.3
        assert fm.GOR == pytest.approx(2429.3)

    def test_depth_is_populated(self, tmp_xml_file):
        field = make_field_xml("depth_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.depth is not None
        assert isinstance(fm.depth, float)

    def test_WOR_is_populated(self, tmp_xml_file):
        field = make_field_xml("wor_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.WOR is not None
        assert isinstance(fm.WOR, float)

    def test_num_prod_wells_is_populated(self, tmp_xml_file):
        field = make_field_xml("wells_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.num_prod_wells is not None

    def test_res_press_is_populated(self, tmp_xml_file):
        field = make_field_xml("press_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.res_press is not None

    def test_res_temp_is_populated(self, tmp_xml_file):
        field = make_field_xml("temp_field", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.res_temp is not None


# ---------------------------------------------------------------------------
# 3. Explicit values preserved
# ---------------------------------------------------------------------------

class TestExplicitValuesPreserved:
    """Values explicitly set in XML must survive the pipeline unchanged."""

    def test_explicit_GOR_preserved(self, tmp_xml_file):
        field = make_field_xml("explicit_gor", oil_sands_mine="None", GOR="999.9")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.GOR == pytest.approx(999.9)

    def test_explicit_depth_preserved(self, tmp_xml_file):
        field = make_field_xml("explicit_depth", oil_sands_mine="None", depth="5000.0")
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.depth == pytest.approx(5000.0)

    def test_explicit_oil_sands_mine_preserved(self, tmp_xml_file):
        field = make_field_xml(
            "explicit_osm",
            oil_sands_mine="Integrated with upgrader",
        )
        path = tmp_xml_file(_model_xml(field))

        results = process_field_xml(path)
        fm = results[0]

        assert fm.oil_sands_mine == "Integrated with upgrader"


# ---------------------------------------------------------------------------
# 4. Multiple fields
# ---------------------------------------------------------------------------

class TestMultipleFields:
    """Pipeline should return one FieldModel per <Field> element."""

    def test_two_fields_returned(self, tmp_xml_file):
        field_a = make_field_xml("field_alpha", oil_sands_mine="None")
        field_b = make_field_xml("field_beta", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field_a, field_b))

        results = process_field_xml(path)

        assert len(results) == 2
        names = {fm.name for fm in results}
        assert names == {"field_alpha", "field_beta"}

    def test_each_field_has_defaults(self, tmp_xml_file):
        field_a = make_field_xml("fa", oil_sands_mine="None")
        field_b = make_field_xml("fb", oil_sands_mine="None")
        path = tmp_xml_file(_model_xml(field_a, field_b))

        results = process_field_xml(path)

        for fm in results:
            assert fm.GOR is not None
            assert fm.depth is not None


# ---------------------------------------------------------------------------
# 5. Pre-resolution validation — no fields
# ---------------------------------------------------------------------------

class TestPreResolutionValidation:
    """Model with no <Field> elements should raise ValueError."""

    def test_no_fields_raises(self, tmp_xml_file):
        model = E.Model()
        path = tmp_xml_file(
            etree.tostring(model, xml_declaration=True, encoding="UTF-8")
        )

        with pytest.raises(ValueError, match="Pre-resolution validation failed"):
            process_field_xml(path)

    def test_field_without_name_raises(self, tmp_xml_file):
        # <Field> with no name attribute
        field = etree.SubElement(E.Model(), "Field")
        etree.SubElement(field, "Separation")
        model = field.getparent()
        path = tmp_xml_file(
            etree.tostring(model, xml_declaration=True, encoding="UTF-8")
        )

        with pytest.raises(ValueError, match="Pre-resolution validation failed"):
            process_field_xml(path)


# ---------------------------------------------------------------------------
# 6. Post-resolution validation — no processes
# ---------------------------------------------------------------------------

class TestPostResolutionValidation:
    """Field with no processes should fail post-resolution validation."""

    def test_field_no_processes_raises(self, tmp_xml_file):
        # Build a Field with no process children — pass children=[] to skip
        # the default Separation that make_field_xml adds.
        field = etree.Element("Field", name="empty_procs")
        etree.SubElement(field, "oil_sands_mine").text = "None"
        model = E.Model(field)
        path = tmp_xml_file(
            etree.tostring(model, xml_declaration=True, encoding="UTF-8")
        )

        with pytest.raises(ValueError, match="Post-resolution validation failed"):
            process_field_xml(path)
