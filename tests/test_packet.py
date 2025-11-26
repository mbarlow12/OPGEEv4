import pytest
from opgee.manager import FieldPacket, _batched


def test_batched():
    with pytest.raises(ValueError, match="_batched: length must be > 0"):
        list(_batched([1, 2, 3], 0))


def test_field_packet():
    model_xml_file = "/foo/bar/baz.xml"
    field_names = ["a", "b", "c", "d"]
    analysis_name = "a3"
    pkt = FieldPacket(model_xml_file, analysis_name, field_names)

    assert pkt.model_xml_file == model_xml_file
    assert pkt.analysis_name == analysis_name
    assert pkt.items == field_names
    assert list(n for n in pkt) == field_names
