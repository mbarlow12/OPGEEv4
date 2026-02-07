"""Tests for Stage 4: Model object builders."""


from opgee.input.xml.builders import build_model, BuiltModel, BuiltField, BuiltProcess, BuiltAnalysis
from tests.xml.conftest import make_model_xml


class TestBuildModel:

    def test_builds_from_minimal_xml(self):
        """Should build a model from minimal XML."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )

        model = build_model(xml)

        assert isinstance(model, BuiltModel)
        assert isinstance(model.field, BuiltField)
        assert isinstance(model.analysis, BuiltAnalysis)

    def test_field_attributes(self):
        """Field attr_dict should contain typed values."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )

        model = build_model(xml)
        assert model.field.name == "test"
        assert "country" in model.field.attr_dict

    def test_process_names_collected(self):
        """Process names should be collected in BuiltField."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Process class="Drilling"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )

        model = build_model(xml)
        assert "Separation" in model.field.process_names
        assert "Drilling" in model.field.process_names

    def test_stream_names_collected(self):
        """Stream names should be collected in BuiltField."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
                <Stream src="Separation" dst="Flaring" name="gas for flaring"/>
            """,
        )

        model = build_model(xml)
        assert "Reservoir => Separation" in model.field.stream_names
        assert "gas for flaring" in model.field.stream_names

    def test_processes_dict(self):
        """Processes dict should map name to BuiltProcess."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )

        model = build_model(xml)
        assert "Separation" in model.processes
        proc = model.processes["Separation"]
        assert isinstance(proc, BuiltProcess)
        assert proc.class_name == "Separation"

    def test_analysis_attributes(self):
        """Analysis attr_dict should contain typed values."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )

        model = build_model(xml)
        assert model.analysis.name == "test"
        assert "functional_unit" in model.analysis.attr_dict

    def test_process_with_explicit_name(self):
        """Process with name attribute should use that name."""
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Boundary" name="ProductionBoundary" boundary="Production"/>
                <Stream src="Reservoir" dst="ProductionBoundary"/>
            """,
        )

        model = build_model(xml)
        assert "ProductionBoundary" in model.processes
        assert model.processes["ProductionBoundary"].class_name == "Boundary"
