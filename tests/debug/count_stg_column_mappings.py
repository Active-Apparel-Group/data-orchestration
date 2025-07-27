#!/usr/bin/env python3
"""
Count STG Columns Mapped to Monday.com API
===========================================
This script parses the mapping YAML and provides a precise count 
of all STG columns currently mapped to Monday.com API columns.
"""

import yaml
import os
from typing import Dict, List, Tuple

def count_stg_column_mappings():
    """
    Count and list all STG columns mapped to Monday.com API columns
    Returns: (count, list_of_mappings)
    """
    mapping_file = "sql/mappings/orders-unified-comprehensive-mapping.yaml"
    
    if not os.path.exists(mapping_file):
        print(f"❌ Mapping file not found: {mapping_file}")
        return 0, []
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading mapping file: {e}")
        return 0, []
    
    mappings = []
    
    # Check field_mappings section
    if 'field_mappings' in mapping_config:
        field_mappings = mapping_config['field_mappings']
        
        # Process different mapping categories
        for category_name, category_data in field_mappings.items():
            if isinstance(category_data, dict):
                for field_name, field_config in category_data.items():
                    if isinstance(field_config, dict):
                        source = field_config.get('source', 'N/A')
                        target = field_config.get('target', 'N/A')
                        target_column_id = field_config.get('target_column_id', 'N/A')
                        field_type = field_config.get('type', 'N/A')
                        
                        mapping_info = {
                            'category': category_name,
                            'stg_field': field_name,
                            'source_column': source,
                            'monday_target': target,
                            'monday_column_id': target_column_id,
                            'type': field_type
                        }
                        mappings.append(mapping_info)
    
    # Check subitem_fields section
    if 'subitem_fields' in mapping_config:
        subitem_fields = mapping_config['subitem_fields']
        
        for field_name, field_config in subitem_fields.items():
            if isinstance(field_config, dict):
                source = field_config.get('source', 'N/A')
                target = field_config.get('target', 'N/A')
                target_column_id = field_config.get('target_column_id', 'N/A')
                field_type = field_config.get('type', 'N/A')
                
                mapping_info = {
                    'category': 'subitem_fields',
                    'stg_field': field_name,
                    'source_column': source,
                    'monday_target': target,
                    'monday_column_id': target_column_id,
                    'type': field_type
                }
                mappings.append(mapping_info)
    
    return len(mappings), mappings

def display_mapping_summary(count: int, mappings: List[Dict]):
    """Display detailed summary of mapped columns"""
    print("=" * 80)
    print("STG COLUMNS MAPPED TO MONDAY.COM API - COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print(f"\n📊 TOTAL STG COLUMNS MAPPED: {count}")
    print(f"📋 Mapping File: sql/mappings/orders-unified-comprehensive-mapping.yaml")
    
    if not mappings:
        print("\n❌ No mappings found!")
        return
    
    # Group by category
    by_category = {}
    for mapping in mappings:
        category = mapping['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(mapping)
    
    print(f"\n📂 MAPPINGS BY CATEGORY:")
    print("-" * 50)
    
    for category, category_mappings in by_category.items():
        print(f"\n🔸 {category.upper()} ({len(category_mappings)} fields)")
        print("-" * 30)
        
        for i, mapping in enumerate(category_mappings, 1):
            stg_field = mapping['stg_field']
            source_column = mapping['source_column']
            monday_target = mapping['monday_target']
            monday_column_id = mapping['monday_column_id']
            field_type = mapping['type']
            
            print(f"  {i:2d}. STG Field: {stg_field}")
            print(f"      Source:    {source_column}")
            print(f"      Target:    {monday_target}")
            print(f"      Column ID: {monday_column_id}")
            print(f"      Type:      {field_type}")
            print()
    
    # Validation check for real Monday.com column IDs
    print("\n🔍 COLUMN ID VALIDATION:")
    print("-" * 30)
    
    real_column_ids = []
    fake_column_ids = []
    missing_column_ids = []
    
    for mapping in mappings:
        column_id = mapping['monday_column_id']
        if column_id == 'N/A' or not column_id:
            missing_column_ids.append(mapping['stg_field'])
        elif column_id in ['text', 'numbers', 'date', 'dropdown', 'status']:
            fake_column_ids.append(f"{mapping['stg_field']} -> {column_id}")
        else:
            real_column_ids.append(f"{mapping['stg_field']} -> {column_id}")
    
    print(f"✅ Real Monday.com Column IDs: {len(real_column_ids)}")
    for real_id in real_column_ids:
        print(f"   - {real_id}")
    
    if fake_column_ids:
        print(f"\n⚠️  Fake/Generic Column IDs: {len(fake_column_ids)}")
        for fake_id in fake_column_ids:
            print(f"   - {fake_id}")
    
    if missing_column_ids:
        print(f"\n❌ Missing Column IDs: {len(missing_column_ids)}")
        for missing_id in missing_column_ids:
            print(f"   - {missing_id}")
    
    # Summary statistics
    print(f"\n📈 MAPPING STATISTICS:")
    print("-" * 25)
    print(f"Total Mapped Fields:     {count}")
    print(f"Real Column IDs:         {len(real_column_ids)}")
    print(f"Fake/Generic IDs:        {len(fake_column_ids)}")
    print(f"Missing Column IDs:      {len(missing_column_ids)}")
    print(f"Production Ready Rate:   {(len(real_column_ids) / count * 100):.1f}%")

def main():
    """Main execution function"""
    print("Starting STG column mapping analysis...")
    
    count, mappings = count_stg_column_mappings()
    display_mapping_summary(count, mappings)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
