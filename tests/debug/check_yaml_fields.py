#!/usr/bin/env python3
"""
Check what source fields are expected in YAML mapping
"""

import yaml

def main():
    with open('sql/mappings/orders-unified-monday-mapping.yaml', 'r') as f:
        mapping = yaml.safe_load(f)
    
    print("📊 Source fields expected in YAML (first 20):")
    exact_matches = mapping.get('exact_matches', [])
    for i, field_config in enumerate(exact_matches[:20]):
        source_field = field_config.get('source_field', 'N/A')
        target_column_id = field_config.get('target_column_id', 'N/A')
        print(f"  {i+1:2d}. {source_field} -> {target_column_id}")
    
    print(f"\n📊 Mapped fields:")
    mapped_fields = mapping.get('mapped_fields', [])
    for i, field_config in enumerate(mapped_fields):
        source_field = field_config.get('source_field', 'N/A')
        target_field = field_config.get('target_field', 'N/A')
        target_column_id = field_config.get('target_column_id', 'N/A')
        print(f"  {i+1}. {source_field} -> {target_field} ({target_column_id})")

if __name__ == "__main__":
    main()
