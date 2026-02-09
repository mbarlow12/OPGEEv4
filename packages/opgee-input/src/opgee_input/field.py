"""Field input dataclass."""
from __future__ import annotations

from dataclasses import field as dc_field
from typing import Literal

from .base import OPGEEInput, opgee_dataclass
from .processes import ProcessUnion
from .stream import StreamInput


@opgee_dataclass
class FieldInput(OPGEEInput):
    """Input specification for a Field element.

    Contains ~145 field-level attributes, process elements, and stream
    elements. Smart-defaulted attrs use default=None so model_fields_set
    tracks which values were explicitly provided.

    Excludes XML-routing-only attrs: oil_sands_mine, upgrader_type,
    gas_processing_path, oil_processing_path, common_gas_process_choice, group.
    """

    name: str
    enabled: bool | None = None

    # --- Production methods ---
    downhole_pump: int = 1
    water_reinjection: int = 1
    natural_gas_reinjection: int = 1
    gas_lifting: int = 0
    water_flooding: int = 0
    gas_flooding: int = 0
    steam_flooding: int = 0

    # Synchronized test attrs
    sync_attr_1: int = 0
    sync_attr_2: int = 0

    # --- Field properties ---
    country: str = "Generic"
    age: float = 38.0
    depth: float | None = None  # smart default
    oil_prod: float = 2098.0
    num_prod_wells: int | None = None  # smart default
    num_water_inj_wells: int | None = None  # smart default
    num_gas_inj_wells: int | None = None  # smart default
    well_diam: float = 2.78
    prod_index: float = 17.0
    res_press: float | None = None  # smart default
    res_temp: float | None = None  # smart default
    wellhead_temperature: float = 150.0
    wellhead_pressure: float = 500.0
    offshore: int = 0

    # --- Fluid properties ---
    API: float = 32.8
    total_dissolved_solids: float = 5000.0
    gas_comp_N2: float = 2.86
    gas_comp_CO2: float = 0.33
    gas_comp_C1: float = 89.18
    gas_comp_C2: float = 5.3
    gas_comp_C3: float = 1.62
    gas_comp_C4: float = 0.71
    gas_comp_H2S: float = 0.0

    # --- Production practices ---
    GOR: float | None = None  # smart default
    WOR: float | None = None  # smart default
    WIR: float | None = None  # smart default
    GLIR: float = 364.0
    GFIR: float | None = None  # smart default
    SOR: float | None = None  # smart default
    liquids_unloading: Literal["Plunger", "No plunger", "None"] | None = None
    perc_sequestration_credit: float = 0.0
    fraction_elec_onsite: float | None = None  # smart default
    fraction_remaining_gas_inj: float | None = None  # smart default
    fraction_water_reinjected: float = 1.0
    fraction_steam_cogen: float = 0.0
    fraction_steam_solar: float = 0.0
    gas_pressure_after_boosting: float = 500.0
    friction_factor: float = 0.02
    AGR_feedin_press: float = 500.0
    has_grid_mix: int = 0

    # --- Processing practices ---
    FOR: float = 141.3
    frac_venting: float = 0.002
    temperature_mined_bitumen: float = 80.0
    pressure_mined_bitumen: float = 14.7
    stabilizer_column: int | None = None  # smart default

    # --- Transportation ---
    frac_transport_tanker: float = 1.0
    frac_transport_barge: float = 0.0
    frac_transport_pipeline: float = 1.0
    frac_transport_rail: float = 0.0
    frac_transport_truck: float = 0.0
    transport_dist_tanker: float = 5082.0
    transport_dist_barge: float = 500.0
    transport_dist_pipeline: float = 750.0
    transport_dist_rail: float = 800.0
    transport_dist_truck: float = 100.0
    ocean_tanker_size: float = 250000.0

    # --- Land use ---
    ecosystem_richness: Literal["Low carbon", "Med carbon", "High carbon"] | None = None  # smart default
    field_development_intensity: Literal["Low", "Med", "High"] | None = None  # smart default

    # --- Exploration/Drilling ---
    number_wells_dry: int = 1
    number_wells_exploratory: int = 3
    weight_land_survey: float = 25.0
    weight_ocean_survey: float = 100.0
    distance_survey: float = 10000.0
    eta_rig: Literal["Low", "Med", "High"] | None = None
    well_complexity: Literal["Simple", "Moderate", "Complex"] | None = None
    well_size: Literal["Small", "Med", "Large", "Extra Large"] | None = None
    fraction_wells_horizontal: float = 0.0
    length_lateral: float = 5000.0
    well_productivity_crude_oil: Literal["Low", "Medium", "High"] | None = None
    well_productivity_natural_gas: Literal["Low", "Medium", "High"] | None = None
    fraction_wells_fractured: float = 0.0
    volume_per_well_fractured: float = 3.0
    pressure_gradient_fracturing: float = 0.7
    timeframe_land_use: str = "30"
    flaring_fracturing_flowback: int = 0
    REC_fracturing_flowback: int = 1
    number_well_workovers: float = 4.0
    field_production_lifetime: float = 30.0

    # --- Steam generation ---
    steam_quality_outlet: float = 0.7
    steam_quality_after_blowdown: float = 0.7
    fraction_blowdown_recycled: float = 0.7
    waste_water_reinjection_temp: float = 150.0
    waste_water_reinjection_press: float = 14.67
    friction_loss_steam_distr: float = 1.1
    pressure_loss_choke_wellhead: float = 1.7
    steam_injection_delta_press: float = 100.0
    prod_water_inlet_temp: float | None = None  # smart default
    makeup_water_inlet_temp: float = 60.0
    eta_displacement_pump: float = 0.87
    eta_air_blower_OTSG: float = 0.139
    eta_air_blower_HRSG: float = 0.0
    makeup_water_inlet_press: float = 14.7
    eta_air_blower_solar: float = 0.139
    prod_water_inlet_press: float = 200.0
    NG_fuel_share_OTSG_produced: float = 0.0
    NG_fuel_share_HRSG_produced: float = 0.0
    waste_water_temp: float = 150.0
    O2_excess_OTSG: float = 1.2
    temperature_inlet_air_OTSG: float = 80.33
    OTSG_exhaust_temp_outlet_before_economizer: float = 350.0
    OTSG_exhaust_temp_outlet: float = 350.0
    OTSG_exhaust_temp_outlet_before_preheater: float = 350.0
    loss_shell_OTSG: float = 0.02
    loss_shell_HRSG: float = 0.02
    loss_gaseous_OTSG: float = 11.02
    loss_liquid_OTSG: float = 250.0
    blowdown_heat_recovery: int = 1
    eta_blowdown_heat_rec_OTSG: float = 0.95
    eta_blowdown_heat_rec_HRSG: float = 0.95
    economizer_OTSG: int = 0
    preheater_OTSG: int = 0
    economizer_HRSG: int = 0
    preheater_HRSG: int = 0
    eta_economizer_heat_rec_OTSG: float = 0.95
    eta_preheater_heat_rec_OTSG: float = 0.9
    eta_economizer_heat_rec_HRSG: float = 0.95
    eta_preheater_heat_rec_HRSG: float = 0.9
    OTSG_frac_import_gas: float = 1.0
    OTSG_frac_prod_gas: float = 0.0
    HRSG_frac_import_gas: float = 1.0
    HRSG_frac_prod_gas: float = 0.0
    duct_firing: int = 0
    duct_firing_inlet_temp: float = 1300.0
    HRSG_exhaust_temp_outlet_before_economizer: float = 350.0
    HRSG_exhaust_temp_outlet: float = 350.0
    HRSG_exhaust_temp_outlet_before_preheater: float = 350.0

    # --- Other ---
    flood_gas_type: Literal["NG", "N2", "CO2"] | None = None
    fuel_input_type_OTSG: Literal["Gas", "Oil"] | None = None
    gas_turbine_type: Literal["A", "B", "C", "D"] | None = None
    combusted_gas_frac: float = 93.0
    surface_piping_leakage: float = 0.0
    reflux_ratio: float = 2.25
    regeneration_feed_temp: float = 200.0
    natural_gas_to_liquefaction_frac: float = 0.5
    frac_CO2_breakthrough: float = 0.59
    GOR_cutoff: float = 100.0
    frac_wells_with_plunger: float = 0.10029988
    frac_wells_with_non_plunger: float = 0.068996621
    workovers_per_well: float = 4.0
    is_flaring: str = "No"
    is_REC: str = "Yes"
    frac_well_fractured: float = 0.0

    # --- Processes and streams ---
    processes: list[ProcessUnion] = dc_field(default_factory=list)
    streams: list[StreamInput] = dc_field(default_factory=list)
