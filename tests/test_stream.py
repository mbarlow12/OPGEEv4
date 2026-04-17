"""Tests for opgee.stream.Stream.

Process-level stream-finding tests (``find_stream`` / ``find_output_stream``
etc.) will be reintroduced under Phase 6.2 once the new Field/Process API
is in place; for now we only exercise Stream's direct public surface.
"""
import pytest
from opgee.chemistry import CARBON_NUMBER, PHASE_GAS, PHASE_LIQUID, is_carbon_number
from opgee.core import TemperaturePressure
from opgee.stream import Stream
from opgee.thermodynamics import ChemicalInfo


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


def test_combustion_math():
    """Smoke-test the Stream math surface that doesn't require a Field."""
    tp = TemperaturePressure(60, 14.7)

    # 1. Build source stream with C1=1.0 t/day and C2=2.0 t/day in gas phase.
    src = Stream("src", tp)
    src.set_flow_rate("C1", PHASE_GAS, 1.0)
    src.set_flow_rate("C2", PHASE_GAS, 2.0)

    # 2. copy_flow_rates_from copies all phases.
    dst = Stream("dst", tp)
    dst.copy_flow_rates_from(src)
    assert dst.gas_flow_rate("C1").m == pytest.approx(1.0)
    assert dst.gas_flow_rate("C2").m == pytest.approx(2.0)

    # 3. multiply_flow_rates doubles all values.
    dst.multiply_flow_rates(2.0)
    assert dst.gas_flow_rate("C1").m == pytest.approx(2.0)
    assert dst.gas_flow_rate("C2").m == pytest.approx(4.0)

    # 4. reset() leaves stream uninitialized and zero-valued.
    dst.reset()
    assert dst.is_uninitialized()
    assert dst.gas_flow_rate("C1").m == pytest.approx(0.0)

    # 5. Re-initialize; non_zero_flow_rates returns only set components.
    dst.set_flow_rate("C1", PHASE_GAS, 3.0)
    dst.set_flow_rate("C2", PHASE_GAS, 4.0)
    nz = dst.non_zero_flow_rates()
    assert set(nz.index) == {"C1", "C2"}

    # 6. voc_flow_rates: C2 is a VOC, C1 (methane) is not.
    vocs = dst.voc_flow_rates()
    assert "C2" in vocs.index
    assert "C1" not in vocs.index

    # 7. add_combustion_CO2_from: verify CO2 rate from complete combustion of src.
    mw = ChemicalInfo.mol_weights()
    expected_co2 = (
        1.0 / mw["C1"].m * CARBON_NUMBER["C1"] * mw["CO2"].m
        + 2.0 / mw["C2"].m * CARBON_NUMBER["C2"] * mw["CO2"].m
    )
    co2_stream = Stream("co2_out", tp)
    co2_stream.add_combustion_CO2_from(src)
    assert co2_stream.gas_flow_rate("CO2").m == pytest.approx(expected_co2, rel=1e-4)
