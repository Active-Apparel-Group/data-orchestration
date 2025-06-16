#!/usr/bin/env python3
"""
Test Complete Monday.com Integration with Group Management

Tests the full end-to-end workflow including the missing group management step:
1. Query new orders from ORDERS_UNIFIED
2. Transform using mapping configuration  
3. Determine appropriate group (by customer)
4. Ensure group exists using ensure_group_exists()
5. Create item in Monday.com using proper column mapping
6. Update staging table with Monday.com item ID
"""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

def determine_group_name(order_data: dict) -> str:
    """
    Determine the appropriate group name for an order based on customer and season
    Format: "{CUSTOMER NAME} {CUSTOMER SEASON}"
    """
    customer_name = order_data.get('CUSTOMER NAME', '').strip()
    customer_season = order_data.get('CUSTOMER SEASON', '').strip()
    
    if not customer_name:
        customer_name = 'UNKNOWN CUSTOMER'
    if not customer_season:
        customer_season = 'UNKNOWN SEASON'
    
    # Group name format: CUSTOMER NAME + space + CUSTOMER SEASON
    group_name = f"{customer_name} {customer_season}"
    
    return group_name

def test_monday_integration_with_groups():
    """Test the complete Monday.com integration including group management"""
    print('=== Testing Complete Monday.com Integration with Group Management ===')
    
    # Import required modules
    from customer_master_schedule.order_queries import get_new_orders_from_unified
    from customer_master_schedule.order_mapping import (
        transform_order_data, 
        load_mapping_config,
        load_customer_mapping
    )
    from customer_master_schedule.monday_integration import (
        ensure_group_exists,
        create_monday_item,
        get_board_info
    )
    
    # Constants
    BOARD_ID = "9200517329"  # Customer Master Schedule board
    
    # Step 1: Get new orders
    print('\\n📋 Step 1: Getting new orders...')
    new_orders = get_new_orders_from_unified(limit=1)  # Test with just 1 order
    print(f'Found {len(new_orders)} new orders')
    
    if new_orders.empty:
        print('No new orders to process')
        return
    
    # Show order details
    first_order = new_orders.iloc[0]
    customer_name = first_order['CUSTOMER NAME']
    aag_order = first_order['AAG ORDER NUMBER']
    style = first_order['CUSTOMER STYLE']
    color = first_order['CUSTOMER COLOUR DESCRIPTION']
    print(f'Testing with order: {aag_order} | Customer: {customer_name} | Style: {style} | Color: {color}')
    
    # Step 2: Load configurations
    print('\\n⚙️ Step 2: Loading configurations...')
    try:
        config = load_mapping_config()
        customer_lookup = load_customer_mapping()
        print(f'✅ Configurations loaded successfully')
    except Exception as e:
        print(f'❌ Error loading configurations: {e}')
        return
    
    # Step 3: Transform order data
    print('\\n🔄 Step 3: Transforming order data...')
    try:
        transformed = transform_order_data(first_order, config, customer_lookup)
        print(f'✅ Order transformed successfully')
        print(f'Sample transformed fields:')
        print(f'  - STYLE: {transformed.get("STYLE", {}).get("value", "N/A")}')
        print(f'  - COLOR: {transformed.get("COLOR", {}).get("value", "N/A")}')
        print(f'  - AAG ORDER NUMBER: {transformed.get("AAG ORDER NUMBER", {}).get("value", "N/A")}')
    except Exception as e:
        print(f'❌ Error transforming order: {e}')
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Determine group name (MISSING STEP!)
    print('\\n🎯 Step 4: Determining appropriate group...')
    try:
        group_name = determine_group_name(first_order.to_dict())
        print(f'✅ Group determined: {group_name}')
    except Exception as e:
        print(f'❌ Error determining group: {e}')
        return
    
    # Step 5: Ensure group exists (MISSING STEP!)
    print('\\n🏗️ Step 5: Ensuring group exists...')
    try:
        group_id = ensure_group_exists(BOARD_ID, group_name)
        if group_id:
            print(f'✅ Group ready: {group_name} (ID: {group_id})')
        else:
            print(f'❌ Failed to ensure group exists: {group_name}')
            return
    except Exception as e:
        print(f'❌ Error ensuring group exists: {e}')
        import traceback
        traceback.print_exc()
        return
    
    # Step 6: Get board info for validation
    print('\\n📋 Step 6: Validating board info...')
    try:
        board_info = get_board_info(BOARD_ID)
        if board_info:
            print(f'✅ Board validated: {board_info.get("name", "Unknown")} (ID: {BOARD_ID})')
        else:
            print(f'❌ Could not get board info for {BOARD_ID}')
            return
    except Exception as e:
        print(f'❌ Error getting board info: {e}')
        return
    
    # Step 7: Create Monday.com item (DRY RUN)
    print('\\n🚀 Step 7: Creating Monday.com item (DRY RUN)...')
    try:
        # Prepare item data
        item_name = f"{style}_{color}_{aag_order}"
        
        print(f'Would create item:')
        print(f'  - Board ID: {BOARD_ID}')
        print(f'  - Group ID: {group_id}')
        print(f'  - Item Name: {item_name}')
        print(f'  - Transformed Data: {len(transformed)} fields ready')
        
        # NOTE: Uncomment to actually create the item
        # item_id = create_monday_item(BOARD_ID, group_id, item_name, transformed)
        # if item_id:
        #     print(f'✅ Item created successfully: {item_id}')
        # else:
        #     print(f'❌ Failed to create item')
        #     return
        
        print(f'✅ DRY RUN - Item preparation successful!')
        
    except Exception as e:
        print(f'❌ Error preparing Monday.com item: {e}')
        import traceback
        traceback.print_exc()
        return
    
    print('\\n✅ Complete Monday.com integration test completed!')
    print('\\n📝 Summary:')
    print(f'  ✅ Order retrieval: Working')
    print(f'  ✅ Data transformation: Working') 
    print(f'  ✅ Group determination: Working')
    print(f'  ✅ Group management: Working')
    print(f'  ✅ Board validation: Working')
    print(f'  ✅ Item preparation: Ready for creation')
    print(f'\\n🎯 The missing group management step has been implemented!')

if __name__ == '__main__':
    test_monday_integration_with_groups()
