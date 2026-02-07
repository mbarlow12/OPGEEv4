"""Test XSD schema validation for pre-pipeline and post-pipeline XML."""

from lxml import etree

from tests.xml.conftest import make_model_xml


class TestExtSchema:
    """Tests for opgee_ext.xsd (pre-pipeline input with ProcessChoice etc.)"""

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


class TestCoreSchema:
    """Tests for opgee_core.xsd (post-pipeline output, no ProcessChoice)."""

    def test_validates_clean_output(self, core_schema):
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
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
        xml = make_model_xml(
            analysis_body='<A name="functional_unit">oil</A>',
            field_body="""
                <A name="country" explicit="true">US</A>
                <Process class="Separation"/>
                <Stream src="Reservoir" dst="Separation"/>
            """,
        )
        assert core_schema.validate(xml), core_schema.error_log


class TestAttrSchema:
    """Tests for attributes.xsd."""

    def test_validates_attr_defs_structure(self, attr_schema):
        xml = etree.fromstring(b"""
        <AttrDefs>
            <ClassAttrs name="Field">
                <Options name="oil_type" default="conventional">
                    <Option>conventional</Option>
                    <Option label="heavy">heavy</Option>
                </Options>
                <AttrDef name="age" type="int" unit="yr">25</AttrDef>
                <AttrDef name="country" type="str">USA</AttrDef>
            </ClassAttrs>
        </AttrDefs>
        """)
        assert attr_schema.validate(xml), attr_schema.error_log

    def test_rejects_missing_class_name(self, attr_schema):
        xml = etree.fromstring(b"""
        <AttrDefs>
            <ClassAttrs>
                <AttrDef name="age" type="int">25</AttrDef>
            </ClassAttrs>
        </AttrDefs>
        """)
        assert not attr_schema.validate(xml)

    def test_validates_real_attributes_xml(self, attr_schema, attr_defs_elt):
        assert attr_schema.validate(attr_defs_elt), attr_schema.error_log
