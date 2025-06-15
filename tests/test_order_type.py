"""
Test to verify ORDER TYPE transformation fix
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import transform_order_data, load_mapping_config, load_customer_mapping

def test_verify_order_type_fix():
    """Test ORDER TYPE transformation after fix"""
    print('=== Testing ORDER TYPE Transformation Fix ===')
    
    # Get sample order
    new_orders = get_new_orders_from_unified(limit=1)
    first_order = new_orders.iloc[0].to_dict()
    
    config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    print(f'Original ORDER TYPE: "{first_order.get("ORDER TYPE")}"')
    
    # Transform data
    transformed = transform_order_data(first_order, config, customer_lookup)
    
    # Check ORDER TYPE result
    order_type_result = transformed.get('ORDER TYPE')
    if order_type_result:
        final_value = order_type_result.get('value')
        column_id = order_type_result.get('column_id')
        field_type = order_type_result.get('type')
        
        print(f'Transformed ORDER TYPE:')
        print(f'  Value: "{final_value}"')
        print(f'  Column ID: {column_id}')
        print(f'  Type: {field_type}')
        
        if final_value == "RECEIVED":
            print(f'✅ SUCCESS: ORDER TYPE correctly transformed to "RECEIVED"')
        elif final_value == "ACTIVE":
            print(f'❌ FAILED: ORDER TYPE not transformed (still "ACTIVE")')
        elif final_value == "":
            print(f'❌ FAILED: ORDER TYPE is empty')
        else:
            print(f'⚠️  UNEXPECTED: ORDER TYPE value is "{final_value}"')
    else:
        print(f'❌ FAILED: ORDER TYPE not found in transformed data')

if __name__ == "__main__":
    test_verify_order_type_fix()