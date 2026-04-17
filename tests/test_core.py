import pytest
from opgee.units import ureg, magnitude, _undefined_units, validate_unit
from opgee.core import OpgeeObject, dict_from_list
from opgee.error import OpgeeException


def test_magnitude_error():
    q = ureg.Quantity(10.0, "tonnes/day")
    with pytest.raises(OpgeeException, match=r"magnitude: value .* units are not .*"):
        magnitude(q, ureg.Unit("tonnes/year"))


def test_dict_from_list():
    foo = OpgeeObject("foo")
    bar = OpgeeObject("bar")
    baz = OpgeeObject("baz")
    items = [foo, bar, baz]
    d = dict_from_list(items)

    assert len(d) == 3 and d['foo'] == foo and d['bar'] == bar and d['baz'] == baz


def test_dict_from_list_error():
    items = [OpgeeObject("foo"), OpgeeObject("bar"), OpgeeObject("foo")]
    with pytest.raises(OpgeeException, match="Duplicate name 'foo'"):
        dict_from_list(items)


def test_validate_unit_error():
    unit = 'not_a_unit'
    assert unit not in _undefined_units
    assert validate_unit(unit) is None and unit in _undefined_units
