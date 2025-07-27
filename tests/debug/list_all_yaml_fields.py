#!/usr/bin/env python3
import yaml

with open('sql/mappings/orders-unified-monday-mapping.yaml', 'r') as f:
    mapping = yaml.safe_load(f)

exact_matches = mapping.get('exact_matches', [])
print(f"All {len(exact_matches)} exact match source fields:")
for i, field in enumerate(exact_matches):
    source_field = field.get('source_field', 'N/A')
    print(f"  {i+1:2d}. {source_field}")
