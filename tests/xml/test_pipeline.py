"""End-to-end integration tests for the XML processing pipeline."""

import pytest
from lxml import etree

from opgee.input.xml import process_field_xml
from opgee.input.xml.builders import BuiltModel
from opgee.attributes import AttrDefs
from tests.xml.conftest import (
    OPGEE_ETC,
    E_a,
    E_process,
    E_process_choice,
    E_process_group,
    E_process_ref,
    E_stream,
)
from tests.xml.fixture_data import model_with_field


@pytest.fixture(autouse=True)
def _cleanup_attr_defs():
    """Ensure AttrDefs is clean before/after each test."""
    AttrDefs.clear()
    yield
    AttrDefs.clear()


class TestPipelineEndToEnd:
    def _load_attr_defs_elt(self) -> etree.Element:
        """Load the real <AttrDefs> element from attributes.xml."""
        tree = etree.parse(str(OPGEE_ETC / "attributes.xml"))
        return tree.getroot().find("AttrDefs")

    def test_minimal_pipeline(self):
        """Pipeline produces a valid BuiltModel from minimal input."""
        xml = model_with_field(
            E_a("country", "US"),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        )
        attr_defs_elt = self._load_attr_defs_elt()

        model = process_field_xml(xml, attr_defs_elt)

        assert isinstance(model, BuiltModel)
        assert model.field.name == "test"
        assert "Separation" in model.field.process_names
        assert "country" in model.field.attr_dict

    def test_pipeline_with_process_choices(self):
        """Pipeline correctly resolves process choices."""
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
                E_process_group("None", E_process_ref("GasGathering")),
            ),
            E_process("GasGathering"),
            E_process("GasDehydration"),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        )
        attr_defs_elt = self._load_attr_defs_elt()

        model = process_field_xml(xml, attr_defs_elt)

        # Both should be present since "All" selected
        assert "GasGathering" in model.field.process_names
        assert "GasDehydration" in model.field.process_names

    def test_pipeline_smart_defaults_applied(self):
        """Pipeline should compute smart defaults."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("steam_flooding", "1"),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        )
        attr_defs_elt = self._load_attr_defs_elt()

        model = process_field_xml(xml, attr_defs_elt)

        # SOR should be computed (steam_flooding=1 → SOR=3.0)
        assert "SOR" in model.field.attr_dict
        sor = model.field.attr_dict["SOR"]
        # SOR has a unit, so check magnitude
        import pint

        if isinstance(sor, pint.Quantity):
            assert sor.magnitude == 3.0
        else:
            assert sor == 3.0

    def test_pipeline_field_attrs_populated(self):
        """After pipeline, field should have many attributes from defaults."""
        xml = model_with_field(
            E_a("country", "US"),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        )
        attr_defs_elt = self._load_attr_defs_elt()

        model = process_field_xml(xml, attr_defs_elt)

        # Should have many attributes from static defaults
        assert len(model.field.attr_dict) > 10

    def test_pipeline_no_process_choice_elements(self):
        """After pipeline, no ProcessChoice elements should remain."""
        xml = model_with_field(
            E_a("country", "US"),
            E_a("gas_path", "All"),
            E_process_choice(
                "gas_path",
                E_process_group("All", E_process_ref("GasGathering")),
            ),
            E_process("GasGathering"),
            E_process("Separation"),
            E_stream("Reservoir", "Separation"),
        )
        attr_defs_elt = self._load_attr_defs_elt()

        process_field_xml(xml, attr_defs_elt)

        # Verify the XML tree is clean
        field = xml.find("Field")
        assert field.findall("ProcessChoice") == []
        assert field.findall("Aggregator") == []
