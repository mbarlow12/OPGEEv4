"""Field model for XML deserialization."""

from __future__ import annotations
from pydantic_xml.element.element import SearchMode

from typing import Literal

from pydantic_xml import attr, element

from .base import OPGEEBaseModel
from .processes import ProcessUnion
from .stream import StreamModel


class FieldModel(OPGEEBaseModel, tag="Field", search_mode=SearchMode.UNORDERED):
    """Pydantic-xml model for a Field element.

    Contains ~150 field-level attribute elements, process elements, and stream
    elements. Smart-defaulted attrs use default=None so model_fields_set
    tracks which values were explicitly provided in XML.
    """

    name: str = attr()
    enabled: bool | None = attr(default=None)
    group: str | None = attr(default=None)

    # --- Production methods ---
    downhole_pump: int = element(tag="downhole_pump", default=1)
    water_reinjection: int = element(tag="water_reinjection", default=1)
    natural_gas_reinjection: int = element(tag="natural_gas_reinjection", default=1)
    gas_lifting: int = element(tag="gas_lifting", default=0)
    water_flooding: int = element(tag="water_flooding", default=0)
    gas_flooding: int = element(tag="gas_flooding", default=0)
    steam_flooding: int = element(tag="steam_flooding", default=0)
    oil_sands_mine: (
        Literal[
            "None",
            "Integrated with upgrader",
            "Integrated with diluent",
            "Integrated with both",
        ]
        | None
    ) = element(tag="oil_sands_mine", default=None)

    # Synchronized test attrs
    sync_attr_1: int = element(tag="sync_attr_1", default=0)
    sync_attr_2: int = element(tag="sync_attr_2", default=0)

    # --- Field properties ---
    country: str = element(tag="country", default="Generic")
    age: float = element(tag="age", default=38.0)
    depth: float | None = element(tag="depth", default=None)  # smart default
    oil_prod: float = element(tag="oil_prod", default=2098.0)
    num_prod_wells: int | None = element(
        tag="num_prod_wells", default=None
    )  # smart default
    num_water_inj_wells: int | None = element(
        tag="num_water_inj_wells", default=None
    )  # smart default
    num_gas_inj_wells: int | None = element(
        tag="num_gas_inj_wells", default=None
    )  # smart default
    well_diam: float = element(tag="well_diam", default=2.78)
    prod_index: float = element(tag="prod_index", default=17.0)
    res_press: float | None = element(tag="res_press", default=None)  # smart default
    res_temp: float | None = element(tag="res_temp", default=None)  # smart default
    wellhead_temperature: float = element(tag="wellhead_temperature", default=150.0)
    wellhead_pressure: float = element(tag="wellhead_pressure", default=500.0)
    offshore: int = element(tag="offshore", default=0)

    # --- Fluid properties ---
    API: float = element(tag="API", default=32.8)
    total_dissolved_solids: float = element(
        tag="total_dissolved_solids", default=5000.0
    )
    gas_comp_N2: float = element(tag="gas_comp_N2", default=2.86)
    gas_comp_CO2: float = element(tag="gas_comp_CO2", default=0.33)
    gas_comp_C1: float = element(tag="gas_comp_C1", default=89.18)
    gas_comp_C2: float = element(tag="gas_comp_C2", default=5.3)
    gas_comp_C3: float = element(tag="gas_comp_C3", default=1.62)
    gas_comp_C4: float = element(tag="gas_comp_C4", default=0.71)
    gas_comp_H2S: float = element(tag="gas_comp_H2S", default=0.0)

    # --- Production practices ---
    GOR: float | None = element(tag="GOR", default=None)  # smart default
    WOR: float | None = element(tag="WOR", default=None)  # smart default
    WIR: float | None = element(tag="WIR", default=None)  # smart default
    GLIR: float = element(tag="GLIR", default=364.0)
    GFIR: float | None = element(tag="GFIR", default=None)  # smart default
    SOR: float | None = element(tag="SOR", default=None)  # smart default
    liquids_unloading: Literal["Plunger", "No plunger", "None"] | None = element(
        tag="liquids_unloading", default=None
    )
    perc_sequestration_credit: float = element(
        tag="perc_sequestration_credit", default=0.0
    )
    fraction_elec_onsite: float | None = element(
        tag="fraction_elec_onsite", default=None
    )  # smart default
    fraction_remaining_gas_inj: float | None = element(
        tag="fraction_remaining_gas_inj", default=None
    )  # smart default
    fraction_water_reinjected: float = element(
        tag="fraction_water_reinjected", default=1.0
    )
    fraction_steam_cogen: float = element(tag="fraction_steam_cogen", default=0.0)
    fraction_steam_solar: float = element(tag="fraction_steam_solar", default=0.0)
    gas_pressure_after_boosting: float = element(
        tag="gas_pressure_after_boosting", default=500.0
    )
    friction_factor: float = element(tag="friction_factor", default=0.02)
    AGR_feedin_press: float = element(tag="AGR_feedin_press", default=500.0)
    has_grid_mix: int = element(tag="has_grid_mix", default=0)

    # --- Processing practices ---
    upgrader_type: (
        Literal["None", "Delayed coking", "Hydroconversion", "Combined"] | None
    ) = element(tag="upgrader_type", default=None)
    gas_processing_path: (
        Literal[
            "None",
            "Minimal",
            "Acid Gas",
            "Wet Gas",
            "Acid Wet Gas",
            "Sour Gas Reinjection",
            "CO2-EOR Membrane",
            "CO2-EOR Ryan Holmes",
        ]
        | None
    ) = element(tag="gas_processing_path", default=None)
    common_gas_process_choice: Literal["None", "All"] | None = element(
        tag="common_gas_process_choice", default=None
    )  # smart default
    FOR: float = element(tag="FOR", default=141.3)
    frac_venting: float = element(tag="frac_venting", default=0.002)
    oil_processing_path: (
        Literal[
            "Stabilization",
            "Storage",
            "Upgrading",
            "Dilution",
            "Dilution and Upgrading",
        ]
        | None
    ) = element(tag="oil_processing_path", default=None)
    temperature_mined_bitumen: float = element(
        tag="temperature_mined_bitumen", default=80.0
    )
    pressure_mined_bitumen: float = element(tag="pressure_mined_bitumen", default=14.7)
    stabilizer_column: int | None = element(
        tag="stabilizer_column", default=None
    )  # smart default

    # --- Transportation ---
    frac_transport_tanker: float = element(tag="frac_transport_tanker", default=1.0)
    frac_transport_barge: float = element(tag="frac_transport_barge", default=0.0)
    frac_transport_pipeline: float = element(tag="frac_transport_pipeline", default=1.0)
    frac_transport_rail: float = element(tag="frac_transport_rail", default=0.0)
    frac_transport_truck: float = element(tag="frac_transport_truck", default=0.0)
    transport_dist_tanker: float = element(tag="transport_dist_tanker", default=5082.0)
    transport_dist_barge: float = element(tag="transport_dist_barge", default=500.0)
    transport_dist_pipeline: float = element(
        tag="transport_dist_pipeline", default=750.0
    )
    transport_dist_rail: float = element(tag="transport_dist_rail", default=800.0)
    transport_dist_truck: float = element(tag="transport_dist_truck", default=100.0)
    ocean_tanker_size: float = element(tag="ocean_tanker_size", default=250000.0)

    # --- Land use ---
    ecosystem_richness: Literal["Low carbon", "Med carbon", "High carbon"] | None = (
        element(tag="ecosystem_richness", default=None)
    )  # smart default
    field_development_intensity: Literal["Low", "Med", "High"] | None = element(
        tag="field_development_intensity", default=None
    )  # smart default

    # --- Exploration/Drilling ---
    number_wells_dry: int = element(tag="number_wells_dry", default=1)
    number_wells_exploratory: int = element(tag="number_wells_exploratory", default=3)
    weight_land_survey: float = element(tag="weight_land_survey", default=25.0)
    weight_ocean_survey: float = element(tag="weight_ocean_survey", default=100.0)
    distance_survey: float = element(tag="distance_survey", default=10000.0)
    eta_rig: Literal["Low", "Med", "High"] | None = element(tag="eta_rig", default=None)
    well_complexity: Literal["Simple", "Moderate", "Complex"] | None = element(
        tag="well_complexity", default=None
    )
    well_size: Literal["Small", "Med", "Large", "Extra Large"] | None = element(
        tag="well_size", default=None
    )
    fraction_wells_horizontal: float = element(
        tag="fraction_wells_horizontal", default=0.0
    )
    length_lateral: float = element(tag="length_lateral", default=5000.0)
    well_productivity_crude_oil: Literal["Low", "Medium", "High"] | None = element(
        tag="well_productivity_crude_oil", default=None
    )
    well_productivity_natural_gas: Literal["Low", "Medium", "High"] | None = element(
        tag="well_productivity_natural_gas", default=None
    )
    fraction_wells_fractured: float = element(
        tag="fraction_wells_fractured", default=0.0
    )
    volume_per_well_fractured: float = element(
        tag="volume_per_well_fractured", default=3.0
    )
    pressure_gradient_fracturing: float = element(
        tag="pressure_gradient_fracturing", default=0.7
    )
    timeframe_land_use: str = element(tag="timeframe_land_use", default="30")
    flaring_fracturing_flowback: int = element(
        tag="flaring_fracturing_flowback", default=0
    )
    REC_fracturing_flowback: int = element(tag="REC_fracturing_flowback", default=1)
    number_well_workovers: float = element(tag="number_well_workovers", default=4.0)
    field_production_lifetime: float = element(
        tag="field_production_lifetime", default=30.0
    )

    # --- Steam generation ---
    steam_quality_outlet: float = element(tag="steam_quality_outlet", default=0.7)
    steam_quality_after_blowdown: float = element(
        tag="steam_quality_after_blowdown", default=0.7
    )
    fraction_blowdown_recycled: float = element(
        tag="fraction_blowdown_recycled", default=0.7
    )
    waste_water_reinjection_temp: float = element(
        tag="waste_water_reinjection_temp", default=150.0
    )
    waste_water_reinjection_press: float = element(
        tag="waste_water_reinjection_press", default=14.67
    )
    friction_loss_steam_distr: float = element(
        tag="friction_loss_steam_distr", default=1.1
    )
    pressure_loss_choke_wellhead: float = element(
        tag="pressure_loss_choke_wellhead", default=1.7
    )
    steam_injection_delta_press: float = element(
        tag="steam_injection_delta_press", default=100.0
    )
    prod_water_inlet_temp: float | None = element(
        tag="prod_water_inlet_temp", default=None
    )  # smart default
    makeup_water_inlet_temp: float = element(
        tag="makeup_water_inlet_temp", default=60.0
    )
    eta_displacement_pump: float = element(tag="eta_displacement_pump", default=0.87)
    eta_air_blower_OTSG: float = element(tag="eta_air_blower_OTSG", default=0.139)
    eta_air_blower_HRSG: float = element(tag="eta_air_blower_HRSG", default=0.0)
    makeup_water_inlet_press: float = element(
        tag="makeup_water_inlet_press", default=14.7
    )
    eta_air_blower_solar: float = element(tag="eta_air_blower_solar", default=0.139)
    prod_water_inlet_press: float = element(tag="prod_water_inlet_press", default=200.0)
    NG_fuel_share_OTSG_produced: float = element(
        tag="NG_fuel_share_OTSG_produced", default=0.0
    )
    NG_fuel_share_HRSG_produced: float = element(
        tag="NG_fuel_share_HRSG_produced", default=0.0
    )
    waste_water_temp: float = element(tag="waste_water_temp", default=150.0)
    O2_excess_OTSG: float = element(tag="O2_excess_OTSG", default=1.2)
    temperature_inlet_air_OTSG: float = element(
        tag="temperature_inlet_air_OTSG", default=80.33
    )
    OTSG_exhaust_temp_outlet_before_economizer: float = element(
        tag="OTSG_exhaust_temp_outlet_before_economizer", default=350.0
    )
    OTSG_exhaust_temp_outlet: float = element(
        tag="OTSG_exhaust_temp_outlet", default=350.0
    )
    OTSG_exhaust_temp_outlet_before_preheater: float = element(
        tag="OTSG_exhaust_temp_outlet_before_preheater", default=350.0
    )
    loss_shell_OTSG: float = element(tag="loss_shell_OTSG", default=0.02)
    loss_shell_HRSG: float = element(tag="loss_shell_HRSG", default=0.02)
    loss_gaseous_OTSG: float = element(tag="loss_gaseous_OTSG", default=11.02)
    loss_liquid_OTSG: float = element(tag="loss_liquid_OTSG", default=250.0)
    blowdown_heat_recovery: int = element(tag="blowdown_heat_recovery", default=1)
    eta_blowdown_heat_rec_OTSG: float = element(
        tag="eta_blowdown_heat_rec_OTSG", default=0.95
    )
    eta_blowdown_heat_rec_HRSG: float = element(
        tag="eta_blowdown_heat_rec_HRSG", default=0.95
    )
    economizer_OTSG: int = element(tag="economizer_OTSG", default=0)
    preheater_OTSG: int = element(tag="preheater_OTSG", default=0)
    economizer_HRSG: int = element(tag="economizer_HRSG", default=0)
    preheater_HRSG: int = element(tag="preheater_HRSG", default=0)
    eta_economizer_heat_rec_OTSG: float = element(
        tag="eta_economizer_heat_rec_OTSG", default=0.95
    )
    eta_preheater_heat_rec_OTSG: float = element(
        tag="eta_preheater_heat_rec_OTSG", default=0.9
    )
    eta_economizer_heat_rec_HRSG: float = element(
        tag="eta_economizer_heat_rec_HRSG", default=0.95
    )
    eta_preheater_heat_rec_HRSG: float = element(
        tag="eta_preheater_heat_rec_HRSG", default=0.9
    )
    OTSG_frac_import_gas: float = element(tag="OTSG_frac_import_gas", default=1.0)
    OTSG_frac_prod_gas: float = element(tag="OTSG_frac_prod_gas", default=0.0)
    HRSG_frac_import_gas: float = element(tag="HRSG_frac_import_gas", default=1.0)
    HRSG_frac_prod_gas: float = element(tag="HRSG_frac_prod_gas", default=0.0)
    duct_firing: int = element(tag="duct_firing", default=0)
    duct_firing_inlet_temp: float = element(
        tag="duct_firing_inlet_temp", default=1300.0
    )
    HRSG_exhaust_temp_outlet_before_economizer: float = element(
        tag="HRSG_exhaust_temp_outlet_before_economizer", default=350.0
    )
    HRSG_exhaust_temp_outlet: float = element(
        tag="HRSG_exhaust_temp_outlet", default=350.0
    )
    HRSG_exhaust_temp_outlet_before_preheater: float = element(
        tag="HRSG_exhaust_temp_outlet_before_preheater", default=350.0
    )

    # --- Other ---
    flood_gas_type: Literal["NG", "N2", "CO2"] | None = element(
        tag="flood_gas_type", default=None
    )
    fuel_input_type_OTSG: Literal["Gas", "Oil"] | None = element(
        tag="fuel_input_type_OTSG", default=None
    )
    gas_turbine_type: Literal["A", "B", "C", "D"] | None = element(
        tag="gas_turbine_type", default=None
    )
    combusted_gas_frac: float = element(tag="combusted_gas_frac", default=93.0)
    surface_piping_leakage: float = element(tag="surface_piping_leakage", default=0.0)
    reflux_ratio: float = element(tag="reflux_ratio", default=2.25)
    regeneration_feed_temp: float = element(tag="regeneration_feed_temp", default=200.0)
    natural_gas_to_liquefaction_frac: float = element(
        tag="natural_gas_to_liquefaction_frac", default=0.5
    )
    frac_CO2_breakthrough: float = element(tag="frac_CO2_breakthrough", default=0.59)
    GOR_cutoff: float = element(tag="GOR_cutoff", default=100.0)
    frac_wells_with_plunger: float = element(
        tag="frac_wells_with_plunger", default=0.10029988
    )
    frac_wells_with_non_plunger: float = element(
        tag="frac_wells_with_non_plunger", default=0.068996621
    )
    workovers_per_well: float = element(tag="workovers_per_well", default=4.0)
    is_flaring: str = element(tag="is_flaring", default="No")
    is_REC: str = element(tag="is_REC", default="Yes")
    frac_well_fractured: float = element(tag="frac_well_fractured", default=0.0)

    # --- Processes and streams ---
    processes: list[ProcessUnion] = []
    streams: list[StreamModel] = element(tag="Stream", default=[])
