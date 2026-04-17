# Field Property Access Trace: Process Subclasses

**Date**: 2026-04-16
**Source**: Automated trace of all 51 process files in `opgee/processes/`

---

## Summary Statistics

- **Total unique field properties accessed by processes**: ~75+
- **Files with field property accesses**: 44 out of 51
- **Files with NO field accesses**: 7 (flaring, LNG_regasification, natural_gas_liquid, pre_membrane_chiller, storage_separator, storage_well, __init__)
- **Most-accessed properties**: model (12), gas (11), stp (10), oil_volume_rate (10), water (9), res_press (8), oil (8)
- **Heaviest field consumers**: gas_partition (25+), exploration (20+), drilling (15+), downhole_pump (15+), steam_generator (15+), separation (12+)

---

## Thermo Models (oil/gas/water)

Note: Process base `__init__` already copies `field.gas`, `field.oil`, `field.water` to `self.gas`, `self.oil`, `self.water`. These accesses below are cases where processes still go through `self.field.<thermo>`.

| Property | File Count | Files |
|---|---|---|
| `field.gas` | 11 | compressor, crude_oil_stabilization, demethanizer, downhole_pump, gas_gathering, gas_partition, heavy_oil_upgrading, post_storage_compressor, reservoir_well_interface, separation, VF_partition |
| `field.oil` | 8 | crude_oil_storage, drilling, downhole_pump, heavy_oil_dilution, heavy_oil_upgrading, reservoir_well_interface, separation, crude_oil_stabilization |
| `field.water` | 9 | acid_gas_removal, crude_oil_dewatering, crude_oil_storage, demethanizer, downhole_pump, gas_dehydration, reservoir_well_interface, separation, water_treatment |

---

## Shared State

| Property | File Count | Notes |
|---|---|---|
| `field.stp` | 10 | bitumen_mining, CO2_membrane, crude_oil_storage, drilling, gas_gathering, gas_partition, heavy_oil_upgrading, separation, venting + base Process class |
| `field.get_process_data(...)` | 17 | Inter-process bulletin board (read) |
| `field.save_process_data(...)` | 15 | Inter-process bulletin board (write) |

---

## Complex Objects

| Property | File Count | Notes |
|---|---|---|
| `field.model` | 12 | For constants and data tables |
| `field.import_export` | 10 | Import/export tracking |
| `field.transport_energy` | 5 | Transport energy calcs |
| `field.imported_gas_comp` | 6 | Gas compositions by name |
| `field.component_fugitive_table` | 3 | Loss rate lookups |
| `field.gas_comp` | 3 | Gas composition series |
| `field.steam_generator` | 1 | steam_generation only |
| `field.vertical_drill_df` | 1 | exploration only |
| `field.horizontal_drill_df` | 1 | exploration only |

---

## Cached Scalar Attributes (by access frequency)

### Widely shared (3+ processes)

| Property | File Count | Type |
|---|---|---|
| oil_volume_rate | 10 | Quantity |
| res_press | 8 | Quantity |
| gas_flooding | 6 | binary |
| natural_gas_reinjection | 5 | binary |
| oil_sands_mine | 5 | string |
| gas_lifting | 4 | binary |
| depth | 3 | Quantity |
| downhole_pump | 3 | string |
| num_prod_wells | 3 | Quantity |
| flood_gas_type | 3 | string |
| SOR | 3 | Quantity |
| water_flooding | 3 | binary |
| water_reinjection | 3 | binary |
| steam_flooding | 3 | binary |
| FOR | 3 | Quantity |
| gas_path | 3 | string |

### Narrowly used (1-2 processes)

~40 remaining scalar properties are each accessed by only 1-2 files. These are strong candidates for becoming process constructor args rather than FieldContext members.

---

## Field Internal Usage (field.py)

### Used internally by Field's own methods:
- `self.oil`, `self.gas` — in `boundary_energy_flow_rate()`
- `self.model` — in `get_component_fugitive()`, `validate()`, `run()`
- `self.import_export` — in `get_net_imported_product()`, `get_carbon_credit()`
- `self.process_data` — in `save_process_data()`, `get_process_data()`
- `self.oil_sands_mine`, `self.num_prod_wells`, `self.field_production_lifetime` — in `get_completion_and_workover_C1_rate()`
- `self.component_fugitive_table`, `self.loss_mat_gas_ave_df` — set in `add_children()`

### Only exposed for process consumption (not used in Field logic):
All other ~55 cached scalar attributes exist solely for `field.<attr>` access by processes. Field itself never uses them post-initialization.

### Pass-through from Model:
- `self.imported_gas_comp` = `model.imported_gas_comp`
- `self.vertical_drill_df` = `model.vertical_drill_df`
- `self.horizontal_drill_df` = `model.horizontal_drill_df`
- `self.LNG_temp` = `model.const("LNG-temp")`

---

## Heaviest Consumers (per-file)

| Process | Unique field accesses |
|---------|---------------------|
| gas_partition | 25+ |
| exploration | 20+ |
| drilling | 15+ |
| downhole_pump | 15+ |
| steam_generator | 15+ |
| separation | 12+ |
| venting | 10+ |
| bitumen_mining | 10+ |
| water_injection | 8+ |
| heavy_oil_upgrading | 8+ |
