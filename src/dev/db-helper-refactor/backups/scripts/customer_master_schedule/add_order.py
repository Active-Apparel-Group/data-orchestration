"""
Add Order to Monday.com Customer Master Schedule Board (Refactored)

This script implements the modular workflow for adding new orders from ORDERS_UNIFIED
to the Monday.com Customer Master Schedule board through the MON_CustMasterSchedule staging table.

Refactored Workflow:
1. Identify new records in ORDERS_UNIFIED not in MON_CustMasterSchedule
2. Transform data using orders_unified_monday_mapping.yaml
3. Insert into MON_CustMasterSchedule (MONDAY_ITEM_ID blank)
4. Create item in Monday.com, receive item_id
5. Update MONDAY_ITEM_ID in the staging table

Dependencies:
- order_queries: Database operations
- order_mapping: Data transformation using YAML mapping
- monday_integration: Monday.com API operations
"""

import os
import sys
import logging
import warnings
from datetime import datetime
from typing import Dict, List, Optional
from tqdm import tqdm

# Add project modules to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

# Import our new modular components
from .order_queries import (
    get_new_orders_for_monday,
    insert_orders_to_staging,
    update_monday_item_id,
    get_orders_pending_monday_sync
)
from customer_master_schedule.order_mapping import (
    load_mapping_config,
    transform_order_data,
    format_monday_column_values,
    load_customer_mapping,  # ✅ ADDED: Import the missing function
    create_staging_dataframe  # ✅ ADDED: Import the new function
)
from .monday_integration import (
    create_monday_item,
    ensure_group_exists,
    get_board_info,
    batch_create_items,
    setup_logging
)

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# Configuration
CUSTOMER_MASTER_SCHEDULE_BOARD_ID = os.getenv('MONDAY_CUSTOMER_MASTER_SCHEDULE_BOARD_ID', '9200517329')

def setup_application_logging():
    """Setup logging for the application with Unicode support"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup basic logging - FIXED for Unicode
    log_file = os.path.join(log_dir, 'add_order.log')
    
    # Custom formatter without emojis for console
    class ConsoleFormatter(logging.Formatter):
        def format(self, record):
            # Remove emojis for console output
            msg = super().format(record)            # Replace common emojis with text
            replacements = {
                '🔍': '[SEARCH]',
                '🔄': '[SYNC]', 
                'ℹ️': '[INFO]',
                '✅': '[SUCCESS]',
                '❌': '[ERROR]',
                '⚠️': '[WARNING]',
                '📊': '[STATS]',
                '💾': '[SAVE]',
                '📋': '[BOARD]',
                '⏱️': '[TIME]'
            }
            for emoji, text in replacements.items():
                msg = msg.replace(emoji, text)
            return msg
    
    # File handler (can handle Unicode)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Console handler (Unicode-safe)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConsoleFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Setup logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def determine_group_name(order_data: Dict) -> str:
    """
    Determine the appropriate group name for an order
    Group naming rule: {CUSTOMER NAME} {CUSTOMER SEASON}
    
    Args:
        order_data: Transformed order data dictionary
        
    Returns:
        Group name string (e.g., "MACK WELDON FALL 2025")
    """
    # Get customer name and customer season
    customer_name = order_data.get('CUSTOMER NAME', order_data.get('CUSTOMER', 'UNKNOWN CUSTOMER')).strip()
    customer_season = order_data.get('CUSTOMER SEASON', 'UNKNOWN SEASON').strip()
    
    # Handle missing data
    if not customer_name:
        customer_name = 'UNKNOWN CUSTOMER'
    if not customer_season:
        customer_season = 'UNKNOWN SEASON'
    
    # Group name format: CUSTOMER NAME + space + CUSTOMER SEASON
    return f"{customer_name} {customer_season}"

def process_new_orders(logger: logging.Logger) -> Dict[str, int]:
    """
    Step 1: Process new orders from ORDERS_UNIFIED to staging table
    
    Returns:
        Dict with processing statistics
    """
    logger.info("🔍 Step 1: Identifying new orders from ORDERS_UNIFIED...")
    
    # Get new orders that need to be processed
    new_orders_df = get_new_orders_for_monday()
    
    if new_orders_df.empty:
        logger.info("ℹ️ No new orders found to process")
        return {"new_orders_found": 0, "orders_staged": 0}
    
    logger.info(f"📊 Found {len(new_orders_df)} new orders to process")
    
    # Load mapping configuration AND customer mapping - FIXED
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()  # ✅ ADDED: Load customer mapping
    
    if not mapping_config:
        raise Exception("Failed to load mapping configuration")
    
    if not customer_lookup:  # ✅ ADDED: Check customer mapping
        raise Exception("Failed to load customer mapping")
    
    logger.info(f"✅ Loaded configurations: {len(customer_lookup)} customer variants")  # ✅ ADDED: Log success
    
    # Transform and stage orders
    staged_orders = []
    transform_errors = 0
    
    logger.info("🔄 Step 2: Transforming and staging orders...")
    
    for _, order_row in tqdm(new_orders_df.iterrows(), total=len(new_orders_df), desc="Transforming orders"):
        try:
            # Transform order data using YAML mapping - FIXED: Added customer_lookup parameter
            transformed_data = transform_order_data(order_row, mapping_config, customer_lookup)  # ✅ FIXED
            staged_orders.append(transformed_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to transform order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
            transform_errors += 1
    
    if not staged_orders:
        logger.warning("⚠️ No orders successfully transformed")
        return {"new_orders_found": len(new_orders_df), "orders_staged": 0, "transform_errors": transform_errors}
      # Insert into staging table
    logger.info(f"💾 Step 3: Inserting {len(staged_orders)} orders into MON_CustMasterSchedule...")
    
    try:
        # Convert transformed data to DataFrame with flattened scalar values
        staging_df = create_staging_dataframe(staged_orders)
        insert_result = insert_orders_to_staging(staging_df)
        logger.info(f"✅ Successfully staged {len(staged_orders)} orders")
        
        return {
            "new_orders_found": len(new_orders_df),
            "orders_staged": len(staged_orders),
            "transform_errors": transform_errors,
            "insert_result": insert_result
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to insert orders to staging table: {e}")
        raise

def sync_orders_to_monday(logger: logging.Logger) -> Dict[str, int]:
    """
    Step 4: Sync staged orders to Monday.com and update item IDs
    
    Returns:
        Dict with sync statistics
    """
    logger.info("🔄 Step 4: Syncing staged orders to Monday.com...")
    
    # Get orders pending Monday.com sync
    pending_orders_df = get_orders_pending_monday_sync()
    
    if pending_orders_df.empty:
        logger.info("ℹ️ No orders pending Monday.com sync")
        return {"orders_pending": 0, "orders_synced": 0, "sync_errors": 0}
    
    logger.info(f"📊 Found {len(pending_orders_df)} orders pending Monday.com sync")
    
    # Get board info to validate board exists
    try:
        board_info = get_board_info(CUSTOMER_MASTER_SCHEDULE_BOARD_ID)
        logger.info(f"📋 Target board: {board_info['name']} (ID: {CUSTOMER_MASTER_SCHEDULE_BOARD_ID})")
    except Exception as e:
        logger.error(f"❌ Failed to get board info: {e}")
        raise
    
    # Load mapping config for column formatting
    mapping_config = load_mapping_config()
    
    sync_success = 0
    sync_errors = 0
    
    # Process each order
    for _, order_row in tqdm(pending_orders_df.iterrows(), total=len(pending_orders_df), desc="Syncing to Monday.com"):
        try:
            # Determine group for this order
            group_name = determine_group_name(order_row.to_dict())
            
            # Ensure group exists
            group_id = ensure_group_exists(CUSTOMER_MASTER_SCHEDULE_BOARD_ID, group_name)
            if not group_id:
                logger.error(f"❌ Failed to ensure group exists: {group_name}")
                sync_errors += 1
                continue
            
            # Create item name
            item_name = order_row.get('ITEM_NAME', f"Order {order_row.get('AAG ORDER NUMBER', 'Unknown')}")
            
            # Format column values for Monday.com
            column_values_json = order_row.get('COLUMN_VALUES', '{}')
            try:
                import json
                column_values = json.loads(column_values_json) if column_values_json else {}
            except:
                logger.warning(f"⚠️ Invalid column values JSON for order {order_row.get('AAG ORDER NUMBER')}, using empty dict")
                column_values = {}
            
            # Create item in Monday.com
            item_id = create_monday_item(
                board_id=CUSTOMER_MASTER_SCHEDULE_BOARD_ID,
                group_id=group_id,
                item_name=item_name,
                column_values=column_values
            )
              # Update database with Monday.com item ID
            update_success = update_monday_item_id(
                order_row['AAG ORDER NUMBER'],
                order_row['STYLE'],  # Fixed: was 'CUSTOMER STYLE', now 'STYLE'
                order_row['COLOR'],
                item_id
            )
            
            if update_success:
                sync_success += 1
                logger.debug(f"✅ Synced order {order_row['AAG ORDER NUMBER']} -> Monday.com item {item_id}")
            else:
                logger.error(f"❌ Failed to update database with item ID for order {order_row['AAG ORDER NUMBER']}")
                sync_errors += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to sync order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
            sync_errors += 1
    
    return {
        "orders_pending": len(pending_orders_df),
        "orders_synced": sync_success,
        "sync_errors": sync_errors
    }

def main():
    """
    Main execution function implementing the complete modular workflow
    """
    logger = setup_application_logging()
    
    print("=" * 80)
    print("🚀 Customer Master Schedule - Add Orders Workflow")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
        # Step 1-3: Process new orders from ORDERS_UNIFIED to staging
        processing_stats = process_new_orders(logger)
        
        # Step 4-5: Sync staged orders to Monday.com and update item IDs
        sync_stats = sync_orders_to_monday(logger)
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("📊 WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total Duration: {duration}")
        print(f"🔍 New Orders Found: {processing_stats.get('new_orders_found', 0)}")
        print(f"💾 Orders Staged: {processing_stats.get('orders_staged', 0)}")
        print(f"🔄 Orders Synced to Monday.com: {sync_stats.get('orders_synced', 0)}")
        print(f"❌ Transform Errors: {processing_stats.get('transform_errors', 0)}")
        print(f"❌ Sync Errors: {sync_stats.get('sync_errors', 0)}")
        
        # Log summary
        logger.info(f"Workflow completed in {duration}")
        logger.info(f"Summary: {processing_stats.get('orders_staged', 0)} staged, {sync_stats.get('orders_synced', 0)} synced")
        
        if sync_stats.get('sync_errors', 0) > 0 or processing_stats.get('transform_errors', 0) > 0:
            print("⚠️  Some errors occurred. Check logs for details.")
            return 1
        else:
            print("✅ Workflow completed successfully!")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        print(f"❌ Workflow failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
