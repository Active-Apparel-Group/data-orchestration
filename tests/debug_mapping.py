#!/usr/bin/env python3
"""
Debug the exact mapping process to see why value_mapping is not working
"""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

def debug_value_mapping():
    """Debug why value mapping is not working for ORDER TYPE -> ORDER STATUS"""
    print('=' * 70)
    print('🐛 DEBUG VALUE MAPPING')
    print('=' * 70)
    
    # Import required modules
    from customer_master_schedule.order_queries import get_new_orders_from_unified
    from customer_master_schedule.order_mapping import (
        transform_order_data, 
        load_mapping_config,
        load_customer_mapping
    )
    
    # Get one order
    print("📋 Getting test order...")
    orders_df = get_new_orders_from_unified()
    if orders_df.empty:
        print("❌ No orders found")
        return
        
    first_order = orders_df.iloc[0]
    print(f"✅ Test order: {first_order['AAG ORDER NUMBER']}")
    print(f"   ORDER TYPE value: '{first_order['ORDER TYPE']}'")
    
    # Load configurations
    print("\n⚙️ Loading configurations...")
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    # Check ORDER TYPE mapping in config
    print("\n🔍 Checking ORDER TYPE mapping in config...")
    mapped_fields = mapping_config.get('mapped_fields', [])
    order_type_mapping = None
    
    for mapping in mapped_fields:
        if mapping.get('source_field') == 'ORDER TYPE':
            order_type_mapping = mapping
            print(f"✅ Found ORDER TYPE mapping:")
            print(f"   Source field: {mapping['source_field']}")
            print(f"   Target field: {mapping['target_field']}")
            print(f"   Target column ID: {mapping['target_column_id']}")
            print(f"   Transformation: {mapping['transformation']}")
            if 'mapping_rules' in mapping:
                print(f"   Mapping rules: {mapping['mapping_rules']}")
            break
    
    if not order_type_mapping:
        print("❌ ORDER TYPE mapping not found in config!")
        return
    
    # Transform the order and see what happens
    print("\n🔄 Transforming order data...")
    transformed = transform_order_data(first_order, mapping_config, customer_lookup)
    
    # Check if ORDER STATUS is in the transformed data
    print("\n📊 Checking transformed data for ORDER STATUS...")
    if 'ORDER STATUS' in transformed:
        order_status = transformed['ORDER STATUS']
        print(f"✅ ORDER STATUS found in transformed data:")
        print(f"   Value: '{order_status['value']}'")
        print(f"   Column ID: {order_status['column_id']}")
        print(f"   Type: {order_status['type']}")
        print(f"   Source field: {order_status['source_field']}")
    else:
        print("❌ ORDER STATUS not found in transformed data!")
        print("Available fields:", list(transformed.keys()))
        
    return True

if __name__ == "__main__":
    debug_value_mapping()
