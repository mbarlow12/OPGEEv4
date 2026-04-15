import re
import os

processes_dir = '/home/michael/rmi/dlab/opgee/refactor-v5/opgee/processes/'

all_accesses = []

# Process each file
for filename in sorted(os.listdir(processes_dir)):
    if not filename.endswith('.py') or filename == '__init__.py':
        continue
    
    filepath = os.path.join(processes_dir, filename)
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find all self.field.X patterns with context
    for i, line in enumerate(lines, 1):
        if 'self.field.' in line:
            context = line.strip()
            match = re.search(r'self\.field\.(\w+)', line)
            if match:
                pattern = match.group(1)
                all_accesses.append({
                    'file': filename,
                    'line': i,
                    'pattern': pattern,
                    'code': context
                })

# Group by pattern
patterns = {}
for access in all_accesses:
    p = access['pattern']
    if p not in patterns:
        patterns[p] = []
    patterns[p].append(access)

print("=" * 100)
print("DETAILED FIELD ACCESS ANALYSIS")
print("=" * 100)

for pattern in sorted(patterns.keys(), key=lambda x: len(patterns[x]), reverse=True):
    accesses = patterns[pattern]
    print(f"\nself.field.{pattern} ({len(accesses)} times)")
    print("-" * 100)
    for access in accesses:
        print(f"  {access['file']}:{access['line']}")
        print(f"    {access['code']}")

