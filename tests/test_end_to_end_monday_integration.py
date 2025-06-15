"""
Final End-to-End Monday.com Integration Test
With correct Board ID and fixed value mapping
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from customer_master_schedule.order_queries import get_new_orders_from_unified
from customer_master_schedule.order_mapping import transform_order_data, load_mapping_config, load_customer_mapping
from customer_master_schedule.monday_integration import create_monday_item, ensure_group_exists
from customer_master_schedule.add_order import determine_group_name

def format_monday_column_values(transformed_data: dict) -> dict:
    """
    Format transformed data into proper Monday.com column_values structure
    """
    column_values = {}
    
    for field_name, field_data in transformed_data.items():
        if isinstance(field_data, dict) and 'column_id' in field_data:
            column_id = field_data['column_id']
            value = field_data['value']  # Already transformed (ACTIVE → RECEIVED)
            field_type = field_data.get('type', 'text')
            
            if not value or value == '':
                continue
                
            # Format based on Monday.com column type
            if field_type == 'dropdown':
                column_values[column_id] = {"labels": [str(value)]}
            elif field_type == 'status':
                # Status uses simple string value (already transformed to "RECEIVED")
                column_values[column_id] = str(value)
            elif field_type == 'date':
                column_values[column_id] = str(value)
            elif field_type in ['text', 'long_text', 'email', 'phone']:
                column_values[column_id] = str(value)
            elif field_type in ['numbers', 'numeric']:
                column_values[column_id] = str(value)
            else:
                column_values[column_id] = str(value)
    
    return column_values

def test_final_end_to_end_workflow():
    """Test the complete end-to-end workflow with correct Board ID"""
    print('=== FINAL End-to-End Monday.com Integration Test ===')
    
    try:
        # Step 1: Get new orders
        print('\n📋 Step 1: Getting new orders...')
        new_orders = get_new_orders_from_unified(limit=1)
        print(f'Found {len(new_orders)} new orders')
        
        if new_orders.empty:
            print('No new orders to process')
            return
        
        # Step 2: Load configurations
        print('\n⚙️ Step 2: Loading configurations...')
        config = load_mapping_config()
        customer_lookup = load_customer_mapping()
        print('✅ Configurations loaded')
        
        # Step 3: Process first order
        first_order = new_orders.iloc[0].to_dict()
        customer_name = first_order.get('CUSTOMER NAME', 'Unknown')
        aag_order = first_order.get('AAG ORDER NUMBER', 'Unknown')
        original_order_type = first_order.get('ORDER TYPE', 'Unknown')
        
        print(f'\n🔄 Step 3: Processing order...')
        print(f'   Customer: {customer_name}')
        print(f'   Order: {aag_order}')
        print(f'   Original ORDER TYPE: "{original_order_type}"')
        
        # Transform the order data
        transformed = transform_order_data(first_order, config, customer_lookup)
        
        # Verify the ORDER STATUS transformation
        order_status_data = transformed.get('ORDER STATUS')
        if order_status_data:
            transformed_value = order_status_data.get('value')
            print(f'   Transformed ORDER STATUS: "{transformed_value}" ✅')
        
        # Step 4: Format for Monday.com API
        print(f'\n🔧 Step 4: Formatting for Monday.com API...')
        column_values = format_monday_column_values(transformed)
        
        # Verify final ORDER STATUS value for API
        final_order_status = column_values.get('color_mkr5j5pp')
        print(f'   Final ORDER STATUS for API: "{final_order_status}"')
        print(f'   Total column values: {len(column_values)}')
        
        # Step 5: Determine and ensure group exists
        print(f'\n📁 Step 5: Managing Monday.com group...')
        group_name = determine_group_name(first_order)
        print(f'   Group name: "{group_name}"')
        
        board_id = "9200517329"  # Correct Board ID
        group_id = ensure_group_exists(board_id, group_name)
        print(f'   ✅ Group ensured - ID: {group_id}')
        
        # Step 6: Create Monday.com item
        print(f'\n📝 Step 6: Creating Monday.com item...')
        item_name = f"{aag_order} - {customer_name}"
        
        print(f'   Item name: "{item_name}"')
        print(f'   Board ID: {board_id}')
        print(f'   Group ID: {group_id}')
        print(f'   ORDER STATUS value: "{final_order_status}"')
        
        item_id = create_monday_item(
            board_id=board_id,
            group_id=group_id,
            item_name=item_name,
            column_values=column_values,
            create_labels_if_missing=True
        )
        
        print(f'✅ SUCCESS! Created Monday.com item: {item_id}')
        print(f'🎉 End-to-end workflow completed successfully!')
        
        return {
            'item_id': item_id,
            'item_name': item_name,
            'group_name': group_name,
            'order_status': final_order_status,
            'customer': customer_name,
            'aag_order': aag_order
        }
        
    except Exception as e:
        print(f'❌ Error in end-to-end workflow: {e}')
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    result = test_final_end_to_end_workflow()
    if result:
        print(f'\n🎯 FINAL RESULT:')
        print(f'   Monday.com Item ID: {result["item_id"]}')
        print(f'   Item Name: {result["item_name"]}')
        print(f'   Group: {result["group_name"]}')
        print(f'   ORDER STATUS: {result["order_status"]}')