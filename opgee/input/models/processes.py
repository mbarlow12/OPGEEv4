"""Process models for XML deserialization.

Each Process subclass has its own pydantic-xml model with tag=ClassName.
ProcessUnion at the bottom is the discriminated union of all 51 types.
"""
from __future__ import annotations

from typing import Literal, Union

from pydantic_xml import attr, element

from .base import OPGEEBaseModel


# --- Process base attributes (shared by all processes) ---

class _ProcessBase(OPGEEBaseModel):
    """Common XML attributes for process elements."""
    enabled: bool | None = attr(default=None)
    boundary: str | None = attr(default=None)
    after: bool | None = attr(default=None)
    impute_start: bool | None = attr(name="impute-start", default=None)
    cycle_start: bool | None = attr(name="cycle-start", default=None)
    # Process-level attrs shared across all subclasses
    leak_rate: float = element(tag="leak_rate", default=0.0)


# --- Process models (alphabetical by class name) ---

class AcidGasRemoval(_ProcessBase, tag="AcidGasRemoval"):
    eta_reboiler: float = element(tag="eta_reboiler", default=1.25)
    air_cooler_delta_T: float = element(tag="air_cooler_delta_T", default=40.0)
    air_cooler_fan_eff: float = element(tag="air_cooler_fan_eff", default=70.0)
    air_cooler_press_drop: float = element(tag="air_cooler_press_drop", default=0.6)
    air_cooler_speed_reducer_eff: float = element(tag="air_cooler_speed_reducer_eff", default=92.0)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    type_amine: Literal["conv DEA", "high DEA", "MEA", "DGA", "MDEA"] = element(tag="type_amine", default="MDEA")
    ratio_reflux_reboiler: float = element(tag="ratio_reflux_reboiler", default=2.0)
    regeneration_temp: float = element(tag="regeneration_temp", default=205.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")


class BitumenMining(_ProcessBase, tag="BitumenMining"):
    CH4_loss_rate: float = element(tag="CH4_loss_rate", default=22.881511207)


class Boundary(_ProcessBase, tag="Boundary"):
    pass


class CO2InjectionWell(_ProcessBase, tag="CO2InjectionWell"):
    pass


class CO2Membrane(_ProcessBase, tag="CO2Membrane"):
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")
    press_drop_across_membrane: float = element(tag="press_drop_across_membrane", default=150.0)


class CO2ReinjectionCompressor(_ProcessBase, tag="CO2ReinjectionCompressor"):
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")


class CrudeOilDewatering(_ProcessBase, tag="CrudeOilDewatering"):
    temperature_heater_treater: float = element(tag="temperature_heater_treater", default=165.0)
    heat_loss: float = element(tag="heat_loss", default=2.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")
    eta_gas: float = element(tag="eta_gas", default=0.8)
    eta_electricity: float = element(tag="eta_electricity", default=0.0004)
    heater_treater: int = element(tag="heater_treater", default=0)


class CrudeOilStabilization(_ProcessBase, tag="CrudeOilStabilization"):
    stabilizer_column_temp: float = element(tag="stabilizer_column_temp", default=344.0)
    stabilizer_column_press: float = element(tag="stabilizer_column_press", default=100.0)
    eps_stab: float = element(tag="eps_stab", default=2.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")
    eta_gas: float = element(tag="eta_gas", default=0.8)
    eta_electricity: float = element(tag="eta_electricity", default=0.0004)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)


class CrudeOilStorage(_ProcessBase, tag="CrudeOilStorage"):
    f_FG_CS_VRU: float = element(tag="f_FG_CS_VRU", default=90.0)
    f_FG_CS_FL: float = element(tag="f_FG_CS_FL", default=10.0)


class CrudeOilTransport(_ProcessBase, tag="CrudeOilTransport"):
    pass


class Demethanizer(_ProcessBase, tag="Demethanizer"):
    feed_press_demethanizer: float = element(tag="feed_press_demethanizer", default=600.0)
    column_pressure: float = element(tag="column_pressure", default=240.0)
    methane_to_LPG_ratio: float = element(tag="methane_to_LPG_ratio", default=0.03)
    eta_reboiler_demethanizer: float = element(tag="eta_reboiler_demethanizer", default=1.25)
    air_cooler_delta_T: float = element(tag="air_cooler_delta_T", default=40.0)
    air_cooler_fan_eff: float = element(tag="air_cooler_fan_eff", default=70.0)
    air_cooler_press_drop: float = element(tag="air_cooler_press_drop", default=0.6)
    air_cooler_speed_reducer_eff: float = element(tag="air_cooler_speed_reducer_eff", default=92.0)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")


class DownholePump(_ProcessBase, tag="DownholePump"):
    eta_pump_well: float = element(tag="eta_pump_well", default=65.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")


class Drilling(_ProcessBase, tag="Drilling"):
    pass


class Exploration(_ProcessBase, tag="Exploration"):
    pass


class Flaring(_ProcessBase, tag="Flaring"):
    pass


class GasDehydration(_ProcessBase, tag="GasDehydration"):
    eta_reboiler_dehydrator: float = element(tag="eta_reboiler_dehydrator", default=1.25)
    air_cooler_delta_T: float = element(tag="air_cooler_delta_T", default=40.0)
    air_cooler_press_drop: float = element(tag="air_cooler_press_drop", default=0.6)
    air_cooler_fan_eff: float = element(tag="air_cooler_fan_eff", default=70.0)
    air_cooler_speed_reducer_eff: float = element(tag="air_cooler_speed_reducer_eff", default=92.0)


class GasDistribution(_ProcessBase, tag="GasDistribution"):
    frac_loss_distribution: float = element(tag="frac_loss_distribution", default=0.0016)
    frac_loss_meter: float = element(tag="frac_loss_meter", default=0.0)
    frac_loss_enduse: float = element(tag="frac_loss_enduse", default=0.00475)


class GasGathering(_ProcessBase, tag="GasGathering"):
    site_fugitive_intercept: float = element(tag="site_fugitive_intercept", default=-1.8618)
    site_fugitive_slope: float = element(tag="site_fugitive_slope", default=-0.59397)
    processing_plant_average_site_throughput: float = element(tag="processing_plant_average_site_throughput", default=126.69245647969)
    gathering_site_average_site_throughput: float = element(tag="gathering_site_average_site_throughput", default=19.3)


class GasLiftingCompressor(_ProcessBase, tag="GasLiftingCompressor"):
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")


class GasPartition(_ProcessBase, tag="GasPartition"):
    N2_flooding_temp: float = element(tag="N2_flooding_temp", default=197.0)
    C1_flooding_temp: float = element(tag="C1_flooding_temp", default=60.0)
    N2_flooding_press: float = element(tag="N2_flooding_press", default=125.0)
    C1_flooding_press: float = element(tag="C1_flooding_press", default=600.0)
    CO2_flooding_temp: float = element(tag="CO2_flooding_temp", default=60.0)
    CO2_flooding_press: float = element(tag="CO2_flooding_press", default=600.0)
    CO2_source: Literal["Natural subsurface reservoir", "Anthropogenic"] = element(tag="CO2_source", default="Natural subsurface reservoir")
    impurity_CH4_in_CO2: float = element(tag="impurity_CH4_in_CO2", default=0.03)
    impurity_N2_in_CO2: float = element(tag="impurity_N2_in_CO2", default=0.03)


class GasReinjectionCompressor(_ProcessBase, tag="GasReinjectionCompressor"):
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    air_separation_energy_intensity: float = element(tag="air_separation_energy_intensity", default=0.004156716)


class GasReinjectionWell(_ProcessBase, tag="GasReinjectionWell"):
    pass


class HeavyOilDilution(_ProcessBase, tag="HeavyOilDilution"):
    diluent_API: float = element(tag="diluent_API", default=55.2)
    dilbit_API: float = element(tag="dilbit_API", default=23.0)
    dilution_type: Literal["Diluent", "Dilbit"] | None = element(tag="dilution_type", default=None)
    diluent_temp: float = element(tag="diluent_temp", default=60.0)
    diluent_press: float = element(tag="diluent_press", default=14.7)
    final_mix_temp: float = element(tag="final_mix_temp", default=60.0)
    final_mix_press: float = element(tag="final_mix_press", default=14.7)
    before_diluent_temp: float = element(tag="before_diluent_temp", default=60.0)
    before_diluent_press: float = element(tag="before_diluent_press", default=14.7)
    fraction_diluent: float = element(tag="fraction_diluent", default=0.0)


class HeavyOilUpgrading(_ProcessBase, tag="HeavyOilUpgrading"):
    cogeneration_upgrading: int = element(tag="cogeneration_upgrading", default=1)


class LNGLiquefaction(_ProcessBase, tag="LNGLiquefaction"):
    compression_refrigeration_load: float = element(tag="compression_refrigeration_load", default=0.0)
    ancillary_loads: float = element(tag="ancillary_loads", default=0.0)
    NG_to_liq_rate: float = element(tag="NG_to_liq_rate", default=0.0)


class LNGRegasification(_ProcessBase, tag="LNGRegasification"):
    energy_intensity_regas: float = element(tag="energy_intensity_regas", default=0.03)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")
    efficiency: float = element(tag="efficiency", default=0.3)


class LNGTransport(_ProcessBase, tag="LNGTransport"):
    pass


class NGL(_ProcessBase, tag="NGL"):
    pass


class PetrocokeTransport(_ProcessBase, tag="PetrocokeTransport"):
    pass


class PostStorageCompressor(_ProcessBase, tag="PostStorageCompressor"):
    discharge_press: float = element(tag="discharge_press", default=2000.0)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")


class PreMembraneChiller(_ProcessBase, tag="PreMembraneChiller"):
    chiller_outlet_temp: float = element(tag="chiller_outlet_temp", default=35.0)


class PreMembraneCompressor(_ProcessBase, tag="PreMembraneCompressor"):
    discharge_press: float = element(tag="discharge_press", default=500.0)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")


class Reservoir(_ProcessBase, tag="Reservoir"):
    pass


class ReservoirWellInterface(_ProcessBase, tag="ReservoirWellInterface"):
    res_thickness: float = element(tag="res_thickness", default=50.0)
    res_perm: float = element(tag="res_perm", default=100.0)


class RyanHolmes(_ProcessBase, tag="RyanHolmes"):
    daily_use_engine: float = element(tag="daily_use_engine", default=2.63)


class Separation(_ProcessBase, tag="Separation"):
    number_stages: int = element(tag="number_stages", default=2)
    pressure_first_stage: float = element(tag="pressure_first_stage", default=500.0)
    pressure_second_stage: float = element(tag="pressure_second_stage", default=250.0)
    pressure_third_stage: float = element(tag="pressure_third_stage", default=100.0)
    water_content_oil_emulsion: float = element(tag="water_content_oil_emulsion", default=14.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")
    pressure_outlet: float = element(tag="pressure_outlet", default=100.0)
    temperature_outlet: float = element(tag="temperature_outlet", default=90.0)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)


class SourGasCompressor(_ProcessBase, tag="SourGasCompressor"):
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor"] = element(tag="prime_mover_type", default="NG_engine")


class SourGasInjection(_ProcessBase, tag="SourGasInjection"):
    pass


class SteamGeneration(_ProcessBase, tag="SteamGeneration"):
    steam_quality_outlet: float = element(tag="steam_quality_outlet", default=0.7)
    steam_quality_after_blowdown: float = element(tag="steam_quality_after_blowdown", default=0.7)
    fraction_blowdown_recycled: float = element(tag="fraction_blowdown_recycled", default=0.7)
    waste_water_reinjection_temp: float = element(tag="waste_water_reinjection_temp", default=150.0)
    waste_water_reinjection_press: float = element(tag="waste_water_reinjection_press", default=14.67)
    friction_loss_stream_distr: float = element(tag="friction_loss_stream_distr", default=1.1)
    pressure_loss_choke_wellhead: float = element(tag="pressure_loss_choke_wellhead", default=1.7)
    steam_injection_delta_press: float = element(tag="steam_injection_delta_press", default=100.0)
    prod_water_inlet_temp: float = element(tag="prod_water_inlet_temp", default=140.0)
    makeup_water_inlet_temp: float = element(tag="makeup_water_inlet_temp", default=60.0)
    eta_displacement_pump: float = element(tag="eta_displacement_pump", default=0.87)
    eta_air_blower_OTSG: float = element(tag="eta_air_blower_OTSG", default=0.139)
    eta_air_blower_HRSG: float = element(tag="eta_air_blower_HRSG", default=0.0)
    makeup_water_inlet_press: float = element(tag="makeup_water_inlet_press", default=14.7)
    eta_air_blower_solar: float = element(tag="eta_air_blower_solar", default=0.139)
    prod_water_inlet_press: float = element(tag="prod_water_inlet_press", default=200.0)


class StorageCompressor(_ProcessBase, tag="StorageCompressor"):
    discharge_press: float = element(tag="discharge_press", default=2000.0)
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")


class StorageSeparator(_ProcessBase, tag="StorageSeparator"):
    outlet_temp: float = element(tag="outlet_temp", default=60.0)
    outlet_press: float = element(tag="outlet_press", default=400.0)
    water_production_frac: float = element(tag="water_production_frac", default=0.1)


class StorageWell(_ProcessBase, tag="StorageWell"):
    pass


class TransmissionCompressor(_ProcessBase, tag="TransmissionCompressor"):
    press_drop_per_dist: float = element(tag="press_drop_per_dist", default=15.67)
    transmission_dist: float = element(tag="transmission_dist", default=680.0)
    transmission_freq: float = element(tag="transmission_freq", default=200.0)
    transmission_inlet_press: float = element(tag="transmission_inlet_press", default=1015.26)
    transmission_loss_rate: float = element(tag="transmission_loss_rate", default=3.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")
    eta_compressor: float = element(tag="eta_compressor", default=75.0)
    gas_to_storage_frac: float = element(tag="gas_to_storage_frac", default=0.0)
    transmission_sys_discharge: float = element(tag="transmission_sys_discharge", default=600.0)


class VFPartition(_ProcessBase, tag="VFPartition"):
    pass


class Venting(_ProcessBase, tag="Venting"):
    pass


class VRUCompressor(_ProcessBase, tag="VRUCompressor"):
    discharge_press: float = element(tag="discharge_press", default=500.0)
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")
    eta_compressor: float = element(tag="eta_compressor", default=75.0)


class WaterInjection(_ProcessBase, tag="WaterInjection"):
    prime_mover_type: Literal["NG_engine", "Electric_motor", "Diesel_engine", "NG_turbine"] = element(tag="prime_mover_type", default="NG_engine")
    press_pump: float = element(tag="press_pump", default=0.0)
    eta_pump: float = element(tag="eta_pump", default=65.0)


class WaterTreatment(_ProcessBase, tag="WaterTreatment"):
    fraction_disp_water_subsurface: float = element(tag="fraction_disp_water_subsurface", default=1.0)
    fraction_disp_water_surface: float = element(tag="fraction_disp_water_surface", default=0.0)
    number_of_stages: int = element(tag="number_of_stages", default=4)
    makeup_water_treatment_table: int = element(tag="makeup_water_treatment_table", default=1)
    makeup_water_temp: float = element(tag="makeup_water_temp", default=60.0)
    makeup_water_press: float = element(tag="makeup_water_press", default=90.0)
    steam_quality_at_generator_outlet: float = element(tag="steam_quality_at_generator_outlet", default=0.7)
    steam_quality_after_blowdown: float = element(tag="steam_quality_after_blowdown", default=0.7)


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
