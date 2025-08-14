import pytest
from opgee.core.field import Field
from opgee.core.units import ureg
from .utils_for_tests import load_model_from_str
from opgee.core.error import XmlFormatError
from opgee.core.model import Model
from opgee.xml.parsers import parse_field
from .utils_for_tests import load_test_model
from .test_processes import approx_equal

model_xml_1 = """
<Model xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../../opgee/etc/opgee.xsd">
	<A name="skip_validation">1</A>

	<Analysis name="test">
	  <A name="functional_unit">oil</A>
	  <A name="GWP_horizon">100</A>
	  <A name="GWP_version">AR5</A>
      <FieldRef name="test1"/>
	</Analysis>

	<Field name="test1">
		<A name="country">USA</A>
		<Process class="After"/>
		<Process class="ProcA" desc="Test process 1"/>
		<Process class="ProcB" desc="Test process 2"/>
		<Process class="Boundary" boundary="UnknownBoundary"/>

		<Stream src="ProcB" dst="ProductionBoundary"/>
	</Field>

</Model>
"""

model_xml_2 = """
<Model xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../../opgee/etc/opgee.xsd">
	<A name="skip_validation">1</A>

	<Analysis name="test">
	  <A name="functional_unit">oil</A>
	  <A name="GWP_horizon">100</A>
	  <A name="GWP_version">AR5</A>
      <FieldRef name="test1"/>
	</Analysis>

	<Field name="test1">
		<A name="country">USA</A>
		<Process class="After"/>
		<Process class="ProcA" desc="Test process 1"/>
		<Process class="ProcB" desc="Test process 2"/>
		<Process class="Boundary" boundary="Production"/>
		<Process class="Boundary" boundary="Production"/>

		<Stream src="ProcB" dst="ProductionBoundary"/>
	</Field>

</Model>
"""


@pytest.fixture(scope="module")
def test_field(configure_logging_for_tests):
    return load_test_model(
        "test_fields.xml", use_default_model=True
    )  # this is required since test_fields references "template" field


def test_component_fugitive(test_field):
    analysis = test_field.get_analysis("test_fugitive")
    oilfield = analysis.get_field("test_component_fugitive_oilfield")
    oilfield_component_fugitive_df = oilfield.component_fugitive_table

    assert approx_equal(
        oilfield_component_fugitive_df["Separation"],
        ureg.Quantity(3.053545e-05, "frac"),
    )
    assert approx_equal(
        oilfield_component_fugitive_df["CrudeOilStorage"],
        ureg.Quantity(0.931951, "frac"),
    )
    assert approx_equal(
        oilfield_component_fugitive_df["DownholePump"],
        ureg.Quantity(0.000410132, "frac"),
    )

    gasfield = analysis.get_field("test_component_fugitive_gasfield")
    gasfield_component_fugitive_df = gasfield.component_fugitive_table

    assert approx_equal(
        gasfield_component_fugitive_df["Separation"], ureg.Quantity(3.77813e-5, "frac")
    )
    assert approx_equal(
        gasfield_component_fugitive_df["CrudeOilStorage"],
        ureg.Quantity(0.4323671, "frac"),
    )
    assert approx_equal(
        gasfield_component_fugitive_df["DownholePump"],
        ureg.Quantity(7.220268674108583e-05, "frac"),
    )


def test_bad_boundary():
    with pytest.raises(
        XmlFormatError, match=".*UnknownBoundary is not a known boundary name.*"
    ):
        model = load_model_from_str(model_xml_1)

    with pytest.raises(XmlFormatError, match=".*duplicate.*"):
        model = load_model_from_str(model_xml_2)

    # with pytest.raises(XmlFormatError, match=".*Duplicate declaration of boundary.*"):
    #     model = load_model_from_str(model_xml_2)

    # model.validate()
    # analysis = model.get_analysis('test')


def test_new_parse_field_integration(test_field):
    """Test new XML parser integrates correctly with existing codebase."""
    from xml.etree import ElementTree as ET

    # Test parsing with actual working field structure
    field_xml = """
    <Field name="integration_test_field">
        <A name="country">USA</A>
        <A name="well_diam">2.89</A>
        <A name="res_temp">200</A>
        <A name="res_press">1556.6</A>
        <Process class="Separation"/>
        <Process class="CrudeOilDewatering"/>
        <Stream src="Separation" dst="CrudeOilDewatering"/>
    </Field>
    """

    element = ET.fromstring(field_xml)

    # Parse with new method
    parsed_field = Field.from_xml(element, parent=test_field, use_new=True)

    # Test basic functionality
    assert parsed_field.name == "integration_test_field"
    assert parsed_field.model == test_field

    # Test that field has processes and streams
    processes = list(parsed_field.processes())
    streams = list(parsed_field.streams())
    assert len(processes) >= 2
    assert len(streams) >= 1


def test_parse_field_old_vs_new_equivalence(test_field):
    """Test that new parser produces equivalent results to old method."""
    from xml.etree import ElementTree as ET

    field_xml = """
    <Model>
    <Field name="equivalence_test_field" modifies="template">
        <A name="country">USA</A>
        <A name="well_diam">2.88</A>
        <A name="res_temp">200</A>
        <A name="res_press">1556.6</A>
        <Process class="Separation"/>
        <Process class="CrudeOilDewatering"/>
        <Stream src="Separation" dst="CrudeOilDewatering"/>
    </Field>
    </Model>
    """

    element = ET.fromstring(field_xml)

    # Parse with old method
    old_field = Field.from_xml(element, parent=test_field, use_new=False)

    # Parse with new method
    new_field = Field.from_xml(element, parent=test_field, use_new=True)

    # Assert structural equivalence
    assert old_field.name == new_field.name
    assert old_field.attr_dict.keys() == new_field.attr_dict.keys()
    assert len(list(old_field.processes())) == len(list(new_field.processes()))
    assert len(list(old_field.streams())) == len(list(new_field.streams()))
    assert old_field.group_names == new_field.group_names


def test_parse_field_performance_comparison(test_field):
    """Test that parse_field performance is comparable to original method."""
    import time
    from xml.etree import ElementTree as ET

    analysis = test_field.get_analysis("test_fugitive")

    field_xml = """
    <Field name="perf_test_field">
        <A name="country">USA</A>
        <A name="well_diam">2.89</A>
        <A name="res_temp">200</A>
        <A name="res_press">1556.6</A>
        <Process class="Separation"/>
        <Process class="CrudeOilDewatering"/>
        <Stream src="Separation" dst="CrudeOilDewatering"/>
    </Field>
    """

    element = ET.fromstring(field_xml)

    # Time new method
    start_time = time.time()
    for _ in range(10):
        field = parse_field(element, parent=test_field)
    new_time = time.time() - start_time

    # Time old method
    start_time = time.time()
    for _ in range(10):
        field = Field.from_xml(element, parent=test_field, use_new=False)
    old_time = time.time() - start_time

    # New method should be within reasonable performance bounds
    # Allow up to 15% performance difference as specified in requirements
    assert new_time < old_time * 1.15, (
        f"New method too slow: {new_time}s vs {old_time}s"
    )
