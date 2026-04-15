import re
from collections import defaultdict

print("=" * 100)
print("COMPREHENSIVE FIELD ACCESS ANALYSIS REPORT")
print("=" * 100)

print("\n" + "=" * 100)
print("PART 1: ACCESS PATTERN SUMMARY (33 total accesses across 51 process files)")
print("=" * 100)

patterns = {
    'self.field.attr': 5,
    'self.field.model': 4,
    'self.field.gas': 4,
    'self.field.oil': 3,
    'self.field.get_process_data': 3,
    'self.field.res_press': 2,
    'self.field.oil_path': 2,
    'self.field.water': 2,
    'self.field.save_process_data': 2,
    'self.field.LNG_temp': 1,
    'self.field.imported_gas_comp': 1,
    'self.field.oil_sands_mine': 1,
    'self.field.stp': 1,
    'self.field.gas_path': 1,
    'self.field.natural_gas_to_liquefaction_frac': 1
}

print("\nTop 15 patterns by frequency:")
for i, (pattern, count) in enumerate(sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:15], 1):
    pct = (count / 33) * 100
    print(f"{i:2}. {pattern:40} - {count:2} times ({pct:5.1f}%)")

print("\n" + "=" * 100)
print("PART 2: CATEGORICAL BREAKDOWN")
print("=" * 100)

categories = {
    'THERMODYNAMICS (Gas/Oil/Water objects)': {
        'patterns': ['oil', 'gas', 'water'],
        'count': 9,
        'concern': 'LOW - These are fundamental property providers, not inter-process dependencies'
    },
    'FIELD CONFIG ATTRIBUTES': {
        'patterns': ['oil_path', 'gas_path', 'res_press', 'res_temp', 'LNG_temp', 'oil_sands_mine',
                    'stp', 'natural_gas_to_liquefaction_frac'],
        'count': 9,
        'concern': 'LOW - Static field configuration, not process-dependent'
    },
    'PROCESS DATA EXCHANGE': {
        'patterns': ['get_process_data', 'save_process_data'],
        'count': 5,
        'concern': 'MEDIUM-HIGH - Enables inter-process coupling via shared bulletin board'
    },
    'FIELD ATTRIBUTES (via attr())': {
        'patterns': ['attr'],
        'count': 5,
        'concern': 'LOW - Static field attributes, not process-dependent'
    },
    'MODEL ACCESS': {
        'patterns': ['model'],
        'count': 4,
        'concern': 'LOW - Accessing global model configuration (constants, tables)'
    }
}

for cat, info in categories.items():
    print(f"\n{cat}")
    print(f"  Patterns: {', '.join(info['patterns'])}")
    print(f"  Total accesses: {info['count']}")
    print(f"  Concern level: {info['concern']}")

print("\n" + "=" * 100)
print("PART 3: INTER-PROCESS COUPLING VIA PROCESS_DATA")
print("=" * 100)

print("\nFound 19 unique data items exchanged via Field.process_data dictionary:")
process_data_patterns = {
    'crude_LHV': ['Exploration (save)', 'CrudeOilTransport (save)', 'TransportEnergy (get)'],
    'exported_prod_LHV': ['Boundary (save)', 'Exploration (get)'],
    'exported_gas': ['GasPartition (save)', 'SteamGenerator (get)'],
    'gas_tp_after_separation': ['Separation (save)', 'CrudeOilStabilization (get)', 'Venting (get)'],
    'processing_unit_loss_rate_df': ['GasGathering (save)', 'AcidGasRemoval/Demethanizer/etc (get)'],
    'gas_flooding_stream': ['GasPartition (save)', 'GasPartition (get)'],
    'CO2_flooding_rate_init': ['GasPartition (save)', 'ReservoirWellInterface (get)'],
    'wellhead_LHV_rate': ['Separation (save)', 'Drilling (get)'],
    'drill_energy_consumption': ['Exploration (save)', 'Drilling (get)'],
    'num_wells': ['Exploration (save)', 'Drilling (get)'],
}

print("\nMost critical inter-process dependencies:")
for item, flows in sorted(process_data_patterns.items())[:10]:
    print(f"  {item:40} - {len(flows)} reader(s)")
    for flow in flows:
        print(f"    {flow}")

print("\n" + "=" * 100)
print("PART 4: VIOLATION ASSESSMENT")
print("=" * 100)

print("\nPRINCIPLE: 'Processes should not know about other processes'")
print("\nVIOLATIONS FOUND:")

print("\n1. DIRECT INTER-PROCESS COUPLING (Severity: MEDIUM-HIGH)")
print("   Pattern: Process A saves data -> Process B reads data via Field.process_data")
print("   Violations found: 5 major patterns")
print("   Examples:")
print("     • Exploration.run() -> stores 'num_wells' -> Drilling.run() reads it")
print("     • GasPartition.run() -> stores 'exported_gas' -> SteamGenerator.run() reads it")
print("     • Separation.run() -> stores 'gas_tp_after_separation' -> Venting.run() reads it")
print("   Impact: Silent failures if upstream process not executed or skipped")

print("\n2. HIDDEN DEPENDENCIES (Severity: MEDIUM)")
print("   Pattern: Boundary process writes data expected by downstream processes")
print("   Violations found: 3+ instances")
print("   Examples:")
print("     • Boundary.run() saves 'exported_prod_LHV', 'boundary_API'")
print("     • Exploration.run() expects 'exported_prod_LHV' to exist")
print("     • Drilling.run() consumes multiple items from other processes")
print("   Impact: Unclear execution order requirements in complex models")

print("\n3. THERMODYNAMICS/CONFIG ACCESS (Severity: LOW)")
print("   Pattern: Safe property/config access that doesn't couple processes")
print("   Accesses: 22 of 33 (67%)")
print("   Impact: No inter-process coupling concerns")

print("\n" + "=" * 100)
print("PART 5: QUANTITATIVE SUMMARY")
print("=" * 100)

print(f"\nTotal self.field accesses found: 33")
print(f"Unique patterns: 15")
print(f"Files with self.field access: ~12 out of 51 process files (24%)")
print(f"Total save_process_data calls across codebase: ~26")
print(f"Total get_process_data calls across codebase: ~24")

print(f"\nBreakdown by category:")
print(f"  ✓ Thermodynamics objects:     9 (27%)  - Safe to keep")
print(f"  ✓ Field config attributes:    9 (27%)  - Safe to keep")
print(f"  ✓ Model access (const/tbl):   4 (12%)  - Safe to keep")
print(f"  ✓ Field attributes (attr()):  5 (15%)  - Safe to keep")
print(f"  ✗ Process data exchange:      5 (15%)  - REFACTOR CANDIDATES")
print(f"                                -----")
print(f"                    Total:     33 (100%)")

print(f"\nRisk Assessment:")
print(f"  Low Risk (safe to keep):       27 (82%)")
print(f"  Medium Risk (review):           5 (15%)")
print(f"  High Risk (refactor priority):  1 ( 3%)")

print("\n" + "=" * 100)
print("PART 6: REFACTORING RECOMMENDATIONS")
print("=" * 100)

print("\nRECOMMENDATION 1: Keep these safe accesses as-is")
print("  • self.field.oil, self.field.gas, self.field.water (thermodynamics)")
print("  • self.field.model.const(), self.field.model.<tables>")
print("  • self.field.<config_attributes> (oil_path, res_press, LNG_temp, etc)")
print("  Estimate: 22/33 accesses (67%)")
print("  Effort: None")

print("\nRECOMMENDATION 2: Refactor process_data dependencies")
print("  Target: ~5 instances of inter-process data exchange")
print("  Approach Options:")
print("    A. Inject computed values as method parameters to downstream processes")
print("    B. Create context objects passed through the execution pipeline")
print("    C. Make data derivable from streams, not from Field storage")
print("  Effort: Moderate (affects 10-15 process classes)")
print("  Benefit: Reduces hidden dependencies, improves testability")

print("\nRECOMMENDATION 3: Make execution order explicit")
print("  Target: Boundary-dependent data flows")
print("  Approach:")
print("    • Document which processes depend on Boundary execution")
print("    • Consider adding validation checks for required data")
print("    • Make streaming connections explicit rather than via bulletin board")
print("  Effort: Low-Moderate")
print("  Benefit: Clearer model structure, easier debugging")

print("\n" + "=" * 100)
print("CONCLUSION")
print("=" * 100)

print("""
Current State:
    - Majority (82%) of self.field accesses are safe and appropriate
    - Field serves as both property provider AND inter-process bulletin board
    - 5 major inter-process dependencies via process_data exchange

Violations Found:
    - MEDIUM-HIGH: 5 instances of direct process-to-process coupling via Field.process_data
    - MEDIUM: 3+ hidden dependencies involving Boundary process
    - LOW: No direct process-to-process method calls (good design)

Refactoring Priority:
    1. Document and centralize process_data dependencies
    2. Refactor critical data flows (num_wells, exported_gas, gas_tp_after_separation)
    3. Consider injecting context/parameters instead of Field storage
    4. Maintain safe thermodynamics/config access patterns

Estimated Refactoring Impact:
    - High-priority refactoring: ~5 self.field accesses
    - Medium-priority documentation: ~3 patterns
    - Low-priority (no change needed): ~25 accesses
""")
