# Process Module Analysis

**File**: `opgee/process.py`
**Lines**: 1,125
**Authors**: Richard Plevin, Wennan Long

## Overview

The `Process` class is the abstract base class for all LCA calculation steps in OPGEE. Each process represents a specific operation in oil/gas production (drilling, separation, compression, transport, etc.) and computes energy consumption and emissions.

## Key Classes

### IntermediateValues

Stores intermediate calculation results for debugging/display:

```python
class IntermediateValues:
    def store(self, name, value, unit=None, desc=None):
        # Stores values with optional units and descriptions
        pass

    def get(self, name):
        # Retrieve stored intermediate value
        pass
```

### Process

Abstract base class inheriting from `AttributeMixin` and `XmlInstantiable`.

```python
class Process(AttributeMixin, XmlInstantiable):
    # Stream direction constants
    INPUT = 'input'
    OUTPUT = 'output'

    # Class-level tracking of iterating processes
    iterating_processes = []

    # Subclass validation requirements
    _required_inputs = []
    _required_outputs = []
```

## Constructor

```python
def __init__(self, name, attr_dict=None, parent=None, desc=None,
             cycle_start=False, impute_start=False, boundary=None):
    # Get references to field thermodynamic objects
    self.gas = field.gas
    self.oil = field.oil
    self.water = field.water

    # Initialize tracking objects
    self.energy = Energy()
    self.emissions = Emissions()
    self.import_export = ImportExport()

    # Cycle/iteration support
    self.visit_count = 0
    self.iteration_value = None
```

## Key Methods

### Abstract Methods (must be implemented by subclasses)

```python
def run(self, analysis):
    """Core calculation logic - MUST be implemented"""
    raise AbstractMethodError()

def bypass(self):
    """Called when process is disabled - optional override"""
    pass
```

### Stream Finding Methods

```python
def find_input_stream(self, stream_type, regex=False, raiseError=True) -> Stream:
    """Find exactly one input stream of given type"""

def find_input_streams(self, stream_type, combine=False, as_list=False, regex=False) -> list:
    """Find all input streams of given type"""

def find_output_stream(self, stream_type, regex=False, raiseError=True) -> Stream:
    """Find exactly one output stream of given type"""

def find_output_streams(self, stream_type, combine=False, as_list=False, regex=False) -> list:
    """Find all output streams of given type"""
```

### Energy Methods

```python
def add_energy_rate(self, carrier, rate):
    """Add energy consumption for a single carrier (mmbtu/day LHV)"""

def add_energy_rates(self, dictionary):
    """Add energy consumption for multiple carriers"""

def get_energy_rates(self):
    """Return current energy consumption rates"""
```

### Emission Methods

```python
def add_emission_rate(self, category, gas, rate):
    """Add emission rate for a single gas in a category"""

def add_emission_rates(self, category, **kwargs):
    """Add emissions: add_emission_rates('combustion', CO2=100, CH4=30)"""

def get_emission_rates(self, analysis, procs_to_exclude=None):
    """Return emission rates with GWP-weighted GHG value"""

def set_combustion_emissions(self):
    """Compute and set combustion emissions from energy use"""
    emissions = self.compute_emission_combustion()
    self.emissions.set_rate(EM_COMBUSTION, "CO2", emissions)
```

### Validation Methods

```python
def validate(self):
    """Validate process configuration"""
    self.validate_streams()
    self.validate_proc()

def validate_streams(self):
    """Verify required input/output streams are connected"""

def validate_proc(self):
    """Optional - subclass-specific validation"""
```

### Iteration/Cycle Support

```python
def set_iteration_value(self, value):
    """Store value to check for convergence in process loops"""

def check_convergence(self):
    """Check if iteration value has converged within tolerance"""

def reset_iteration(self):
    """Reset iteration state between runs"""
```

### Graph Navigation

```python
def predecessors(self) -> set:
    """Return immediate upstream processes"""

def successors(self) -> set:
    """Return immediate downstream processes"""

def within_boundary(self) -> set:
    """Return all processes upstream of this boundary"""

def beyond_boundary(self) -> set:
    """Return all processes downstream of this boundary"""
```

## Process Implementation Pattern

Example subclass structure:

```python
from opgee.process import Process

class MyProcess(Process):
    _required_inputs = ['gas']
    _required_outputs = ['gas']

    def run(self, analysis):
        # 1. Get input streams
        input_stream = self.find_input_stream("gas")

        # 2. Perform calculations
        gas_rate = input_stream.gas_flow_rate("C1")
        energy_used = self.calculate_compression_energy(gas_rate)

        # 3. Record energy consumption
        self.add_energy_rate("Natural gas", energy_used)

        # 4. Calculate and set emissions
        self.set_combustion_emissions()

        # 5. Set output stream
        output = self.find_output_stream("gas")
        output.copy_flow_rates_from(input_stream)
```

## Special Process Types

### Boundary

Marker process for system boundaries (no calculations):

```python
class Boundary(Process):
    def run(self, analysis):
        pass  # No-op - just marks boundary
```

### Reservoir

Built-in source process (outputs only, no inputs):

```python
class Reservoir(Process):
    def run(self, analysis):
        # Sets initial stream conditions from field attributes
        pass
```

### Aggregator

Container for grouping related processes:

```python
class Aggregator(Container):
    # Groups processes for organizational purposes
    pass
```

## Subclass Registration

Processes are discovered dynamically:

```python
def reload_subclass_dict():
    """Scan for all Process subclasses in opgee/processes/"""
    global _Subclass_dict
    _Subclass_dict = {
        Process: _subclass_dict(Process),
        Aggregator: _subclass_dict(Aggregator),
    }
```

This enables:
- Plugin processes from user-defined files
- Dynamic process loading from configuration

## Key Dependencies

- `opgee.energy`: Energy carrier tracking
- `opgee.emissions`: Emission category tracking
- `opgee.stream`: Stream flow handling
- `opgee.attributes`: XML attribute handling
- `pint`: Unit handling via `ureg`
- `pandas`: Data structures

## Process Configuration

From `attributes.xml`:

```xml
<ClassAttrs name="Process">
    <Attr name="leak_rate" type="float" value="0.0" unit="frac"/>
</ClassAttrs>
```

Process-specific attributes are defined per process class:

```xml
<ClassAttrs name="Compressor">
    <Attr name="eta_compressor" type="float" value="0.75" unit="frac"/>
    <Attr name="prime_mover" type="str" value="NG_engine">
        <Options default="NG_engine">NG_engine,Electric</Options>
    </Attr>
</ClassAttrs>
```
