#!/usr/bin/env python3
"""
Check ALL available fields in YAML mapping
"""

import yaml

def main():
    with open('sql/mappings/orders-unified-monday-mapping.yaml', 'r') as f:
        mapping = yaml.safe_load(f)
    
    exact_matches = mapping.get('exact_matches', [])
    mapped_fields = mapping.get('mapped_fields', [])
    computed_fields = mapping.get('computed_fields', [])
    
    print(f"📊 Total available fields: {len(exact_matches) + len(mapped_fields) + len(computed_fields)}")
    print(f"   📋 Exact matches: {len(exact_matches)}")
    print(f"   📋 Mapped fields: {len(mapped_fields)}")
    print(f"   📋 Computed fields: {len(computed_fields)}")
    
    print(f"\n📋 ALL EXACT MATCH SOURCE FIELDS:")
    for i, field_config in enumerate(exact_matches):
        source_field = field_config.get('source_field', 'N/A')
        print(f"  '{source_field}',")
    
    print(f"\n📋 ALL MAPPED FIELD SOURCE FIELDS:")
    for i, field_config in enumerate(mapped_fields):
        source_field = field_config.get('source_field', 'N/A')
        print(f"  '{source_field}',")
    
    print(f"\n📋 ALL COMPUTED FIELD SOURCE FIELDS:")
    for computed_field in computed_fields:
        source_fields = computed_field.get('source_fields', [])
        for source_field in source_fields:
            print(f"  '{source_field}',")

if __name__ == "__main__":
    main()
