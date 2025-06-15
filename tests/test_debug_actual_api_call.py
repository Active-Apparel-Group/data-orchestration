"""
Debug what's actually being sent to the Monday.com API
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import transform_order_data, load_mapping_config, load_customer_mapping
import json

def debug_actual_api_call():
    """Debug what column_values are actually being sent to Monday.com API"""
    print('=== Debugging Actual API Call ===')
    
    # Get and transform order
    new_orders = get_new_orders_from_unified(limit=1)
    first_order = new_orders.iloc[0].to_dict()
    
    config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    print(f'Original ORDER TYPE: "{first_order.get("ORDER TYPE")}"')
    
    transformed = transform_order_data(first_order, config, customer_lookup)
    
    # Check what's in the transformed data for ORDER STATUS
    order_status_data = transformed.get('ORDER STATUS')
    print(f'Transformed ORDER STATUS data: {order_status_data}')
    
    # Now let's see what the create_monday_item function would actually send
    # Let's manually build column_values the way create_monday_item expects it
    
    # Check if there's a format_column_values function in monday_integration.py
    try:
        from customer_master_schedule.monday_integration import format_column_values
        print('\nUsing format_column_values from monday_integration.py:')
        column_values = format_column_values(transformed)
        
        order_status_final = column_values.get('color_mkr5j5pp')
        print(f'Final ORDER STATUS from monday_integration: {order_status_final}')
        
    except ImportError:
        print('\nNo format_column_values function found in monday_integration.py')
        print('This means create_monday_item is expecting a different format!')
        
        # Let's see what create_monday_item actually expects
        # Check the actual column_values parameter structure expected
        
        # Manual format - let's see what structure create_monday_item uses
        column_values_manual = {}
        for field_name, field_data in transformed.items():
            if isinstance(field_data, dict) and 'column_id' in field_data:
                column_id = field_data['column_id']
                value = field_data['value']
                field_type = field_data.get('type', 'text')
                
                # This is what we THINK should happen
                if field_type == 'status':
                    column_values_manual[column_id] = str(value)  # Should be "RECEIVED"
                elif field_type == 'dropdown':
                    column_values_manual[column_id] = {"labels": [str(value)]}
                else:
                    column_values_manual[column_id] = str(value)
        
        print(f'Manual column_values ORDER STATUS: {column_values_manual.get("color_mkr5j5pp")}')
    
    # Let's check what JSON would be sent
    print(f'\nFinal JSON that would be sent to API:')
    final_json = json.dumps(column_values_manual if 'column_values_manual' in locals() else column_values)
    print(final_json)
    
    # Look for any ACTIVE values still present
    if 'ACTIVE' in final_json:
        print('\n❌ FOUND "ACTIVE" IN FINAL JSON!')
        print('This explains why the API is receiving ACTIVE instead of RECEIVED')
    else:
        print('\n✅ No "ACTIVE" found in final JSON')

if __name__ == "__main__":
    debug_actual_api_call()