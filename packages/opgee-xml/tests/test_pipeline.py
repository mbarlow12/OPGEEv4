"""End-to-end tests for process_field_xml() pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from opgee_input import AnalysisInput, FieldInput

from opgee_xml import ParsedField, process_field_xml

from .conftest import make_field_xml


def _model_with_fields(*fields: etree._Element) -> etree._Element:
    """Build a <Model> with the given <Field> children."""
    model = etree.Element("Model")
    for f in fields:
        model.append(f)
    return model


def _write_model(tmp_xml_file, model_elt: etree._Element) -> Path:
    """Serialize a model element to a temp file."""
    return tmp_xml_file(model_elt)


class TestProcessFieldXml:
    def test_returns_iterator(self, tmp_xml_file):
        model = _model_with_fields(make_field_xml("f1"))
        path = _write_model(tmp_xml_file, model)
        result = process_field_xml(path)
        assert hasattr(result, "__next__")

    def test_minimal_field(self, tmp_xml_file):
        model = _model_with_fields(make_field_xml("test_field"))
        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        assert len(results) == 1
        pf = results[0]
        assert isinstance(pf, ParsedField)
        assert isinstance(pf.field, FieldInput)
        assert pf.field.name == "test_field"
        assert isinstance(pf.choices, dict)
        assert pf.analysis is None

    def test_parsed_field_has_processes(self, tmp_xml_file):
        model = _model_with_fields(make_field_xml("f1"))
        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        assert len(results[0].field.processes) > 0

    def test_multiple_fields(self, tmp_xml_file):
        model = _model_with_fields(
            make_field_xml("f1"),
            make_field_xml("f2"),
        )
        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        assert len(results) == 2
        names = {r.field.name for r in results}
        assert names == {"f1", "f2"}

    def test_field_with_analysis(self, tmp_xml_file):
        model = etree.Element("Model")
        analysis = etree.SubElement(model, "Analysis", name="a1")
        group = etree.SubElement(analysis, "Group")
        group.text = "grp"
        gwp = etree.SubElement(analysis, "GWP_horizon")
        gwp.text = "100"
        field = make_field_xml("f1")
        field.set("group", "grp")
        model.append(field)

        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        assert len(results) == 1
        assert results[0].analysis is not None
        assert isinstance(results[0].analysis, AnalysisInput)
        assert results[0].analysis.name == "a1"
        assert results[0].group == "grp"

    def test_pre_resolution_validation_error(self, tmp_xml_file):
        # Model with no fields
        model = etree.Element("Model")
        path = _write_model(tmp_xml_file, model)
        with pytest.raises(ValueError, match="Pre-resolution validation failed"):
            list(process_field_xml(path))

    def test_post_resolution_no_processes_error(self, tmp_xml_file):
        # Field with no process children
        model = etree.Element("Model")
        etree.SubElement(model, "Field", name="empty")
        path = _write_model(tmp_xml_file, model)
        with pytest.raises(ValueError, match="Post-resolution validation failed"):
            list(process_field_xml(path))

    def test_choices_dict_populated(self, tmp_xml_file):
        model = _model_with_fields(make_field_xml("f1"))
        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        # No inc elements, so choices should be empty
        assert results[0].choices == {}

    def test_group_propagated(self, tmp_xml_file):
        model = etree.Element("Model")
        field = make_field_xml("f1")
        field.set("group", "my_group")
        model.append(field)
        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        assert results[0].group == "my_group"

    def test_group_none_when_absent(self, tmp_xml_file):
        model = _model_with_fields(make_field_xml("f1"))
        path = _write_model(tmp_xml_file, model)
        results = list(process_field_xml(path))
        assert results[0].group is None
