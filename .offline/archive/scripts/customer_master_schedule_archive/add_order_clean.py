"""
Clean Add Order to Monday.com - Step by Step

Minimal, focused implementation:
1. Determine group name
2. Process new orders
3. Sync to Monday.com

No excessive logging, no emojis, no debugging noise.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add project modules to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

# Import our modules
from customer_master_schedule.order_queries import (
    get_new_orders_for_monday,
    insert_orders_to_staging,
    get_orders_pending_monday_sync,
    update_monday_item_id
)
from customer_master_schedule.order_mapping import (
    load_mapping_config,
    transform_order_data,
    load_customer_mapping,
    create_staging_dataframe
)
from customer_master_schedule.monday_integration import (
    create_monday_item,
    ensure_group_exists,
    get_board_info
)

# Configuration
CUSTOMER_MASTER_SCHEDULE_BOARD_ID = os.getenv('MONDAY_CUSTOMER_MASTER_SCHEDULE_BOARD_ID', '9200517329')

def determine_group_name(order_data: Dict) -> str:
    """
    Determine group name: {CUSTOMER NAME} {CUSTOMER SEASON}
    """
    customer_name = order_data.get('Customer', 'UNKNOWN CUSTOMER').strip()
    customer_season = order_data.get('Season', 'UNKNOWN SEASON').strip()
    
    if not customer_name:
        customer_name = 'UNKNOWN CUSTOMER'
    if not customer_season:
        customer_season = 'UNKNOWN SEASON'
    
    return f"{customer_name} {customer_season}"

def create_item_name(order_row) -> str:
    """
    Create item name: STYLE + space + COLOR + space + AAG ORDER NUMBER
    """
    style = str(order_row.get('Style', '')).strip()
    color = str(order_row.get('Color', '')).strip()
    order_number = str(order_row.get('Order_Number', '')).strip()
    
    return f"{style} {color} {order_number}"

def process_new_orders() -> Dict[str, int]:
    """
    Step 1: Process new orders from ORDERS_UNIFIED to staging table
    """
    print("Step 1: Processing new orders...")
    
    # Get new orders
    new_orders_df = get_new_orders_for_monday()
    
    if new_orders_df.empty:
        print("No new orders found")
        return {"new_orders_found": 0, "orders_staged": 0}
    
    print(f"Found {len(new_orders_df)} new orders")
    
    # Load configurations
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    if not mapping_config or not customer_lookup:
        raise Exception("Failed to load configurations")
    
    # Transform orders
    staged_orders = []
    for _, order_row in new_orders_df.iterrows():
        try:
            transformed_data = transform_order_data(order_row, mapping_config, customer_lookup)
            staged_orders.append(transformed_data)
        except Exception as e:
            print(f"Transform error for order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
    
    if not staged_orders:
        print("No orders successfully transformed")
        return {"new_orders_found": len(new_orders_df), "orders_staged": 0}
    
    # Insert to staging
    staging_df = create_staging_dataframe(staged_orders)
    insert_result = insert_orders_to_staging(staging_df)
    
    if insert_result:
        print(f"Successfully staged {len(staged_orders)} orders")
    
    return {
        "new_orders_found": len(new_orders_df),
        "orders_staged": len(staged_orders) if insert_result else 0
    }

def sync_orders_to_monday() -> Dict[str, int]:
    """
    Step 2: Sync staged orders to Monday.com and update item IDs
    """
    print("Step 2: Syncing to Monday.com...")
    
    # Get pending orders
    pending_orders_df = get_orders_pending_monday_sync()
    
    if pending_orders_df.empty:
        print("No orders pending sync")
        return {"orders_pending": 0, "orders_synced": 0, "sync_errors": 0}
    
    print(f"Found {len(pending_orders_df)} orders pending sync")
    
    # Validate board exists
    try:
        board_info = get_board_info(CUSTOMER_MASTER_SCHEDULE_BOARD_ID)
        print(f"Target board: {board_info['name']}")
    except Exception as e:
        print(f"Board validation failed: {e}")
        raise
    
    sync_success = 0
    sync_errors = 0
    
    # Process each order
    for _, order_row in pending_orders_df.iterrows():
        try:
            # Determine group
            group_name = determine_group_name(order_row.to_dict())
            group_id = ensure_group_exists(CUSTOMER_MASTER_SCHEDULE_BOARD_ID, group_name)
            
            if not group_id:
                print(f"Failed to ensure group exists: {group_name}")
                sync_errors += 1
                continue
            
            # Create item name - FIXED LOGIC
            item_name = create_item_name(order_row)
            
            # Get column values
            column_values_json = order_row.get('COLUMN_VALUES', '{}')
            try:
                column_values = json.loads(column_values_json) if column_values_json else {}
            except:
                print(f"Invalid column values for order {order_row.get('Order_Number', 'Unknown')}")
                column_values = {}
            
            # Create Monday.com item
            monday_item_id = create_monday_item(
                board_id=CUSTOMER_MASTER_SCHEDULE_BOARD_ID,
                group_id=group_id,
                item_name=item_name,
                column_values=column_values
            )
            
            # Update database with Monday.com item ID using staging ID
            staging_id = str(order_row['Item ID'])  # This is our 1000+ staging ID
            update_success = update_monday_item_id(staging_id, monday_item_id)
            
            if update_success:
                sync_success += 1
                print(f"Synced: staging ID {staging_id} -> Monday.com item {monday_item_id}")
            else:
                print(f"Failed to update database for staging ID {staging_id}")
                sync_errors += 1
                
        except Exception as e:
            print(f"Sync error for order {order_row.get('Order_Number', 'Unknown')}: {e}")
            sync_errors += 1
    
    return {
        "orders_pending": len(pending_orders_df),
        "orders_synced": sync_success,
        "sync_errors": sync_errors
    }

def main():
    """
    Main execution - step by step
    """
    print("=" * 60)
    print("Customer Master Schedule - Clean Add Orders")
    print("=" * 60)
    
    try:
        # Step 1: Process new orders
        processing_stats = process_new_orders()
        
        # Step 2: Sync to Monday.com
        sync_stats = sync_orders_to_monday()
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"New Orders Found: {processing_stats.get('new_orders_found', 0)}")
        print(f"Orders Staged: {processing_stats.get('orders_staged', 0)}")
        print(f"Orders Synced: {sync_stats.get('orders_synced', 0)}")
        print(f"Sync Errors: {sync_stats.get('sync_errors', 0)}")
        
        if sync_stats.get('sync_errors', 0) > 0:
            print("Some errors occurred - check output above")
            return 1
        else:
            print("Workflow completed successfully")
            return 0
            
    except Exception as e:
        print(f"Workflow failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
