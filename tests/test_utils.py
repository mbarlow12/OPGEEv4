import pytest

from opgee.error import OpgeeException
from opgee.utils import coercible, getBooleanXML, parse_boolean


@pytest.mark.parametrize(
    "value, expected", [
        ("true", True), ("yes", True), ("1", True), (True, True),
        ("false", False), ("no", False), ("0", False), (False, False),
    ]
)
def test_boolean_xml(value, expected):
    assert getBooleanXML(value) == expected
    assert parse_boolean(value) == expected


def test_boolean_xml_failure():
    with pytest.raises(OpgeeException, match="Cannot convert 'xyz' to boolean"):
        getBooleanXML("xyz")


def test_coercible():
    assert coercible(10, float) == 10.0
    assert coercible("11.5", float) == 11.5
    assert coercible("abc", int) is None
    assert coercible("abc", int, default=-1) == -1
