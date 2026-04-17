# Field Attribute Trace: Process Files

**Date**: 2026-04-16
**Source**: Automated trace of all 51 process files in `opgee/processes/`

---

## Summary Statistics

- **Total process files scanned:** 51
- **Files with `field.attr("...")` calls:** 8
- **Files with `field.attrs_with_prefix("...")` calls:** 2
- **Files accessing cached field properties (`field.property`):** ~30
- **Files with no field attribute access at all:** ~10
- **Total unique field attribute names (all patterns):** ~95

---

## Direct `field.attr("name")` Calls (43 unique attribute names)

Only 5 attributes are accessed by more than 1 process via `field.attr()`:

| Attribute | Count | Processes |
|-----------|-------|-----------|
| **API** | 3 | bitumen_mining, separation, steam_generator |
| **WOR** | 3 | gas_partition, separation, water_treatment |
| **prod_water_inlet_temp** | 1 | steam_generator (called in 2 runtime methods) |
| All other 40 attrs | 1 each | steam_generator (35 of them), plus 1 each in VF_partition, acid_gas_removal, downhole_pump |

**steam_generator.py accounts for 38 of the 43 direct `field.attr()` call sites.** It is not a Process subclass — it is an `OpgeeObject` helper instantiated by the `SteamGeneration` process.

---

## `field.attrs_with_prefix()` Calls (4 prefixes)

| Prefix | Attributes | Process |
|--------|-----------|---------|
| `frac_transport_` | tanker, barge, pipeline, rail, truck | crude_oil_transport |
| `transport_dist_` | tanker, barge, pipeline, rail, truck | crude_oil_transport |
| `OTSG_exhaust_temp_` | outlet, before_preheater, before_economizer | steam_generator |
| `HRSG_exhaust_temp_` | outlet, before_preheater, before_economizer | steam_generator |

---

## Most Widely Used Field Properties (via cached `field.property`)

| Attribute (XML name) | Property | Process Count |
|----------------------|----------|---------------|
| oil_prod | oil_volume_rate | 12 |
| res_press | res_press | 8 |
| oil_sands_mine | oil_sands_mine | 7 |
| gas_lifting | gas_lifting | 4 |
| gas_flooding | gas_flooding | 4 |
| natural_gas_reinjection | natural_gas_reinjection | 4 |
| FOR | FOR | 4 |
| depth | depth | 4 |

---

## Key Inconsistency: WOR and API

- **WOR** is accessed both as `field.WOR` (cached, in gas_partition.cache_attributes) AND `field.attr("WOR")` (direct lookup, in gas_partition.run, separation.run, water_treatment.run). The runtime `field.attr("WOR")` calls look like they should use the cached value instead.
- **API** has no cached property on Field at all — it is only ever accessed via `field.attr("API")` by 3 processes (bitumen_mining, separation, steam_generator). This is inconsistent with how other core reservoir properties are handled.

---

## Single-Consumer Attributes (candidates for process-level)

These field-level attributes are consumed by exactly 1 process file:

| Process | Exclusive Attributes |
|---------|---------------------|
| exploration.py | well_size, well_complexity, eta_rig, weight_land_survey, weight_ocean_survey, distance_survey, number_wells_dry, number_wells_exploratory, fraction_wells_horizontal, length_lateral (10) |
| drilling.py | fraction_wells_fractured, pressure_gradient_fracturing, volume_per_well_fractured (3) |
| steam_generator.py | 35+ OTSG/HRSG configuration attrs |
| VF_partition.py | combusted_gas_frac (1) |
| acid_gas_removal.py | AGR_feedin_press (1) |
| gas_dehydration.py | reflux_ratio, regeneration_feed_temp (2) |

---

## Implication for Design

The vast majority of `field.attr()` calls are single-consumer — they should become process constructor args, not ReservoirParams fields. Only widely-shared properties (oil_volume_rate, res_press, oil_sands_mine, gas_lifting, etc.) belong on FieldContext.
