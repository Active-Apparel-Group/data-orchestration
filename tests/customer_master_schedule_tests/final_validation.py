#!/usr/bin/env python3
"""
Final Workflow Validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import transform_order_data, load_mapping_config, load_customer_mapping, get_monday_column_values_dict

def final_validation():
    print("🎉 FINAL WORKFLOW VALIDATION")
    print("=" * 50)
    
    try:
        # Get sample order
        orders = get_new_orders_from_unified(limit=1)
        if orders.empty:
            print("❌ No orders found")
            return False
            
        order = orders.iloc[0]
        order_number = order['AAG ORDER NUMBER']
        print(f"✅ Testing with order: {order_number}")
        
        # Load configuration
        mapping_config = load_mapping_config()
        customer_lookup = load_customer_mapping()
        print("✅ Configuration loaded")
        
        # Transform order
        transformed = transform_order_data(order, mapping_config, customer_lookup)
        print(f"✅ Order transformed: {len(transformed)} fields")
        
        # Check Title field (computed field)
        title = transformed.get('Title', {}).get('value', 'NOT FOUND')
        if title and title != 'NOT FOUND':
            print(f"✅ Title field: {title[:50]}...")
        else:
            print(f"❌ Title field missing: {title}")
            return False
        
        # Get Monday.com column values
        monday_values = get_monday_column_values_dict(transformed)
        print(f"✅ Monday.com column values: {len(monday_values)} fields")
        
        # Success criteria
        success_criteria = [
            len(transformed) >= 40,  # Should have many fields
            len(monday_values) >= 30,  # Should have many with column_ids
            title and title != 'NOT FOUND',  # Title should exist
            'TOTAL QTY' in transformed,  # TOTAL QTY should be mapped
        ]
        
        all_passed = all(success_criteria)
        
        print(f"\n📊 SUCCESS CRITERIA:")
        print(f"  - Total fields (≥40): {len(transformed)} {'✅' if success_criteria[0] else '❌'}")
        print(f"  - Monday.com fields (≥30): {len(monday_values)} {'✅' if success_criteria[1] else '❌'}")
        print(f"  - Title field exists: {'✅' if success_criteria[2] else '❌'}")
        print(f"  - TOTAL QTY mapped: {'✅' if success_criteria[3] else '❌'}")
        
        if all_passed:
            print(f"\n🎉 WORKFLOW VALIDATION: PASSED")
            print("   All core functionality restored and working!")
            return True
        else:
            print(f"\n❌ WORKFLOW VALIDATION: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = final_validation()
    exit(0 if success else 1)
