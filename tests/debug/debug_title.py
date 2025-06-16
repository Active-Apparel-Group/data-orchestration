#!/usr/bin/env python3
"""
Debug Title Field Issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import transform_order_data, load_mapping_config, load_customer_mapping

def debug_title_field():
    print("🔍 DEBUG: Title Field Generation")
    print("=" * 50)
    
    # Step 1: Get orders
    print("Step 1: Getting orders...")
    orders = get_new_orders_from_unified(limit=1)
    if orders.empty:
        print("❌ No orders found")
        return
    
    order = orders.iloc[0]
    print(f"✅ Got order: {order.get('AAG ORDER NUMBER', 'N/A')}")
    
    # Step 2: Load config
    print("\nStep 2: Loading config...")
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    print(f"✅ Config loaded: {len(mapping_config.get('computed_fields', []))} computed fields")
    
    # Step 3: Check computed fields in YAML
    computed_fields = mapping_config.get('computed_fields', [])
    print(f"\nStep 3: Computed fields in YAML:")
    for field in computed_fields:
        print(f"  - {field}")
    
    # Step 4: Transform order
    print("\nStep 4: Transforming order...")
    transformed = transform_order_data(order, mapping_config, customer_lookup)
    
    # Step 5: Check Title field specifically
    print(f"\nStep 5: Title field analysis:")
    title_field = transformed.get('Title', {})
    print(f"  Title field exists: {'Title' in transformed}")
    print(f"  Title field content: {title_field}")
    
    if isinstance(title_field, dict):
        print(f"  Title value: {title_field.get('value', 'NO VALUE')}")
        print(f"  Title column_id: {title_field.get('column_id', 'NO COLUMN_ID')}")
    
    # Step 6: Check raw order data for Title components
    print(f"\nStep 6: Raw order data for Title components:")
    print(f"  CUSTOMER STYLE: {order.get('CUSTOMER STYLE', 'N/A')}")
    print(f"  CUSTOMER COLOUR DESCRIPTION: {order.get('CUSTOMER COLOUR DESCRIPTION', 'N/A')}")
    print(f"  AAG ORDER NUMBER: {order.get('AAG ORDER NUMBER', 'N/A')}")
    
    # Step 7: Check if computed fields were processed
    print(f"\nStep 7: All transformed fields:")
    for i, (key, value) in enumerate(transformed.items()):
        if i < 10:  # Show first 10
            val_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {key}: {val_preview}")
    
    print(f"\nTotal fields: {len(transformed)}")
    print("🔍 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_title_field()
