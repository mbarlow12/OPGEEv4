# Field Module Analysis

**File**: `opgee/field.py`
**Lines**: 1,825
**Authors**: Richard Plevin, Wennan Long

## Overview

The `Field` class is the central orchestrator for OPGEE's LCA calculations. It represents a single oil or gas field containing all processes and streams, managing the calculation workflow from reservoir to system boundary.

## Key Classes

### FieldResult

A data container for storing calculation results:

```python
class FieldResult:
    def __init__(self, analysis_name, field_name, result_type,
                 energy_data, ghg_data, gas_data, streams_data,
                 ci_results, energy_output, trial_num, audit_data, error):
```

Used to return results from `field.run()` including:
- Energy consumption data
- GHG emissions (CO2e)
- Individual gas emissions
- Stream flow data
- Carbon intensity results

### Field

Main class inheriting from `Container`. Key responsibilities:

1. **Process Management**: Contains all `Process` instances
2. **Stream Management**: Contains all `Stream` connections
3. **Thermodynamic Objects**: Creates `Oil`, `Gas`, `Water` instances
4. **Carbon Intensity Calculation**: Computes CI at system boundaries
5. **Graph Analysis**: Uses NetworkX for process dependency resolution

## Key Attributes (100+ from XML)

Field attributes are defined in `opgee/etc/attributes.xml`. Major categories:

| Category | Example Attributes |
|----------|-------------------|
| Production | `oil_prod`, `GOR`, `WOR`, `num_prod_wells` |
| Reservoir | `res_temp`, `res_press`, `depth`, `API` |
| Gas Composition | `gas_comp_C1` through `gas_comp_CO2` |
| Processing | `gas_processing_path`, `oil_processing_path` |
| Enhanced Recovery | `steam_flooding`, `water_flooding`, `gas_flooding` |
| Transport | `offshore`, `ocean_tanker_size` |

## Key Methods

### `run(analysis, compute_ci=True, trial_num=None)`

Main entry point for field calculations:

```python
def run(self, analysis, compute_ci=True, trial_num=None):
    self.check_enabled_processes()
    boundary_proc = self.boundary_process(analysis)
    self.procs_beyond_boundary = boundary_proc.beyond_boundary()

    self.reset()
    self._impute()
    self.reset_iteration()
    self.run_processes(analysis)

    self.check_balances()
    self.get_energy_rates()
    self.get_emission_rates(analysis, procs_to_exclude=self.procs_beyond_boundary)
    self.carbon_intensity = self.compute_carbon_intensity(analysis)
```

### `compute_carbon_intensity(analysis)`

Calculates CI in g CO2e/MJ:

```python
def compute_carbon_intensity(self, analysis):
    rates = self.emissions.rates(analysis.gwp)
    onsite_emissions = rates.loc["GHG"].sum()
    net_import = self.get_net_imported_product()
    imported_emissions = self.get_imported_emissions(net_import)
    total_emissions = onsite_emissions + imported_emissions

    boundary_energy_flow_rate = self.boundary_energy_flow_rate(analysis)
    self.carbon_intensity = (total_emissions / boundary_energy_flow_rate).to("grams/MJ")
    return self.carbon_intensity
```

### `add_children(aggs, procs, streams, process_choice_dict)`

Initializes field structure after XML parsing:
- Adds processes and aggregators
- Creates built-in `Reservoir` process
- Connects streams to processes
- Validates boundary declarations
- Builds process dependency graph

### `finalize_process_graph()`

Completes field initialization:
- Applies smart defaults
- Resolves process choices (mutually exclusive groups)
- Builds NetworkX graph
- Detects cycles for iterative solving

## Process Graph Management

The field uses NetworkX to manage process execution order:

```python
self.graph = self._connect_processes()
self.cycles = list(nx.simple_cycles(g))
```

Processes are executed in topological order, with special handling for:
- **Cycles**: Iterative convergence with `maximum_iterations` limit
- **Imputation**: Upstream value propagation for missing data
- **Boundaries**: Tracking which processes are within/beyond the analysis boundary

## Thermodynamic Objects

Each field creates instances for property calculations:

```python
self.oil = Oil(self)    # Crude oil properties
self.gas = Gas(self)    # Natural gas properties
self.water = Water(self) # Water/steam properties
```

These provide:
- Density calculations
- Energy content (LHV/HHV)
- Formation volume factors
- Bubble point calculations

## Smart Defaults

The field applies computed defaults based on field properties:

```python
SmartDefault.apply_defaults(self)
self.cache_attributes()  # Refresh after defaults applied
```

Smart defaults allow automatic calculation of values like:
- Wellhead temperature/pressure from reservoir conditions
- Equipment sizing from production rates
- Default gas compositions

## Process Choices

Fields support mutually exclusive process groups:

```python
self.resolve_process_choices()
```

For example, a field might choose between:
- Gas lifting vs. downhole pump
- Steam flooding vs. water flooding

## Import/Export Tracking

```python
self.import_export = ImportExport()
```

Tracks:
- Imported electricity, fuel, water
- Exported products
- Net import calculations for emissions allocation

## Key Dependencies

- `networkx`: Process graph analysis
- `pint`: Physical units handling
- `pandas`: Data structures
- `opgee.thermodynamics`: Oil, Gas, Water classes
- `opgee.process`: Process base class
- `opgee.stream`: Stream connections
