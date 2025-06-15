#!/usr/bin/env python3
"""
Debug the exact column value formatting for Monday.com API
"""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

def debug_column_values():
    """Debug how column values are being formatted"""
    print('=' * 70)
    print('🐛 DEBUG COLUMN VALUES FORMATTING')
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
    first_order = orders_df.iloc[0]
    
    # Load configurations
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    # Transform the order
    transformed = transform_order_data(first_order, mapping_config, customer_lookup)
    
    # Focus on ORDER STATUS field
    order_status = transformed['ORDER STATUS']
    print(f"\n📊 ORDER STATUS field details:")
    print(f"   Value: '{order_status['value']}'")
    print(f"   Column ID: {order_status['column_id']}")
    print(f"   Type: {order_status['type']}")
    print(f"   Source field: {order_status['source_field']}")
    
    # Show how we're currently formatting it
    current_format = order_status['value']  # This is what we're currently doing
    print(f"\n🔧 Current formatting: {current_format}")
    
    # Show the correct format for status columns
    correct_format = {"labels": [order_status['value']]}
    print(f"🎯 Correct formatting for status: {correct_format}")
    
    # Check all fields and their types
    print(f"\n📋 All transformed fields by type:")
    field_types = {}
    for field_name, field_data in transformed.items():
        field_type = field_data.get('type', 'unknown')
        if field_type not in field_types:
            field_types[field_type] = []
        field_types[field_type].append(field_name)
    
    for type_name, fields in field_types.items():
        print(f"   {type_name}: {len(fields)} fields - {fields[:3]}{'...' if len(fields) > 3 else ''}")
    
    return True

if __name__ == "__main__":
    debug_column_values()
