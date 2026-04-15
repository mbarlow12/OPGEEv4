import re
import os
from collections import defaultdict

processes_dir = '/home/michael/rmi/dlab/opgee/refactor-v5/opgee/processes/'

# Dictionary to store patterns
patterns = defaultdict(list)
all_accesses = []

# Process each file
for filename in os.listdir(processes_dir):
    if not filename.endswith('.py') or filename == '__init__.py':
        continue
    
    filepath = os.path.join(processes_dir, filename)
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all self.field.X patterns
    matches = re.finditer(r'self\.field\.(\w+)', content)
    
    for match in matches:
        access_pattern = match.group(1)
        all_accesses.append((filename, access_pattern, match.start()))
        patterns[access_pattern].append(filename)

# Sort by frequency
sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)

print("=" * 80)
print("SELF.FIELD ACCESS PATTERNS - FREQUENCY ANALYSIS")
print("=" * 80)
print(f"\nTotal unique patterns: {len(patterns)}")
print(f"Total accesses: {len(all_accesses)}")

print("\n" + "=" * 80)
print("TOP 15 MOST COMMON PATTERNS")
print("=" * 80)

for i, (pattern, files) in enumerate(sorted_patterns[:15], 1):
    print(f"\n{i}. self.field.{pattern}")
    print(f"   Frequency: {len(files)}")
    print(f"   Used in: {', '.join(sorted(set(files)))}")

print("\n" + "=" * 80)
print("CATEGORIZATION ANALYSIS")
print("=" * 80)

categories = {
    'thermodynamics': ['oil', 'gas', 'water'],
    'field_config': ['oil_path', 'gas_path', 'res_press', 'res_temp', 'LNG_temp', 
                     'stp', 'oil_sands_mine', 'natural_gas_to_liquefaction_frac'],
    'process_data': ['save_process_data', 'get_process_data'],
    'field_attributes': ['attr'],
    'model_access': ['model'],
    'tables': ['imported_gas_comp', 'component_fugitive_table', 'loss_mat_gas_ave_df'],
    'other_processes': []  # Will find these manually
}

categorized = defaultdict(list)

for pattern, files in sorted_patterns:
    categorized_to = None
    
    if pattern in categories['thermodynamics']:
        categorized_to = 'thermodynamics'
    elif pattern in categories['field_config']:
        categorized_to = 'field_config'
    elif pattern in categories['process_data']:
        categorized_to = 'process_data'
    elif pattern in categories['field_attributes']:
        categorized_to = 'field_attributes'
    elif pattern in categories['model_access']:
        categorized_to = 'model_access'
    elif pattern in categories['tables']:
        categorized_to = 'tables'
    else:
        categorized_to = 'other'
    
    categorized[categorized_to].append((pattern, len(files)))

for category in ['thermodynamics', 'field_config', 'field_attributes', 'process_data', 
                 'model_access', 'tables', 'other']:
    if categorized[category]:
        print(f"\n{category.upper()}:")
        for pattern, count in sorted(categorized[category], key=lambda x: x[1], reverse=True):
            print(f"  - self.field.{pattern} ({count})")

