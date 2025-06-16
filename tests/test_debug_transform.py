"""
Debug why 10 orders had transform errors
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import load_mapping_config, transform_order_data, load_customer_mapping

def debug_transform_errors():
    """Debug what's causing the transform errors"""
    print('=== Debugging Transform Errors ===')
    
    # Get the same orders that failed
    new_orders = get_new_orders_from_unified(limit=10)
    
    config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    print(f'Testing transformation of {len(new_orders)} orders...')
    
    for i, (index, order_row) in enumerate(new_orders.iterrows()):
        try:
            aag_order = order_row.get('AAG ORDER NUMBER', f'Order_{i}')
            customer = order_row.get('CUSTOMER NAME', 'Unknown')
            
            print(f'\nOrder {i+1}: {aag_order} - {customer}')
            
            # Try transformation
            transformed = transform_order_data(order_row, config, customer_lookup)
            
            print(f'  ✅ Transformation successful: {len(transformed)} fields')
            
            # Check for ORDER TYPE specifically
            order_type_result = transformed.get('ORDER TYPE')
            if order_type_result:
                print(f'  📋 ORDER TYPE: "{order_type_result.get("value")}" (Column: {order_type_result.get("column_id")})')
            
        except Exception as e:
            print(f'  ❌ Transformation failed: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_transform_errors()