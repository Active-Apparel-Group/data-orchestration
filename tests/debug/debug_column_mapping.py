"""
Debug script to inspect Monday.com column values generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from customer_master_schedule.order_mapping import (
    load_mapping_config, 
    load_customer_mapping, 
    transform_order_data,
    get_monday_column_values_dict
)
import pandas as pd
import json

def debug_column_values():
    """Debug the column values generation process"""
    
    print("=" * 60)
    print("DEBUG: Monday.com Column Values Generation")
    print("=" * 60)
    
    # Load configurations
    print("\n1. Loading configurations...")
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    if not mapping_config:
        print("❌ Failed to load mapping config")
        return
    
    # Create sample order data (matching real data structure)
    print("\n2. Creating sample order data...")
    sample_order = pd.Series({
        'AAG ORDER NUMBER': 'MWE-00025',
        'CUSTOMER NAME': 'MACK WELDON',
        'CUSTOMER STYLE': 'M01Z26',
        'CUSTOMER COLOUR DESCRIPTION': 'TOTAL ECLIPSE/TRUE BLACK LINER',
        'STYLE DESCRIPTION': 'POCKETED RUN SHORT',
        'CUSTOMER SEASON': 'SPRING SUMMER 2026',
        'ORDER DATE PO RECEIVED': '2025-05-20',
        'PO NUMBER': '8148-00',
        'CUSTOMER PRICE': '28.86',
        'CATEGORY': 'MENS',
        'ORDER TYPE': 'ACTIVE',
        'EX FACTORY DATE': '2025-09-26'
    })
    
    print(f"Sample order: {sample_order['AAG ORDER NUMBER']}")
    print(f"Customer: {sample_order['CUSTOMER NAME']}")
    print(f"Style: {sample_order['CUSTOMER STYLE']}")
    print(f"Color: {sample_order['CUSTOMER COLOUR DESCRIPTION']}")
    
    # Transform the data
    print("\n3. Transforming order data...")
    transformed = transform_order_data(sample_order, mapping_config, customer_lookup)
    
    print(f"Transformed fields count: {len(transformed)}")
    print("\nTransformed field structure (first 5 fields):")
    count = 0
    for field_name, field_data in transformed.items():
        if count >= 5:
            break
        print(f"  {field_name}: {field_data}")
        count += 1
    
    # Check specific important fields
    print("\n4. Checking critical fields...")
    critical_fields = ['CUSTOMER', 'STYLE', 'COLOR', 'AAG ORDER NUMBER']
    
    for field in critical_fields:
        if field in transformed:
            field_data = transformed[field]
            print(f"✅ {field}:")
            print(f"   Value: {field_data.get('value')}")
            print(f"   Column ID: {field_data.get('column_id')}")
            print(f"   Type: {field_data.get('type')}")
        else:
            print(f"❌ {field}: NOT FOUND in transformed data")
    
    # Generate Monday.com column values
    print("\n5. Generating Monday.com column values...")
    column_values = get_monday_column_values_dict(transformed)
    
    print(f"Column values count: {len(column_values)}")
    print(f"Column values keys: {list(column_values.keys())}")
    
    # Show the actual column values structure
    print("\n6. Monday.com API payload structure:")
    print(json.dumps(column_values, indent=2, default=str))
    
    # Check for specific column IDs from YAML
    print("\n7. Checking specific YAML column IDs...")
    expected_columns = {
        'dropdown_mkr542p2': 'CUSTOMER',
        'dropdown_mkr5tgaa': 'STYLE', 
        'dropdown_mkr5677f': 'COLOR',
        'text_mkr5ej2x': 'PO NUMBER',
        'text_mkrh94rx': 'CUSTOMER ALT PO'
    }
    
    for column_id, field_name in expected_columns.items():
        if column_id in column_values:
            print(f"✅ {column_id} ({field_name}): {column_values[column_id]}")
        else:
            print(f"❌ {column_id} ({field_name}): MISSING")
    
    # Check YAML mapping structure
    print("\n8. YAML mapping structure analysis...")
    exact_matches = mapping_config.get('exact_matches', [])
    mapped_fields = mapping_config.get('mapped_fields', [])
    
    print(f"Exact matches: {len(exact_matches)}")
    print(f"Mapped fields: {len(mapped_fields)}")
    
    # Find Customer, Style, Color mappings in YAML
    customer_mapping = None
    style_mapping = None
    color_mapping = None
    
    for mapping in exact_matches + mapped_fields:
        target_field = mapping.get('target_field')
        if target_field == 'CUSTOMER':
            customer_mapping = mapping
        elif target_field == 'STYLE':
            style_mapping = mapping
        elif target_field == 'COLOR':
            color_mapping = mapping
    
    print("\n9. Critical field mappings from YAML:")
    for name, mapping in [('Customer', customer_mapping), ('Style', style_mapping), ('Color', color_mapping)]:
        if mapping:
            print(f"✅ {name}:")
            print(f"   Source: {mapping.get('source_field')}")
            print(f"   Target: {mapping.get('target_field')}")
            print(f"   Column ID: {mapping.get('target_column_id')}")
            print(f"   Type: {mapping.get('target_type')}")
            print(f"   Transformation: {mapping.get('transformation', 'direct_mapping')}")
        else:
            print(f"❌ {name}: NOT FOUND in YAML mappings")

if __name__ == "__main__":
    debug_column_values()
