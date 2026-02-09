"""Process input dataclasses.

Each Process subclass is a pure pydantic dataclass with kw_only=True.
ProcessUnion at the bottom is the Union of all 51 types.
"""
from __future__ import annotations

from typing import Literal, Union

from .base import OPGEEInput, opgee_dataclass


# --- Process base attributes (shared by all processes) ---


@opgee_dataclass
class ProcessBase(OPGEEInput):
    """Common attributes for process elements."""

    enabled: bool | None = None
    boundary: str | None = None
    after: bool | None = None
    impute_start: bool | None = None
    cycle_start: bool | None = None
    leak_rate: float = 0.0


# --- Process models (alphabetical by class name) ---


@opgee_dataclass
class AcidGasRemoval(ProcessBase):
    eta_reboiler: float = 1.25
    air_cooler_delta_T: float = 40.0
    air_cooler_fan_eff: float = 70.0
    air_cooler_press_drop: float = 0.6
    air_cooler_speed_reducer_eff: float = 92.0
    eta_compressor: float = 75.0
    type_amine: Literal["conv DEA", "high DEA", "MEA", "DGA", "MDEA"] = "MDEA"
    ratio_reflux_reboiler: float = 2.0
    regeneration_temp: float = 205.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"


@opgee_dataclass
class BitumenMining(ProcessBase):
    CH4_loss_rate: float = 22.881511207


@opgee_dataclass
class Boundary(ProcessBase):
    pass


@opgee_dataclass
class CO2InjectionWell(ProcessBase):
    pass


@opgee_dataclass
class CO2Membrane(ProcessBase):
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"
    press_drop_across_membrane: float = 150.0


@opgee_dataclass
class CO2ReinjectionCompressor(ProcessBase):
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"


@opgee_dataclass
class CrudeOilDewatering(ProcessBase):
    temperature_heater_treater: float = 165.0
    heat_loss: float = 2.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"
    eta_gas: float = 0.8
    eta_electricity: float = 0.0004
    heater_treater: int = 0


@opgee_dataclass
class CrudeOilStabilization(ProcessBase):
    stabilizer_column_temp: float = 344.0
    stabilizer_column_press: float = 100.0
    eps_stab: float = 2.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"
    eta_gas: float = 0.8
    eta_electricity: float = 0.0004
    eta_compressor: float = 75.0


@opgee_dataclass
class CrudeOilStorage(ProcessBase):
    f_FG_CS_VRU: float = 90.0
    f_FG_CS_FL: float = 10.0


@opgee_dataclass
class CrudeOilTransport(ProcessBase):
    pass


@opgee_dataclass
class Demethanizer(ProcessBase):
    feed_press_demethanizer: float = 600.0
    column_pressure: float = 240.0
    methane_to_LPG_ratio: float = 0.03
    eta_reboiler_demethanizer: float = 1.25
    air_cooler_delta_T: float = 40.0
    air_cooler_fan_eff: float = 70.0
    air_cooler_press_drop: float = 0.6
    air_cooler_speed_reducer_eff: float = 92.0
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"


@opgee_dataclass
class DownholePump(ProcessBase):
    eta_pump_well: float = 65.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"


@opgee_dataclass
class Drilling(ProcessBase):
    pass


@opgee_dataclass
class Exploration(ProcessBase):
    pass


@opgee_dataclass
class Flaring(ProcessBase):
    pass


@opgee_dataclass
class GasDehydration(ProcessBase):
    eta_reboiler_dehydrator: float = 1.25
    air_cooler_delta_T: float = 40.0
    air_cooler_press_drop: float = 0.6
    air_cooler_fan_eff: float = 70.0
    air_cooler_speed_reducer_eff: float = 92.0


@opgee_dataclass
class GasDistribution(ProcessBase):
    frac_loss_distribution: float = 0.0016
    frac_loss_meter: float = 0.0
    frac_loss_enduse: float = 0.00475


@opgee_dataclass
class GasGathering(ProcessBase):
    site_fugitive_intercept: float = -1.8618
    site_fugitive_slope: float = -0.59397
    processing_plant_average_site_throughput: float = 126.69245647969
    gathering_site_average_site_throughput: float = 19.3


@opgee_dataclass
class GasLiftingCompressor(ProcessBase):
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"


@opgee_dataclass
class GasPartition(ProcessBase):
    N2_flooding_temp: float = 197.0
    C1_flooding_temp: float = 60.0
    N2_flooding_press: float = 125.0
    C1_flooding_press: float = 600.0
    CO2_flooding_temp: float = 60.0
    CO2_flooding_press: float = 600.0
    CO2_source: Literal["Natural subsurface reservoir", "Anthropogenic"] = "Natural subsurface reservoir"
    impurity_CH4_in_CO2: float = 0.03
    impurity_N2_in_CO2: float = 0.03


@opgee_dataclass
class GasReinjectionCompressor(ProcessBase):
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"
    eta_compressor: float = 75.0
    air_separation_energy_intensity: float = 0.004156716


@opgee_dataclass
class GasReinjectionWell(ProcessBase):
    pass


@opgee_dataclass
class HeavyOilDilution(ProcessBase):
    diluent_API: float = 55.2
    dilbit_API: float = 23.0
    dilution_type: Literal["Diluent", "Dilbit"] | None = None
    diluent_temp: float = 60.0
    diluent_press: float = 14.7
    final_mix_temp: float = 60.0
    final_mix_press: float = 14.7
    before_diluent_temp: float = 60.0
    before_diluent_press: float = 14.7
    fraction_diluent: float = 0.0


@opgee_dataclass
class HeavyOilUpgrading(ProcessBase):
    cogeneration_upgrading: int = 1


@opgee_dataclass
class LNGLiquefaction(ProcessBase):
    compression_refrigeration_load: float = 0.0
    ancillary_loads: float = 0.0
    NG_to_liq_rate: float = 0.0


@opgee_dataclass
class LNGRegasification(ProcessBase):
    energy_intensity_regas: float = 0.03
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"
    efficiency: float = 0.3


@opgee_dataclass
class LNGTransport(ProcessBase):
    pass


@opgee_dataclass
class NGL(ProcessBase):
    pass


@opgee_dataclass
class PetrocokeTransport(ProcessBase):
    pass


@opgee_dataclass
class PostStorageCompressor(ProcessBase):
    discharge_press: float = 2000.0
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"


@opgee_dataclass
class PreMembraneChiller(ProcessBase):
    chiller_outlet_temp: float = 35.0


@opgee_dataclass
class PreMembraneCompressor(ProcessBase):
    discharge_press: float = 500.0
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"


@opgee_dataclass
class Reservoir(ProcessBase):
    pass


@opgee_dataclass
class ReservoirWellInterface(ProcessBase):
    res_thickness: float = 50.0
    res_perm: float = 100.0


@opgee_dataclass
class RyanHolmes(ProcessBase):
    daily_use_engine: float = 2.63


@opgee_dataclass
class Separation(ProcessBase):
    number_stages: int = 2
    pressure_first_stage: float = 500.0
    pressure_second_stage: float = 250.0
    pressure_third_stage: float = 100.0
    water_content_oil_emulsion: float = 14.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"
    pressure_outlet: float = 100.0
    temperature_outlet: float = 90.0
    eta_compressor: float = 75.0


@opgee_dataclass
class SourGasCompressor(ProcessBase):
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = "NG_engine"


@opgee_dataclass
class SourGasInjection(ProcessBase):
    pass


@opgee_dataclass
class SteamGeneration(ProcessBase):
    steam_quality_outlet: float = 0.7
    steam_quality_after_blowdown: float = 0.7
    fraction_blowdown_recycled: float = 0.7
    waste_water_reinjection_temp: float = 150.0
    waste_water_reinjection_press: float = 14.67
    friction_loss_stream_distr: float = 1.1
    pressure_loss_choke_wellhead: float = 1.7
    steam_injection_delta_press: float = 100.0
    prod_water_inlet_temp: float = 140.0
    makeup_water_inlet_temp: float = 60.0
    eta_displacement_pump: float = 0.87
    eta_air_blower_OTSG: float = 0.139
    eta_air_blower_HRSG: float = 0.0
    makeup_water_inlet_press: float = 14.7
    eta_air_blower_solar: float = 0.139
    prod_water_inlet_press: float = 200.0


@opgee_dataclass
class StorageCompressor(ProcessBase):
    discharge_press: float = 2000.0
    eta_compressor: float = 75.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"


@opgee_dataclass
class StorageSeparator(ProcessBase):
    outlet_temp: float = 60.0
    outlet_press: float = 400.0
    water_production_frac: float = 0.1


@opgee_dataclass
class StorageWell(ProcessBase):
    pass


@opgee_dataclass
class TransmissionCompressor(ProcessBase):
    press_drop_per_dist: float = 15.67
    transmission_dist: float = 680.0
    transmission_freq: float = 200.0
    transmission_inlet_press: float = 1015.26
    transmission_loss_rate: float = 3.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"
    eta_compressor: float = 75.0
    gas_to_storage_frac: float = 0.0
    transmission_sys_discharge: float = 600.0


@opgee_dataclass
class VFPartition(ProcessBase):
    pass


@opgee_dataclass
class Venting(ProcessBase):
    pass


@opgee_dataclass
class VRUCompressor(ProcessBase):
    discharge_press: float = 500.0
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"
    eta_compressor: float = 75.0


@opgee_dataclass
class WaterInjection(ProcessBase):
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = "NG_engine"
    press_pump: float = 0.0
    eta_pump: float = 65.0


@opgee_dataclass
class WaterTreatment(ProcessBase):
    fraction_disp_water_subsurface: float = 1.0
    fraction_disp_water_surface: float = 0.0
    number_of_stages: int = 4
    makeup_water_treatment_table: int = 1
    makeup_water_temp: float = 60.0
    makeup_water_press: float = 90.0
    steam_quality_at_generator_outlet: float = 0.7
    steam_quality_after_blowdown: float = 0.7


# --- Literal of all process class names ---

ProcessClassName = Literal[
    "AcidGasRemoval",
    "BitumenMining",
    "Boundary",
    "CO2InjectionWell",
    "CO2Membrane",
    "CO2ReinjectionCompressor",
    "CrudeOilDewatering",
    "CrudeOilStabilization",
    "CrudeOilStorage",
    "CrudeOilTransport",
    "Demethanizer",
    "DownholePump",
    "Drilling",
    "Exploration",
    "Flaring",
    "GasDehydration",
    "GasDistribution",
    "GasGathering",
    "GasLiftingCompressor",
    "GasPartition",
    "GasReinjectionCompressor",
    "GasReinjectionWell",
    "HeavyOilDilution",
    "HeavyOilUpgrading",
    "LNGLiquefaction",
    "LNGRegasification",
    "LNGTransport",
    "NGL",
    "PetrocokeTransport",
    "PostStorageCompressor",
    "PreMembraneChiller",
    "PreMembraneCompressor",
    "Reservoir",
    "ReservoirWellInterface",
    "RyanHolmes",
    "Separation",
    "SourGasCompressor",
    "SourGasInjection",
    "SteamGeneration",
    "StorageCompressor",
    "StorageSeparator",
    "StorageWell",
    "TransmissionCompressor",
    "VFPartition",
    "Venting",
    "VRUCompressor",
    "WaterInjection",
    "WaterTreatment",
]

# --- Union of all process types ---

ProcessUnion = Union[
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

# --- Map of class name to class ---

PROCESS_CLASSES: dict[str, type[ProcessBase]] = {
    "AcidGasRemoval": AcidGasRemoval,
    "BitumenMining": BitumenMining,
    "Boundary": Boundary,
    "CO2InjectionWell": CO2InjectionWell,
    "CO2Membrane": CO2Membrane,
    "CO2ReinjectionCompressor": CO2ReinjectionCompressor,
    "CrudeOilDewatering": CrudeOilDewatering,
    "CrudeOilStabilization": CrudeOilStabilization,
    "CrudeOilStorage": CrudeOilStorage,
    "CrudeOilTransport": CrudeOilTransport,
    "Demethanizer": Demethanizer,
    "DownholePump": DownholePump,
    "Drilling": Drilling,
    "Exploration": Exploration,
    "Flaring": Flaring,
    "GasDehydration": GasDehydration,
    "GasDistribution": GasDistribution,
    "GasGathering": GasGathering,
    "GasLiftingCompressor": GasLiftingCompressor,
    "GasPartition": GasPartition,
    "GasReinjectionCompressor": GasReinjectionCompressor,
    "GasReinjectionWell": GasReinjectionWell,
    "HeavyOilDilution": HeavyOilDilution,
    "HeavyOilUpgrading": HeavyOilUpgrading,
    "LNGLiquefaction": LNGLiquefaction,
    "LNGRegasification": LNGRegasification,
    "LNGTransport": LNGTransport,
    "NGL": NGL,
    "PetrocokeTransport": PetrocokeTransport,
    "PostStorageCompressor": PostStorageCompressor,
    "PreMembraneChiller": PreMembraneChiller,
    "PreMembraneCompressor": PreMembraneCompressor,
    "Reservoir": Reservoir,
    "ReservoirWellInterface": ReservoirWellInterface,
    "RyanHolmes": RyanHolmes,
    "Separation": Separation,
    "SourGasCompressor": SourGasCompressor,
    "SourGasInjection": SourGasInjection,
    "SteamGeneration": SteamGeneration,
    "StorageCompressor": StorageCompressor,
    "StorageSeparator": StorageSeparator,
    "StorageWell": StorageWell,
    "TransmissionCompressor": TransmissionCompressor,
    "VFPartition": VFPartition,
    "Venting": Venting,
    "VRUCompressor": VRUCompressor,
    "WaterInjection": WaterInjection,
    "WaterTreatment": WaterTreatment,
}
