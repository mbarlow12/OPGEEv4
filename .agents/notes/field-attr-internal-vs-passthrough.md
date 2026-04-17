# Field Attribute Classification: Internal vs. Pass-Through

**Date**: 2026-04-16
**Source**: Trace of field.py cache_attributes(), attributes.xml, and all process consumers

---

## Headline: 85.5% of cached Field attributes are pure pass-through

Of the 69 attributes in `cache_attributes()`, only **7** are used by Field's own logic. The other **59** exist on Field solely so processes can read `field.<attr>`.

---

## INTERNAL-only (used by Field, not by processes): 1 attribute

| Cached Name | Field Method | Line |
|---|---|---|
| `has_grid_mix` | `get_imported_emissions()` | 757 |

---

## BOTH (used by Field AND by processes): 6 attributes

| Cached Name | Field Method | Process Consumers |
|---|---|---|
| `field_production_lifetime` | `get_completion_and_workover_C1_rate()` | exploration |
| `num_prod_wells` | `get_completion_and_workover_C1_rate()` | reservoir_well_interface, downhole_pump, exploration |
| `oil_sands_mine` | `get_completion_and_workover_C1_rate()` | 7 processes |
| `res_press` | Computes `wellhead_p` | 9 processes |
| `res_temp` | Computes `wellhead_t` | reservoir_well_interface, downhole_pump |

---

## PURE PASS-THROUGH: 59 attributes

Every other cached attribute exists only for process consumption:

AGR_feedin_press, API, depth, distance_survey, downhole_pump, ecosystem_richness, eta_rig,
field_development_intensity, flood_gas_type, FOR, frac_CO2_breakthrough, frac_water_reinj,
frac_wells_horizontal, fraction_elec_onsite, fraction_remaining_gas_inj, fraction_steam_cogen,
fraction_steam_solar, fraction_wells_fractured, friction_factor, friction_loss_steam_distr,
gas_comp, gas_flooding, gas_lifting, gas_oil_ratio, gas_path, GOR, GFIR, GLIR, length_lateral,
mined_bitumen_p, mined_bitumen_t, natural_gas_reinjection, natural_gas_to_liquefaction_frac,
num_water_inj_wells, num_gas_inj_wells, number_wells_dry, number_wells_exploratory, offshore,
oil_path, oil_volume_rate, pipe_leakage, pressure_gradient_fracturing, prod_tubing_diam,
productivity_index, reflux_ratio, regeneration_feed_temp, SOR, stab_gas_press, steam_flooding,
upgrader_type, volume_per_well_fractured, frac_venting, water_flooding, water_reinjection,
weight_land_survey, weight_ocean_survey, well_complexity, well_size, ocean_tanker_size,
wellhead_t, wellhead_p, WIR, WOR

---

## Duplicates Found

- `GOR` and `gas_oil_ratio` both cache `self.attr("GOR")` — redundant
- `WOR` is cached but processes also call `field.attr("WOR")` directly (separation, gas_partition, water_treatment)

---

## Uncached Attributes Accessed via `self.attr()` / `field.attr()`

### Field's own methods (~12 attrs):
`GOR_cutoff`, `frac_wells_with_plunger`, `frac_wells_with_non_plunger`, `workovers_per_well`,
`is_flaring`, `is_REC`, `frac_well_fractured`, plus re-reads of already-cached attrs
(GOR, oil_prod, gas_lifting, GLIR, gas_flooding, flood_gas_type, GFIR, frac_CO2_breakthrough, num_prod_wells)

### SteamGenerator (~40 attrs):
Biggest consumer — reads ~40 Field XML attributes directly via `field.attr()`.
None are in `cache_attributes()`. All are steam generation config (OTSG/HRSG efficiencies,
temperatures, fuel splits, etc.).

---

## Potentially Dead XML Attributes (~20)

`sync_attr_1/2`, `country`, `age`, `liquids_unloading`, `perc_sequestration_credit`,
`common_gas_process_choice`, `stabilizer_column`, `frac_transport_*` (5),
`transport_dist_*` (5), `well_productivity_crude_oil/natural_gas`, `timeframe_land_use`,
`flaring_fracturing_flowback`, `REC_fracturing_flowback`, `number_well_workovers`,
`eta_displacement_pump`, `eta_air_blower_*` (3), `NG_fuel_share_*_produced` (2),
`waste_water_temp`

---

## Recommendations

### Keep on Field (7 attrs)
`has_grid_mix`, `num_prod_wells`, `oil_sands_mine`, `field_production_lifetime`, `res_press`, `res_temp`

### Move to ReservoirParams on FieldContext (~16 widely-shared attrs)
Core physical properties consumed by 3+ processes:
`API`, `GOR`, `WOR`, `WIR`, `gas_comp`, `depth`, `oil_volume_rate`, `res_press`, `res_temp`,
`num_prod_wells`, `offshore`, `oil_sands_mine`, `gas_flooding`, `natural_gas_reinjection`,
`gas_lifting`, `FOR`

### Move to individual Process constructors (~40+ narrow-use attrs)
Single or dual-consumer attributes. Examples:
`AGR_feedin_press` (acid_gas_removal only), `reflux_ratio` (gas_dehydration only),
`well_size` (exploration only), `pressure_gradient_fracturing` (drilling only), etc.

### Extract SteamGenerator attrs (~40)
The uncached steam attrs should become SteamGenerator's own constructor args,
not Field-level attributes at all.

### Eliminate duplicates
Remove `gas_oil_ratio` (keep `GOR`). Standardize `WOR` to cached value only.
