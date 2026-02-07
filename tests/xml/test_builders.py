"""Tests for Stage 4: Model object builders."""

from opgee.input.xml.builders import (
    build_model,
    BuiltModel,
    BuiltField,
    BuiltProcess,
    BuiltAnalysis,
)
from tests.xml.fixture_data import builder_model
from tests.xml.conftest import E_process, E_stream


class TestBuildModel:
    def test_builds_from_minimal_xml(self):
        """Should build a model from minimal XML."""
        xml = builder_model()

        model = build_model(xml)

        assert isinstance(model, BuiltModel)
        assert isinstance(model.field, BuiltField)
        assert isinstance(model.analysis, BuiltAnalysis)

    def test_field_attributes(self):
        """Field attr_dict should contain typed values."""
        xml = builder_model()

        model = build_model(xml)
        assert model.field.name == "test"
        assert "country" in model.field.attr_dict

    def test_process_names_collected(self):
        """Process names should be collected in BuiltField."""
        xml = builder_model(E_process("Drilling"))

        model = build_model(xml)
        assert "Separation" in model.field.process_names
        assert "Drilling" in model.field.process_names

    def test_stream_names_collected(self):
        """Stream names should be collected in BuiltField."""
        xml = builder_model(E_stream("Separation", "Flaring", name="gas for flaring"))

        model = build_model(xml)
        assert "Reservoir => Separation" in model.field.stream_names
        assert "gas for flaring" in model.field.stream_names

    def test_processes_dict(self):
        """Processes dict should map name to BuiltProcess."""
        xml = builder_model()

        model = build_model(xml)
        assert "Separation" in model.processes
        proc = model.processes["Separation"]
        assert isinstance(proc, BuiltProcess)
        assert proc.class_name == "Separation"

    def test_analysis_attributes(self):
        """Analysis attr_dict should contain typed values."""
        xml = builder_model()

        model = build_model(xml)
        assert model.analysis.name == "test"
        assert "functional_unit" in model.analysis.attr_dict

    def test_process_with_explicit_name(self):
        """Process with name attribute should use that name."""
        xml = builder_model(
            E_process("Boundary", name="ProductionBoundary", boundary="Production"),
            E_stream("Reservoir", "ProductionBoundary"),
        )

        model = build_model(xml)
        assert "ProductionBoundary" in model.processes
        assert model.processes["ProductionBoundary"].class_name == "Boundary"
