"""Tests for opgee.context — FieldContext and frozen config dataclasses."""
import pandas as pd
import pytest

from opgee.context import FieldContext, GWPData, SimulationParams
from opgee.core import STP
from opgee.table_manager import TableManager


def test_gwp_data_frozen():
    gwp = GWPData(values=pd.Series({"CO2": 1.0, "CH4": 30.0}), horizon=100)
    assert gwp.horizon == 100
    assert gwp.values["CH4"] == 30.0
    with pytest.raises(AttributeError):
        gwp.horizon = 20


def test_simulation_params_frozen():
    sim = SimulationParams(maximum_iterations=10, maximum_change=0.001)
    assert sim.maximum_iterations == 10
    with pytest.raises(AttributeError):
        sim.maximum_iterations = 20


def test_field_context_creation():
    ctx = FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=pd.Series({"CO2": 1.0}), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
    assert ctx.stp is STP
    assert isinstance(ctx.process_data, dict)
    assert len(ctx.process_data) == 0


def test_field_context_process_data_mutable():
    ctx = FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=pd.Series({"CO2": 1.0}), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
    ctx.process_data["key"] = "value"
    assert ctx.process_data["key"] == "value"


def test_field_context_table_access():
    ctx = FieldContext(
        stp=STP,
        tables=TableManager(),
        gwp=GWPData(values=pd.Series({"CO2": 1.0}), horizon=100),
        simulation=SimulationParams(maximum_iterations=10, maximum_change=0.001),
    )
    tbl = ctx.tables.get_table("constants")
    assert tbl is not None
