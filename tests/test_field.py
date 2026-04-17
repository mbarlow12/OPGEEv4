"""Tests for opgee.field — direct Field construction after the v5 deep-clean.

Field is now built from explicit Python arguments rather than XML. This
suite exercises:
  - `Field.__init__` wiring (processes, streams, FieldContext).
  - `Field.run()` on a trivial graph (Reservoir -> StubProc -> Sink).
  - The graph-helper methods `find_process`, `find_stream`,
    `save_process_data` / `get_process_data`.
  - `Field.get_completion_and_workover_C1_rate` end-to-end, using the
    real `well-completion-and-workover-C1-rate` CSV via TableManager.
"""
from __future__ import annotations

import pandas as pd
import pytest

from opgee.context import GWPData, SimulationParams
from opgee.core import STP
from opgee.field import Field
from opgee.process import Process
from opgee.stream import Stream
from opgee.table_manager import TableManager
from opgee.thermodynamics import Gas, Oil, Water
from opgee.units import ureg


class StubProc(Process):
    """Minimal Process subclass whose `run` just increments a counter."""

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self.run_calls = 0

    def run(self):
        self.run_calls += 1


class SinkProc(StubProc):
    """Sink process — structurally identical to StubProc but named for clarity."""


def _build_thermo() -> tuple[Oil, Gas, Water]:
    """Construct the three thermodynamic helpers with minimal params."""
    res_temp = ureg.Quantity(200.0, "degF")
    res_press = ureg.Quantity(1500.0, "psia")
    TDS = ureg.Quantity(50000.0, "mg/L")
    API = ureg.Quantity(32.0, "degAPI")
    gas_comp = pd.Series(
        {"N2": 0.0, "CO2": 2.0, "C1": 92.0, "C2": 3.0, "C3": 2.0, "C4": 1.0, "H2S": 0.0},
        dtype="pint[mol_pct]",
    )
    gas_oil_ratio = ureg.Quantity(1000.0, "scf/bbl_oil")

    oil = Oil(
        API=API,
        gas_comp=gas_comp,
        gas_oil_ratio=gas_oil_ratio,
        res_temp=res_temp,
        res_press=res_press,
        TDS=TDS,
    )
    gas = Gas(res_temp=res_temp, res_press=res_press)
    water = Water(res_temp=res_temp, res_press=res_press, TDS=TDS)
    return oil, gas, water


def _build_field() -> Field:
    """Helper: construct a trivial Field with Reservoir -> StubA -> Sink."""
    oil, gas, water = _build_thermo()
    sim = SimulationParams(maximum_iterations=10, maximum_change=0.001)
    gwp = GWPData(
        values=pd.Series({"VOC": 0.0, "CO": 0.0, "CH4": 30.0, "N2O": 265.0, "CO2": 1.0}),
        horizon=100,
    )
    tables = TableManager()

    # Note: we pass placeholder Process instances without ctx wiring; Field
    # does not inject ctx into pre-built processes (they get it via their
    # own __init__ per the Phase 5 contract). We therefore construct them
    # against a throwaway ctx here. Field will hold its own FieldContext;
    # the stubs don't rely on it beyond what their constructors stored.
    from opgee.context import FieldContext

    ctx_for_procs = FieldContext(stp=STP, tables=tables, gwp=gwp, simulation=sim)

    stub_a = StubProc("StubA", ctx_for_procs)
    sink = SinkProc("Sink", ctx_for_procs)

    # Reservoir is built by Field.__init__ unless supplied; let Field build it.
    streams = [
        Stream("res_to_a", tp=STP, src_name="Reservoir", dst_name="StubA"),
        Stream("a_to_sink", tp=STP, src_name="StubA", dst_name="Sink"),
    ]

    field = Field(
        name="test_field",
        simulation=sim,
        gwp=gwp,
        tables=tables,
        processes=[stub_a, sink],
        streams=streams,
        oil=oil,
        gas=gas,
        water=water,
        num_prod_wells=10,
        oil_sands_mine="None",
        field_production_lifetime=ureg.Quantity(30.0, "year"),
        res_press=ureg.Quantity(1500.0, "psia"),
        res_temp=ureg.Quantity(200.0, "degF"),
        has_grid_mix=False,
    )
    return field


def test_field_construction() -> None:
    """Field wires processes/streams into a 3-node DiGraph."""
    field = _build_field()

    assert field.name == "test_field"
    assert set(field.process_dict) == {"Reservoir", "StubA", "Sink"}
    assert set(field.stream_dict) == {"res_to_a", "a_to_sink"}
    assert field.graph.number_of_nodes() == 3
    assert field.graph.number_of_edges() == 2
    assert field.cycles == []


def test_find_helpers() -> None:
    field = _build_field()
    assert field.find_process("StubA").name == "StubA"
    assert field.find_stream("res_to_a").src_name == "Reservoir"
    assert field.find_process("DoesNotExist", raiseError=False) is None


def test_process_data_bulletin_board() -> None:
    field = _build_field()
    field.save_process_data(foo=42, bar="hello")
    assert field.get_process_data("foo") == 42
    assert field.get_process_data("bar") == "hello"
    assert field.get_process_data("missing") is None


def test_field_run_calls_each_process_once() -> None:
    """A trivial linear graph runs each process exactly once."""
    field = _build_field()
    field.run()

    stub = field.find_process("StubA")
    sink = field.find_process("Sink")
    assert stub.run_calls == 1
    assert sink.run_calls == 1


def test_get_completion_and_workover_C1_rate_smoke() -> None:
    """End-to-end call using the real CSV table via TableManager."""
    field = _build_field()
    rate = field.get_completion_and_workover_C1_rate(
        workovers_per_well=ureg.Quantity(1.1, "frac"),
        is_flaring="No",
        is_REC="No",
        frac_well_fractured=ureg.Quantity(0.5, "frac"),
    )
    # We don't care about the exact value, only that it's a Quantity
    # with sensible units (tonne/year or similar).
    assert rate is not None
    assert hasattr(rate, "m")


def test_duplicate_process_name_raises() -> None:
    """Two processes with the same name must fail construction."""
    from opgee.context import FieldContext
    from opgee.error import OpgeeException

    oil, gas, water = _build_thermo()
    sim = SimulationParams(maximum_iterations=10, maximum_change=0.001)
    gwp = GWPData(
        values=pd.Series({"CO2": 1.0, "CH4": 30.0}),
        horizon=100,
    )
    tables = TableManager()
    ctx = FieldContext(stp=STP, tables=tables, gwp=gwp, simulation=sim)

    dup1 = StubProc("Dup", ctx)
    dup2 = StubProc("Dup", ctx)

    with pytest.raises(OpgeeException, match="Duplicate process name"):
        Field(
            name="f",
            simulation=sim,
            gwp=gwp,
            tables=tables,
            processes=[dup1, dup2],
            streams=[],
            oil=oil,
            gas=gas,
            water=water,
        )
