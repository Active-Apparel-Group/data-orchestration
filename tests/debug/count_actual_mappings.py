#!/usr/bin/env python3
"""
Count actual mappings and fix the coverage calculation
"""
import yaml
from pathlib import Path

# Load the current mapping file
mapping_path = Path("sql/mappings/orders-unified-comprehensive-mapping.yaml")
with open(mapping_path, 'r') as f:
    data = yaml.safe_load(f)

# Count exact matches
exact_matches = data.get('exact_matches', [])
print(f'Exact matches: {len(exact_matches)}')

# Count different mapping categories that might exist
total_mappings = len(exact_matches)

# Check for other mapping categories
for key in data.keys():
    if key != 'exact_matches' and key != 'metadata' and key != 'orchestration_workflow':
        if isinstance(data[key], list):
            print(f'{key}: {len(data[key])}')
            total_mappings += len(data[key])

print(f'Total mappings: {total_mappings}')

# Monday columns info
metadata = data.get('metadata', {})
monday_columns = metadata.get('target_monday_columns', 88)
print(f'Monday.com columns from metadata: {monday_columns}')

# Calculate CORRECTED coverage
staging_management_columns = 10
mappable_columns = monday_columns - staging_management_columns
coverage_percent = (total_mappings / mappable_columns) * 100 if mappable_columns > 0 else 0

print()
print("CORRECTED COVERAGE CALCULATION:")
print(f'Monday.com total columns: {monday_columns}')
print(f'Staging management columns (excluded): {staging_management_columns}')
print(f'Mappable columns: {monday_columns} - {staging_management_columns} = {mappable_columns}')
print(f'Current mappings: {total_mappings}')
print(f'Coverage: {total_mappings}/{mappable_columns} = {coverage_percent:.2f}%')

# You're absolutely right - it should be 88 - 10 = 78!
print()
print(f"✅ YOU'RE RIGHT! The calculation should be:")
print(f"   88 Monday.com columns - 10 staging columns = 78 mappable columns")
print(f"   Coverage: {total_mappings}/78 = {(total_mappings/78)*100:.2f}%")
