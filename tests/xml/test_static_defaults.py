"""Tests for Stage 1: Static defaults."""

from opgee.input.xml.static_defaults import apply_static_defaults
from tests.xml.fixture_data import model_with_field
from tests.xml.conftest import E_a, E_process


class TestApplyStaticDefaults:
    def test_adds_missing_defaults(self, loaded_attr_defs):
        """Field missing an attribute with a default should get <A> added."""
        xml = model_with_field(E_a("country", "US"))

        apply_static_defaults(xml)

        field = xml.find("Field")
        a_names = {a.get("name") for a in field.findall("A")}
        # 'age' should be added as a default from AttrDefs
        assert "age" in a_names

    def test_explicit_attrs_marked_true(self, loaded_attr_defs):
        """Existing <A> elements should be marked explicit='true'."""
        xml = model_with_field(E_a("country", "US"))

        apply_static_defaults(xml)

        field = xml.find("Field")
        country_a = None
        for a in field.findall("A"):
            if a.get("name") == "country":
                country_a = a
                break

        assert country_a is not None
        assert country_a.get("explicit") == "true"

    def test_default_attrs_marked_false(self, loaded_attr_defs):
        """New default <A> elements should be marked explicit='false'."""
        xml = model_with_field(E_a("country", "US"))

        apply_static_defaults(xml)

        field = xml.find("Field")
        age_a = None
        for a in field.findall("A"):
            if a.get("name") == "age":
                age_a = a
                break

        assert age_a is not None
        assert age_a.get("explicit") == "false"

    def test_process_gets_base_and_subclass_attrs(self, loaded_attr_defs):
        """Process elements should get both base Process attrs and subclass attrs."""
        xml = model_with_field(E_a("country", "US"), E_process("Separation"))

        apply_static_defaults(xml)

        proc = xml.find(".//Process[@class='Separation']")
        a_names = {a.get("name") for a in proc.findall("A")}

        # Should have base Process attributes
        attr_defs = loaded_attr_defs
        process_attrs = attr_defs.class_attrs("Process", raiseError=False)
        if process_attrs:
            for name, attr_def in process_attrs.attr_dict.items():
                if attr_def.default is not None:
                    assert name in a_names, f"Missing Process base attr '{name}'"

    def test_no_attr_added_when_no_default(self, loaded_attr_defs):
        """Attributes with no default should not get <A> elements."""
        xml = model_with_field(E_a("country", "US"))

        apply_static_defaults(xml)

        field = xml.find("Field")
        a_names = {a.get("name") for a in field.findall("A")}

        # Check that no attr with None default was added
        attr_defs = loaded_attr_defs
        field_attrs = attr_defs.class_attrs("Field", raiseError=False)
        if field_attrs:
            for name, attr_def in field_attrs.attr_dict.items():
                if attr_def.default is None and name != "country":
                    assert name not in a_names, (
                        f"Attr '{name}' has no default but was added"
                    )

    def test_analysis_gets_defaults(self, loaded_attr_defs):
        """Analysis element should also get static defaults."""
        xml = model_with_field(E_a("country", "US"))

        apply_static_defaults(xml)

        analysis = xml.find("Analysis")
        a_names = {a.get("name") for a in analysis.findall("A")}

        # Should have GWP_horizon or similar analysis defaults
        attr_defs = loaded_attr_defs
        analysis_attrs = attr_defs.class_attrs("Analysis", raiseError=False)
        if analysis_attrs:
            for name, attr_def in analysis_attrs.attr_dict.items():
                if attr_def.default is not None:
                    assert name in a_names, f"Missing Analysis attr '{name}'"

    def test_idempotent(self, loaded_attr_defs):
        """Running apply_static_defaults twice should not duplicate <A> elements."""
        xml = model_with_field(E_a("country", "US"))

        apply_static_defaults(xml)
        count_1 = len(xml.find("Field").findall("A"))

        apply_static_defaults(xml)
        count_2 = len(xml.find("Field").findall("A"))

        assert count_1 == count_2
