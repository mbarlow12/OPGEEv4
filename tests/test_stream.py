"""Tests for opgee.stream.Stream.

Process-level stream-finding tests (``find_stream`` / ``find_output_stream``
etc.) will be reintroduced under Phase 6.2 once the new Field/Process API
is in place; for now we only exercise Stream's direct public surface.
"""
from opgee.chemistry import PHASE_GAS, PHASE_LIQUID, is_carbon_number
from opgee.core import TemperaturePressure
from opgee.stream import Stream


def test_carbon_number():
    assert is_carbon_number("C2") and is_carbon_number("C200")
    assert not is_carbon_number("foo")


def test_stream_utils():
    s = Stream("stream1", None)
    assert s.tp is None

    tp = TemperaturePressure(100, 200)
    s.set_tp(tp)

    assert s.tp.T.m == 100.0
    assert s.tp.P.m == 200.0


def test_to_dataframe():
    tp = TemperaturePressure(100, 200)
    s = Stream(
        "stream1", tp, src_name="src_proc", dst_name="dst_proc", contents=["gas"]
    )
    s.set_flow_rate("C1", PHASE_GAS, 12.5)
    s.set_flow_rate("oil", PHASE_LIQUID, 3.25)

    df = s.to_dataframe()

    # The legacy 'field' column was dropped in Phase 3.3.
    assert "field" not in df.columns
    assert list(df.columns) == [
        "stream",
        "source",
        "destination",
        "phase",
        "component",
        "value",
        "units",
    ]

    assert (df["stream"] == "stream1").all()
    assert (df["source"] == "src_proc").all()
    assert (df["destination"] == "dst_proc").all()

    # component rows present
    component_rows = df[df["phase"].isin(["gas", "liquid", "solid"])]
    components = set(component_rows["component"])
    assert "C1" in components
    assert "oil" in components

    # T and P rows appear with blank phase
    extras = df[df["phase"] == ""]
    assert set(extras["component"]) >= {"T", "P"}
