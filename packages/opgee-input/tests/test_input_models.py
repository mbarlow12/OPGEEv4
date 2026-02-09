"""Tests for opgee-input dataclass models."""
from __future__ import annotations

import pytest

from opgee_input import (
    AnalysisInput,
    ContainsSpec,
    FieldInput,
    ModelInput,
    PROCESS_CLASSES,
    ProcessBase,
    StreamInput,
)
from opgee_input.processes import (
    AcidGasRemoval,
    BitumenMining,
    Boundary,
    CO2InjectionWell,
    CO2Membrane,
    CO2ReinjectionCompressor,
    CrudeOilDewatering,
    CrudeOilStabilization,
    CrudeOilStorage,
    CrudeOilTransport,
    Demethanizer,
    DownholePump,
    Drilling,
    Exploration,
    Flaring,
    GasDehydration,
    GasDistribution,
    GasGathering,
    GasLiftingCompressor,
    GasPartition,
    GasReinjectionCompressor,
    GasReinjectionWell,
    HeavyOilDilution,
    HeavyOilUpgrading,
    LNGLiquefaction,
    LNGRegasification,
    LNGTransport,
    NGL,
    PetrocokeTransport,
    PostStorageCompressor,
    PreMembraneChiller,
    PreMembraneCompressor,
    Reservoir,
    ReservoirWellInterface,
    RyanHolmes,
    Separation,
    SourGasCompressor,
    SourGasInjection,
    SteamGeneration,
    StorageCompressor,
    StorageSeparator,
    StorageWell,
    TransmissionCompressor,
    VFPartition,
    Venting,
    VRUCompressor,
    WaterInjection,
    WaterTreatment,
)


# ---------------------------------------------------------------------------
# Base / OPGEEInput
# ---------------------------------------------------------------------------


class TestOPGEEInput:
    def test_model_fields_set_tracks_explicit_args(self):
        p = ProcessBase(enabled=True)
        assert "enabled" in p.model_fields_set
        assert "boundary" not in p.model_fields_set

    def test_model_fields_set_empty_when_all_defaults(self):
        p = ProcessBase()
        assert p.model_fields_set == set()


# ---------------------------------------------------------------------------
# ProcessBase
# ---------------------------------------------------------------------------


class TestProcessBase:
    def test_defaults(self):
        p = ProcessBase()
        assert p.enabled is None
        assert p.boundary is None
        assert p.after is None
        assert p.impute_start is None
        assert p.cycle_start is None
        assert p.leak_rate == 0.0

    def test_keyword_construction(self):
        p = ProcessBase(enabled=True, boundary="Production", leak_rate=1.5)
        assert p.enabled is True
        assert p.boundary == "Production"
        assert p.leak_rate == 1.5

    def test_type_coercion_string_to_float(self):
        p = ProcessBase(leak_rate="2.5")
        assert p.leak_rate == 2.5

    def test_type_coercion_string_to_bool(self):
        p = ProcessBase(enabled="true")
        assert p.enabled is True


# ---------------------------------------------------------------------------
# All 51 process classes construct correctly
# ---------------------------------------------------------------------------

ALL_PROCESS_CLASSES = [
    AcidGasRemoval,
    BitumenMining,
    Boundary,
    CO2InjectionWell,
    CO2Membrane,
    CO2ReinjectionCompressor,
    CrudeOilDewatering,
    CrudeOilStabilization,
    CrudeOilStorage,
    CrudeOilTransport,
    Demethanizer,
    DownholePump,
    Drilling,
    Exploration,
    Flaring,
    GasDehydration,
    GasDistribution,
    GasGathering,
    GasLiftingCompressor,
    GasPartition,
    GasReinjectionCompressor,
    GasReinjectionWell,
    HeavyOilDilution,
    HeavyOilUpgrading,
    LNGLiquefaction,
    LNGRegasification,
    LNGTransport,
    NGL,
    PetrocokeTransport,
    PostStorageCompressor,
    PreMembraneChiller,
    PreMembraneCompressor,
    Reservoir,
    ReservoirWellInterface,
    RyanHolmes,
    Separation,
    SourGasCompressor,
    SourGasInjection,
    SteamGeneration,
    StorageCompressor,
    StorageSeparator,
    StorageWell,
    TransmissionCompressor,
    VFPartition,
    Venting,
    VRUCompressor,
    WaterInjection,
    WaterTreatment,
]


@pytest.mark.parametrize("cls", ALL_PROCESS_CLASSES, ids=lambda c: c.__name__)
class TestAllProcessClasses:
    def test_construct_with_defaults(self, cls):
        obj = cls()
        assert isinstance(obj, ProcessBase)

    def test_is_in_process_classes_map(self, cls):
        assert cls.__name__ in PROCESS_CLASSES
        assert PROCESS_CLASSES[cls.__name__] is cls


def test_process_classes_count():
    assert len(PROCESS_CLASSES) == 48


# ---------------------------------------------------------------------------
# Specific process field checks
# ---------------------------------------------------------------------------


class TestAcidGasRemoval:
    def test_defaults(self):
        p = AcidGasRemoval()
        assert p.eta_reboiler == 1.25
        assert p.air_cooler_delta_T == 40.0
        assert p.type_amine == "MDEA"
        assert p.prime_mover_type == "NG_engine"

    def test_literal_validation_rejects_invalid(self):
        with pytest.raises(Exception):
            AcidGasRemoval(type_amine="InvalidAmine")

    def test_literal_validation_rejects_invalid_prime_mover(self):
        with pytest.raises(Exception):
            AcidGasRemoval(prime_mover_type="Steam_turbine")


class TestSeparation:
    def test_defaults(self):
        s = Separation()
        assert s.number_stages == 2
        assert s.pressure_first_stage == 500.0
        assert s.eta_compressor == 75.0

    def test_override(self):
        s = Separation(number_stages=3, pressure_first_stage=600.0)
        assert s.number_stages == 3
        assert s.pressure_first_stage == 600.0


class TestHeavyOilDilution:
    def test_dilution_type_none_default(self):
        h = HeavyOilDilution()
        assert h.dilution_type is None

    def test_dilution_type_valid(self):
        h = HeavyOilDilution(dilution_type="Diluent")
        assert h.dilution_type == "Diluent"

    def test_dilution_type_invalid(self):
        with pytest.raises(Exception):
            HeavyOilDilution(dilution_type="InvalidType")


class TestTransmissionCompressor:
    def test_defaults(self):
        t = TransmissionCompressor()
        assert t.press_drop_per_dist == 15.67
        assert t.transmission_dist == 680.0
        assert t.gas_to_storage_frac == 0.0


class TestGasPartition:
    def test_co2_source_literal(self):
        g = GasPartition(CO2_source="Anthropogenic")
        assert g.CO2_source == "Anthropogenic"

    def test_co2_source_invalid(self):
        with pytest.raises(Exception):
            GasPartition(CO2_source="Synthetic")


# ---------------------------------------------------------------------------
# ContainsSpec
# ---------------------------------------------------------------------------


class TestContainsSpec:
    def test_defaults(self):
        c = ContainsSpec()
        assert c.value is None
        assert c.delete is None

    def test_with_values(self):
        c = ContainsSpec(value="gas", delete=True)
        assert c.value == "gas"
        assert c.delete is True


# ---------------------------------------------------------------------------
# StreamInput
# ---------------------------------------------------------------------------


class TestStreamInput:
    def test_required_fields(self):
        with pytest.raises(Exception):
            StreamInput()

    def test_minimal_construction(self):
        s = StreamInput(src="Separation", dst="GasGathering")
        assert s.src == "Separation"
        assert s.dst == "GasGathering"
        assert s.name is None
        assert s.contains == []

    def test_with_contains(self):
        s = StreamInput(
            src="A",
            dst="B",
            contains=[ContainsSpec(value="oil"), ContainsSpec(value="gas")],
        )
        assert len(s.contains) == 2
        assert s.contains[0].value == "oil"

    def test_fields_set_tracking(self):
        s = StreamInput(src="A", dst="B", impute=True)
        assert "impute" in s.model_fields_set
        assert "boundary" not in s.model_fields_set


# ---------------------------------------------------------------------------
# AnalysisInput
# ---------------------------------------------------------------------------


class TestAnalysisInput:
    def test_required_name(self):
        with pytest.raises(Exception):
            AnalysisInput()

    def test_defaults(self):
        a = AnalysisInput(name="test")
        assert a.GWP_horizon is None
        assert a.GWP_version is None
        assert a.functional_unit is None
        assert a.boundary is None

    def test_literal_validation(self):
        a = AnalysisInput(name="test", GWP_horizon="100", GWP_version="AR5")
        assert a.GWP_horizon == "100"
        assert a.GWP_version == "AR5"

    def test_invalid_gwp_horizon(self):
        with pytest.raises(Exception):
            AnalysisInput(name="test", GWP_horizon="50")

    def test_invalid_boundary(self):
        with pytest.raises(Exception):
            AnalysisInput(name="test", boundary="Invalid")


# ---------------------------------------------------------------------------
# FieldInput
# ---------------------------------------------------------------------------


class TestFieldInput:
    def test_required_name(self):
        with pytest.raises(Exception):
            FieldInput()

    def test_minimal_construction(self):
        f = FieldInput(name="test-field")
        assert f.name == "test-field"
        assert f.enabled is None
        assert f.processes == []
        assert f.streams == []

    def test_defaults(self):
        f = FieldInput(name="f")
        assert f.downhole_pump == 1
        assert f.country == "Generic"
        assert f.age == 38.0
        assert f.API == 32.8
        assert f.gas_comp_C1 == 89.18
        assert f.GLIR == 364.0
        assert f.wellhead_pressure == 500.0

    def test_smart_default_fields_none(self):
        f = FieldInput(name="f")
        assert f.depth is None
        assert f.num_prod_wells is None
        assert f.res_press is None
        assert f.res_temp is None
        assert f.GOR is None
        assert f.WOR is None
        assert f.GFIR is None
        assert f.SOR is None
        assert f.fraction_elec_onsite is None
        assert f.fraction_remaining_gas_inj is None
        assert f.stabilizer_column is None
        assert f.prod_water_inlet_temp is None
        assert f.ecosystem_richness is None
        assert f.field_development_intensity is None

    def test_literal_fields(self):
        f = FieldInput(
            name="f",
            liquids_unloading="Plunger",
            eta_rig="High",
            well_complexity="Complex",
            well_size="Extra Large",
            flood_gas_type="CO2",
        )
        assert f.liquids_unloading == "Plunger"
        assert f.eta_rig == "High"
        assert f.well_complexity == "Complex"
        assert f.well_size == "Extra Large"
        assert f.flood_gas_type == "CO2"

    def test_literal_validation_rejects_invalid(self):
        with pytest.raises(Exception):
            FieldInput(name="f", liquids_unloading="InvalidValue")

    def test_type_coercion(self):
        f = FieldInput(name="f", age="25.5", offshore="1")
        assert f.age == 25.5
        assert f.offshore == 1

    def test_with_processes(self):
        f = FieldInput(
            name="f",
            processes=[
                Separation(number_stages=3),
                Flaring(),
                Boundary(),
            ],
        )
        assert len(f.processes) == 3
        assert isinstance(f.processes[0], Separation)
        assert f.processes[0].number_stages == 3

    def test_with_streams(self):
        f = FieldInput(
            name="f",
            streams=[
                StreamInput(src="Separation", dst="GasGathering"),
                StreamInput(src="GasGathering", dst="Flaring"),
            ],
        )
        assert len(f.streams) == 2

    def test_fields_set_tracking(self):
        f = FieldInput(name="f", API=35.0, depth=1000.0)
        assert "name" in f.model_fields_set
        assert "API" in f.model_fields_set
        assert "depth" in f.model_fields_set
        assert "age" not in f.model_fields_set

    def test_mixed_processes_and_streams(self):
        f = FieldInput(
            name="test",
            processes=[
                Separation(),
                GasGathering(),
                AcidGasRemoval(type_amine="MEA"),
            ],
            streams=[
                StreamInput(src="Separation", dst="GasGathering"),
                StreamInput(
                    src="GasGathering",
                    dst="AcidGasRemoval",
                    contains=[ContainsSpec(value="gas")],
                ),
            ],
        )
        assert len(f.processes) == 3
        assert len(f.streams) == 2
        assert isinstance(f.processes[2], AcidGasRemoval)
        assert f.processes[2].type_amine == "MEA"
        assert f.streams[1].contains[0].value == "gas"


# ---------------------------------------------------------------------------
# ModelInput
# ---------------------------------------------------------------------------


class TestModelInput:
    def test_empty_model(self):
        m = ModelInput()
        assert m.schema_version is None
        assert m.analyses == []
        assert m.fields == []

    def test_field_property_empty(self):
        m = ModelInput()
        assert m.field is None
        assert m.analysis is None

    def test_field_property_with_data(self):
        m = ModelInput(
            fields=[FieldInput(name="f1"), FieldInput(name="f2")],
            analyses=[AnalysisInput(name="a1")],
        )
        assert m.field is not None
        assert m.field.name == "f1"
        assert m.analysis is not None
        assert m.analysis.name == "a1"

    def test_full_model(self):
        m = ModelInput(
            schema_version="4.0",
            analyses=[
                AnalysisInput(
                    name="test-analysis",
                    GWP_horizon="100",
                    functional_unit="oil",
                ),
            ],
            fields=[
                FieldInput(
                    name="test-field",
                    API=30.0,
                    processes=[Separation(), Flaring()],
                    streams=[StreamInput(src="Separation", dst="Flaring")],
                ),
            ],
        )
        assert m.schema_version == "4.0"
        assert len(m.analyses) == 1
        assert len(m.fields) == 1
        assert m.field.API == 30.0
        assert len(m.field.processes) == 2
