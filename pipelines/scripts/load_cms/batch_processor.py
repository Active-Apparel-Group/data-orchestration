"""
Main batch processor for Monday.com staging workflow
Orchestrates the complete customer batch processing pipeline
"""

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import logging
import warnings
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from .staging_operations import StagingOperations
from .monday_api_client import MondayApiClient
from .error_handler import ErrorHandler
from .staging_config import get_config

# Suppress pandas warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")


# Import existing transformation functions
from customer_master_schedule.order_mapping import (
    transform_orders_batch,
    create_staging_dataframe,
    get_monday_column_values_dict,
    transform_order_data,
    load_mapping_config,
    load_customer_mapping
)

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Main orchestrator for customer batch processing"""
    
    def __init__(self, db_key: str = 'orders'):
        self.db_key = db_key
        self.config = get_config()
        
        # Initialize components with config key (not connection string)
        self.staging_ops = StagingOperations(db_key)
        self.monday_client = MondayApiClient()
        self.error_handler = ErrorHandler(db_key)
        
        # Load mapping configuration once
        self.mapping_config = load_mapping_config()
        self.customer_lookup = load_customer_mapping()

    def cleanup_staging_tables(self) -> Dict[str, int]:
        """
        Clean up staging tables by removing incomplete/failed records.
        This ensures we don't have orphaned or incomplete data from failed jobs.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting staging tables cleanup...")
        results = {
            'orphaned_subitems': 0,
            'failed_subitems': 0,
            'failed_orders': 0
        }
        
        try:
            with self.staging_ops.get_connection() as conn:
                cursor = conn.cursor()
                
                # Step 1: Delete orphaned subitems (SQL Server compatible)
                cursor.execute(
                """
                DELETE FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
                WHERE stg_parent_stg_id IS NOT NULL
                    AND stg_parent_stg_id NOT IN (SELECT stg_id FROM [dbo].[STG_MON_CustMasterSchedule])
                """
                                        )
                results['orphaned_subitems'] = cursor.rowcount
                logger.info(f"Deleted {results['orphaned_subitems']} orphaned subitems")

                # Step 2: Delete failed or incomplete subitems
                cursor.execute("""
                    DELETE FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
                    WHERE stg_status IN ('PENDING', 'API_FAILED')
                        OR stg_monday_subitem_id IS NULL
                """)
                results['failed_subitems'] = cursor.rowcount
                logger.info(f"Deleted {results['failed_subitems']} failed/incomplete subitems")

                # Step 3: Delete failed or incomplete orders
                cursor.execute("""
                    DELETE FROM [dbo].[STG_MON_CustMasterSchedule]
                    WHERE stg_status IN ('PENDING', 'API_FAILED')
                        OR stg_monday_item_id IS NULL
                """)
                results['failed_orders'] = cursor.rowcount
                logger.info(f"Deleted {results['failed_orders']} failed/incomplete orders")
                
                conn.commit()
                
                logger.info(f"Staging tables cleanup completed successfully: {results}")
                return results
                
        except Exception as e:
            logger.error(f"Failed to clean up staging tables: {str(e)}")
            raise
    def get_customers_with_new_orders(self) -> List[str]:
        """Get list of customers with new orders not yet in MON_CustMasterSchedule"""
        
        query = """
        SELECT DISTINCT ou.[CUSTOMER NAME] as customer_name
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
            ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
            -- AND ou.[CUSTOMER NAME] = cms.[CUSTOMER] removed as canonical names won't always match so not needed given AAG order number unique to a customer
            AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
        WHERE cms.[AAG ORDER NUMBER] IS NULL
            AND ou.[AAG ORDER NUMBER] IS NOT NULL
            AND ou.[CUSTOMER STYLE] IS NOT NULL
            AND ou.[CUSTOMER COLOUR DESCRIPTION] IS NOT NULL
        ORDER BY ou.[CUSTOMER NAME]
        """
        
        with self.staging_ops.get_connection() as conn:
            df = pd.read_sql(query, conn)
        
        customers = df['customer_name'].tolist()
        logger.info(f"Found {len(customers)} customers with new orders: {customers}")
        return customers
    def get_new_orders_for_customer(self, customer_name: str) -> pd.DataFrame:
        """Get new orders for a specific customer"""
        
        query = """
        SELECT ou.*
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
            ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
            -- AND ou.[CUSTOMER NAME] = cms.[CUSTOMER] removed as canonical names won't always match so not needed given AAG order number unique to a customer
            AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
        WHERE cms.[AAG ORDER NUMBER] IS NULL
            AND ou.[CUSTOMER NAME] = ?
            AND ou.[AAG ORDER NUMBER] IS NOT NULL
            AND ou.[CUSTOMER STYLE] IS NOT NULL
            AND ou.[CUSTOMER COLOUR DESCRIPTION] IS NOT NULL
        ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
        """
        
        with self.staging_ops.get_connection() as conn:
            df = pd.read_sql(query, conn, params=[customer_name])
        
        logger.info(f"Found {len(df)} new orders for customer {customer_name}")
        return df
    def create_item_name(self, order_row: pd.Series) -> str:
        """Create Monday.com item name using existing logic"""
        # Use the Title field from transformation if available
        title = order_row.get('Title', '')
        if title:
            return str(title).strip()
        
        # Fallback: manual construction using Monday.com target field names
        style = str(order_row.get('STYLE', '')).strip()
        color = str(order_row.get('COLOR', '')).strip()
        order_number = str(order_row.get('AAG ORDER NUMBER', '')).strip()
        
        return f"{style} {color} {order_number}".strip()
    
    def create_group_name(self, order_row: pd.Series) -> str:
        """Create group name using calculated Group field with CUSTOMER SEASON → AAG SEASON fallback"""
        # Use the pre-calculated Group field that has fallback logic
        if 'Group' in order_row and order_row['Group']:
            group_name = str(order_row['Group']).strip()
            if group_name:
                return group_name
        
        # Fallback to manual construction with CUSTOMER SEASON → AAG SEASON fallback
        customer = str(order_row.get('CUSTOMER', '')).strip()
        customer_season = str(order_row.get('CUSTOMER SEASON', '')).strip()
        aag_season = str(order_row.get('AAG SEASON', '')).strip()
        
        # Apply the same fallback logic as in staging_operations
        if not customer_season or customer_season.lower() in ['', 'nan', 'none', 'null']:
            effective_season = aag_season if aag_season else 'UNKNOWN_SEASON'
        else:
            effective_season = customer_season
        
        return f"{customer} {effective_season}".strip()
    
    def ensure_group_exists(self, order_row: pd.Series) -> str:
        """Ensure group exists and return group ID"""
        group_name = self.create_group_name(order_row)
        
        # Use Monday API client to ensure group exists
        success, group_id, error = self.monday_client.ensure_group_exists(group_name)
        
        if not success:
            logger.error(f"Failed to ensure group exists for '{group_name}': {error}")
            # Return a default group ID or raise exception based on your needs
            from .staging_config import MONDAY_CONFIG
            return MONDAY_CONFIG.get('default_group_id', 'topics')  # fallback to default group
        
        return group_id
    
    def ensure_group_exists(self, order_row: pd.Series) -> str:
        """Ensure Monday.com group exists and return group ID"""
        try:
            group_name = self.create_group_name(order_row)
            
            # For now, return a placeholder group ID or use Monday API to create/find group
            # This should call your Monday.com API client to ensure group exists
            # and return the actual group ID
            
            # Placeholder implementation - replace with actual Monday.com API call
            logger.info(f"Ensuring group exists: {group_name}")
            return "placeholder_group_id"  # Replace with actual Monday.com group ID
            
        except Exception as e:
            logger.error(f"Failed to ensure group exists for order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
            return "default_group_id"  # Fallback group ID
    
    def get_monday_column_values_for_staged_order(self, order_row: pd.Series) -> Dict:
        """Get Monday.com column values for staged order data"""
        try:
            if not self.mapping_config:
                logger.warning(f"No mapping config available for order {order_row.get('AAG ORDER NUMBER', 'Unknown')}")
                return {}
            
            # Build column values dictionary by mapping staged column names to Monday.com column IDs
            column_values = {}
            
            # Create a lookup of target_field -> column_id from YAML mapping
            field_to_column_id = {}
            
            # Process exact matches
            for mapping in self.mapping_config.get('exact_matches', []):
                target_field = mapping['target_field']
                target_column_id = mapping['target_column_id']
                target_type = mapping['target_type']
                field_to_column_id[target_field] = {
                    'column_id': target_column_id,
                    'type': target_type
                }
            
            # Process mapped fields
            for mapping in self.mapping_config.get('mapped_fields', []):
                target_field = mapping['target_field']
                target_column_id = mapping['target_column_id']
                target_type = mapping['target_type']
                field_to_column_id[target_field] = {
                    'column_id': target_column_id,
                    'type': target_type
                }
            
            # Map staged data to Monday.com column IDs
            for field_name, mapping_info in field_to_column_id.items():
                column_id = mapping_info['column_id']
                field_type = mapping_info['type']
                
                # Get value from staged data (use the target field name)
                value = order_row.get(field_name)
                
                # Skip if no value or empty
                if value is None or (isinstance(value, str) and not value.strip()):
                    continue
                
                # Format based on Monday.com column type requirements
                if field_type == 'text' or field_type == 'long_text':
                    column_values[column_id] = str(value)
                elif field_type == 'numbers':
                    try:
                        column_values[column_id] = float(value) if value else 0
                    except (ValueError, TypeError):
                        continue
                elif field_type == 'date':
                    if pd.notna(value):
                        column_values[column_id] = str(value)
                elif field_type == 'dropdown' or field_type == 'status':
                    column_values[column_id] = str(value)
                else:
                    column_values[column_id] = str(value)
            
            return column_values
            
        except Exception as e:
            logger.error(f"Error getting Monday.com column values for staged order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
            return {}
    
    def load_new_orders_to_staging(self, customer_name: str, batch_id: str) -> int:
        """Step 1: Load new orders to staging table"""
        
        logger.info(f"Loading new orders for customer {customer_name} to staging...")
        
        # Get new orders for customer
        orders_df = self.get_new_orders_for_customer(customer_name)
        
        if orders_df.empty:
            logger.info(f"No new orders found for customer {customer_name}")
            return 0
        
        # Transform orders using complete YAML mapping
        logger.info(f"Transforming {len(orders_df)} orders using YAML mapping...")
        transformed_df = transform_orders_batch(orders_df)
        
        if transformed_df.empty:
            logger.warning(f"No orders successfully transformed for customer {customer_name}")
            return 0
        
        # Insert to staging
        rows_inserted = self.staging_ops.insert_orders_to_staging(
            transformed_df, customer_name, batch_id
        )
        
        # Update batch status
        self.staging_ops.update_batch_status(
            batch_id, 'STAGING_LOADED', total_records=rows_inserted
        )
        
        return rows_inserted
    
    def create_monday_items_from_staging(self, batch_id: str) -> Tuple[int, int]:
        """Create Monday.com items in batches with robust error handling and optimized group creation"""
        BATCH_SIZE = 20  # Monday.com recommended batch size is 50
        current_batch = []
        batch_stg_ids = []
        success_count = 0
        error_count = 0

        # Get staging records
        staging_records = self.staging_ops.get_pending_staging_orders(batch_id)

        # Cache for group IDs to avoid multiple API calls
        group_cache = {}

        # Use iterrows to get row data
        for idx, record in staging_records.iterrows():
            try:
                # Get group name and ensure group exists (cached)
                group_name = self.create_group_name(record)
                
                # Check cache first
                if group_name not in group_cache:
                    logger.info(f"Ensuring group exists: {group_name}")
                    success, group_id, error = self.monday_client.ensure_group_exists(group_name)
                    if not success:
                        logger.error(f"Failed to ensure group exists for '{group_name}': {error}")
                        # Use fallback group ID
                        from .staging_config import MONDAY_CONFIG
                        group_id = MONDAY_CONFIG.get('default_group_id', 'topics')
                    group_cache[group_name] = group_id
                    logger.debug(f"Cached group '{group_name}' with ID: {group_id}")
                else:
                    group_id = group_cache[group_name]

                item = {
                    "item_name": self.create_item_name(record),
                    "group_id": group_id,
                    "column_values": self.get_monday_column_values_for_staged_order(record),
                    "stg_id": record["stg_id"]  # Add stg_id for tracking
                }
                current_batch.append(item)
                batch_stg_ids.append(record["stg_id"])
            except Exception as e:
                logger.error(f"Failed to build Monday.com item for row {idx}: {e}\nRow data: {record.to_dict()}")
                error_count += 1
                continue

            # Process batch when full
            if len(current_batch) >= BATCH_SIZE:
                try:
                    success, item_ids, error = self.monday_client.create_items_batch(current_batch)
                    if success:
                        # Update staging with item IDs
                        for stg_id, item_id in zip(batch_stg_ids, item_ids):
                            if item_id:  # Only update if item_id is not None
                                self.staging_ops.update_staging_with_monday_id(stg_id, int(item_id))
                        successful_items = sum(1 for item_id in item_ids if item_id is not None)
                        success_count += successful_items
                        failed_items = len(item_ids) - successful_items
                        error_count += failed_items
                    else:
                        error_count += len(current_batch)
                        logger.error(f"Batch creation failed: {error}")
                except Exception as e:
                    error_count += len(current_batch)
                    logger.error(f"Exception during batch creation: {e}")
                current_batch = []
                batch_stg_ids = []

        if current_batch:
            try:
                success, item_ids, error = self.monday_client.create_items_batch(current_batch)
                if success:
                    for stg_id, item_id in zip(batch_stg_ids, item_ids):
                        if item_id:  # Only update if item_id is not None
                            self.staging_ops.update_staging_with_monday_id(stg_id, int(item_id))
                    successful_items = sum(1 for item_id in item_ids if item_id is not None)
                    success_count += successful_items
                    failed_items = len(item_ids) - successful_items
                    error_count += failed_items
                else:
                    error_count += len(current_batch)
                    logger.error(f"Batch creation failed: {error}")
            except Exception as e:
                error_count += len(current_batch)
                logger.error(f"Exception during batch creation: {e}")

        logger.info(f"Group cache summary: {len(group_cache)} unique groups cached: {list(group_cache.keys())}")
        return success_count, error_count
    
    def create_monday_subitems_from_staging(self, batch_id: str) -> Tuple[int, int]:
        """Step 3: Create Monday.com subitems from staging records with parent_item_id (BATCHED)"""
        logger.info(f"Creating Monday.com subitems for batch {batch_id}...")

        # Get subitems that have parent_item_id set (ready for API creation)
        subitem_query = """
            SELECT 
                stg_id as stg_subitem_id,
                stg_parent_stg_id,
                stg_monday_parent_item_id,
                AAG_ORDER_NUMBER,
                Size,
                ORDER_QTY,
                [Order Qty]
            FROM STG_MON_CustMasterSchedule_Subitems
            WHERE stg_batch_id = ?
              AND stg_status = 'PENDING'
              AND stg_monday_parent_item_id IS NOT NULL
            ORDER BY stg_parent_stg_id, Size
        """

        with self.staging_ops.get_connection() as conn:
            subitems_df = pd.read_sql(subitem_query, conn, params=[batch_id])

        if subitems_df.empty:
            logger.info(f"No subitems ready for API creation in batch {batch_id}")
            return 0, 0

        logger.info(f"Found {len(subitems_df)} subitems ready for Monday.com API creation")

        # Process in batches - FIXED LOGIC
        BATCH_SIZE = 10  # Reasonable batch size to avoid timeouts
        success_count = 0
        error_count = 0
        
        for batch_start in range(0, len(subitems_df), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(subitems_df))
            batch_df = subitems_df.iloc[batch_start:batch_end]
            
            logger.info(f"Processing subitems batch {batch_start//BATCH_SIZE + 1}: items {batch_start+1}-{batch_end} of {len(subitems_df)}")
            
            # Prepare batch payload for THIS BATCH ONLY
            batch_payload = []
            batch_stg_id_map = []
            
            for _, subitem in batch_df.iterrows():
                item_name = f"Size {subitem['Size']}"
                subitem_column_values = {
                    "dropdown_mkrak7qp": {"labels": [str(subitem['Size'])]},  # Size dropdown
                    "numeric_mkra7j8e": str(subitem['ORDER_QTY'])  # Order Qty numeric
                }
                batch_payload.append({
                    "parent_item_id": int(subitem['stg_monday_parent_item_id']),
                    "item_name": item_name,
                    "column_values": subitem_column_values
                })
                batch_stg_id_map.append({
                    "stg_subitem_id": subitem['stg_subitem_id'],
                    "AAG_ORDER_NUMBER": subitem['AAG_ORDER_NUMBER'],
                    "Size": subitem['Size']
                })

            # Call batch API for THIS BATCH ONLY
            try:
                batch_success, batch_results, batch_error = self.monday_client.create_subitems_batch(batch_payload)
                
                if batch_success:
                    # Process results for THIS BATCH
                    for idx, result in enumerate(batch_results):
                        stg_info = batch_stg_id_map[idx]  # Now correctly indexed to current batch
                        if result and 'subitem_id' in result:
                            subitem_id = result['subitem_id']
                            self.staging_ops.update_subitem_with_monday_id(
                                stg_info['stg_subitem_id'],
                                int(subitem_id)
                            )
                            success_count += 1
                            logger.info(f"Created subitem {subitem_id} for order {stg_info['AAG_ORDER_NUMBER']}, size {stg_info['Size']}")
                        else:
                            # Mark individual subitem as failed
                            self.staging_ops.mark_subitem_as_failed(
                                stg_info['stg_subitem_id'],
                                "No subitem ID returned from API"
                            )
                            error_count += 1
                            logger.error(f"Failed to create subitem for order {stg_info['AAG_ORDER_NUMBER']}, size {stg_info['Size']}")
                else:
                    # Only mark THIS BATCH as failed
                    for stg_info in batch_stg_id_map:  # Only current batch items
                        self.staging_ops.mark_subitem_as_failed(
                            stg_info['stg_subitem_id'],
                            batch_error or "Batch subitem creation failed"
                        )
                        error_count += 1
                        logger.error(f"Failed to create subitem for order {stg_info['AAG_ORDER_NUMBER']}, size {stg_info['Size']}: {batch_error}")
                    
            except Exception as e:
                # Only mark THIS BATCH as failed
                for stg_info in batch_stg_id_map:  # Only current batch items
                    self.staging_ops.mark_subitem_as_failed(
                        stg_info['stg_subitem_id'],
                        str(e)
                    )
                    error_count += 1
                    logger.error(f"Unexpected error processing subitem for order {stg_info['AAG_ORDER_NUMBER']}, size {stg_info['Size']}: {e}")

        logger.info(f"Subitem creation completed: {success_count} success, {error_count} errors")
        return success_count, error_count
    
    def process_customer_batch(self, customer_name: str) -> Dict[str, any]:
        """Main workflow orchestrator for a single customer batch"""
        
        logger.info(f"Starting batch processing for customer: {customer_name}")
        
        # Start batch tracking
        batch_id = self.staging_ops.start_batch(customer_name, 'FULL_BATCH')
        
        try:
            # Step 1: Load new orders to staging
            orders_loaded = self.load_new_orders_to_staging(customer_name, batch_id)
            
            if orders_loaded == 0:
                self.staging_ops.update_batch_status(batch_id, 'COMPLETED', 0, 0, 0, 'No new orders found')
                return {
                    'batch_id': batch_id,
                    'customer_name': customer_name,
                    'status': 'COMPLETED',
                    'orders_loaded': 0,
                    'items_created': 0,
                    'subitems_created': 0,
                    'message': 'No new orders found'
                }
            
            # Step 2: Create Monday.com items
            items_success, items_errors = self.create_monday_items_from_staging(batch_id)
            
            # Step 3: Create subitems
            subitems_success, subitems_errors = self.create_monday_subitems_from_staging(batch_id)
            
            # Step 4: Promote successful records to production MON_ tables
            orders_promoted, subitems_promoted = self.staging_ops.promote_successful_orders_to_production(batch_id)
            
            # Step 5: Validate promotion success
            promotion_validation = self.staging_ops.validate_promotion_success(batch_id)
            
            # Step 6: Cleanup promoted staging records
            cleanup_results = self.staging_ops.cleanup_promoted_staging_records(batch_id)
            
            # Final batch status
            total_errors = items_errors + subitems_errors
            if total_errors == 0:
                final_status = 'COMPLETED'
                error_summary = None
            else:
                final_status = 'COMPLETED_WITH_ERRORS'
                error_summary = f"Items: {items_errors} errors, Subitems: {subitems_errors} errors"
            
            self.staging_ops.update_batch_status(
                batch_id, final_status,
                successful_records=items_success + subitems_success,
                failed_records=total_errors,
                error_summary=error_summary
            )
            
            result = {
                'batch_id': batch_id,
                'customer_name': customer_name,
                'status': final_status,
                'orders_loaded': orders_loaded,
                'items_created': items_success,
                'items_errors': items_errors,
                'subitems_created': subitems_success,
                'subitems_errors': subitems_errors,
                'orders_promoted': orders_promoted,
                'subitems_promoted': subitems_promoted,
                'promotion_validation': promotion_validation,
                'orders_deleted': cleanup_results.get('orders_deleted', 0),
                'subitems_deleted': cleanup_results.get('subitems_deleted', 0)
            }
            
            logger.info(f"Batch processing completed for {customer_name}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            self.staging_ops.update_batch_status(batch_id, 'FAILED', error_summary=error_msg)
            logger.error(f"Batch processing failed for {customer_name}: {e}")
            raise
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all connections before processing"""
        
        results = {}
        
        # Test database connection
        try:
            with self.staging_ops.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            results['database'] = True
            logger.info("Database connection: OK")
        except Exception as e:
            results['database'] = False
            logger.error(f"Database connection: FAILED - {e}")
        
        # Test Monday.com API
        api_success, api_error = self.monday_client.test_connection()
        results['monday_api'] = api_success
        if api_success:
            logger.info("Monday.com API connection: OK")
        else:
            logger.error(f"Monday.com API connection: FAILED - {api_error}")
        return results
    
    def process_specific_po(self, customer_name: str = None, po_number: str = None, 
                           aag_season: str = None, customer_season: str = None, limit: int = None) -> Dict[str, Any]:
        """
        Process orders with targeted filters (SAFE for production use)
        
        All parameters are optional, but at least one must be provided to avoid processing all records.
        
        Args:
            customer_name: Filter by customer name (e.g., "GREYSON CLOTHIERS")  
            po_number: Filter by PO number (e.g., "4755")
            aag_season: Filter by AAG season (e.g., "2026 SPRING")
            customer_season: Filter by customer season (e.g., "SP26")
        
        Returns:
            Dict with success status, counts, and batch_id
            
        Examples:
            # Process specific PO for a customer
            processor.process_specific_po(customer_name='GREYSON CLOTHIERS', po_number='4755')
            
            # Process all records for a customer and season
            processor.process_specific_po(customer_name='GREYSON CLOTHIERS', customer_season='SP26')
            
            # Process by PO number only
            processor.process_specific_po(po_number='4755')
        """
        # Safety check - require at least one filter
        if not any([customer_name, po_number, aag_season, customer_season]):
            error_msg = "Safety check failed: At least one filter must be provided (customer_name, po_number, aag_season, or customer_season)"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'orders_loaded': 0,
                'items_created': 0,
                'errors': 1
            }
        
        logger.info(f"Processing orders with targeted filters:")
        if customer_name:
            logger.info(f"  Customer: {customer_name}")
        if po_number:
            logger.info(f"  PO Number: {po_number}")
        if aag_season:
            logger.info(f"  AAG Season: {aag_season}")
        if customer_season:
            logger.info(f"  Customer Season: {customer_season}")
        
        try:
            # Step 1: Check if records exist with filters
            with self.staging_ops.get_connection() as conn:
                # Build dynamic query with all possible filters
                where_conditions = [
                    "cms.[AAG ORDER NUMBER] IS NULL",
                    "ou.[AAG ORDER NUMBER] IS NOT NULL",
                    "ou.[CUSTOMER STYLE] IS NOT NULL",
                    "ou.[CUSTOMER COLOUR DESCRIPTION] IS NOT NULL"
                ]
                params = []
                
                if customer_name:
                    where_conditions.append("ou.[CUSTOMER NAME] = ?")
                    params.append(customer_name)
                
                if po_number:
                    where_conditions.append("ou.[PO NUMBER] LIKE ?")
                    params.append(f'%{po_number}%')
                
                if aag_season:
                    where_conditions.append("ou.[AAG SEASON] = ?")
                    params.append(aag_season)
                    
                if customer_season:
                    where_conditions.append("ou.[CUSTOMER SEASON] = ?")
                    params.append(customer_season)
                
                check_query = f"""
                SELECT COUNT(*) as count
                FROM [dbo].[ORDERS_UNIFIED] ou
                LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
                    ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
                    -- AND ou.[CUSTOMER NAME] = cms.[CUSTOMER] removed as canonical names won't always match so not needed given AAG order number unique to a customer
                    AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
                    AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
                WHERE {' AND '.join(where_conditions)}
                """
                
                df = pd.read_sql(check_query, conn, params=params)
                record_count = df.iloc[0]['count']
                if record_count == 0:
                    filter_desc = []
                    if customer_name:
                        filter_desc.append(f"customer='{customer_name}'")
                    if po_number:
                        filter_desc.append(f"PO='{po_number}'")
                    if aag_season:
                        filter_desc.append(f"AAG_season='{aag_season}'")
                    if customer_season:
                        filter_desc.append(f"customer_season='{customer_season}'")
                    
                    return {
                        'success': False,
                        'error': f'No new records found with filters: {", ".join(filter_desc)}',
                        'orders_loaded': 0,
                        'items_created': 0,
                        'errors': 0
                    }
                
                logger.info(f"Found {record_count} new records matching filters")
              # Step 2: Start batch with dynamic naming
            batch_name_parts = []
            batch_type_parts = ["TARGETED"]
            
            if customer_name:
                batch_name_parts.append(customer_name.replace(' ', '_'))
                batch_type_parts.append("CUSTOMER")
            if po_number:
                batch_name_parts.append(f"PO_{po_number}")
                batch_type_parts.append("PO")
            if aag_season:
                batch_type_parts.append(f"AAG_{aag_season.replace(' ', '_')}")
            if customer_season:
                batch_type_parts.append(f"CUST_{customer_season.replace(' ', '_')}")
            
            batch_name = "_".join(batch_name_parts) if batch_name_parts else "FILTERED_ORDERS"
            batch_type = "_".join(batch_type_parts)
            
            batch_id = self.staging_ops.start_batch(batch_name, batch_type)
            
            # Step 3: Load orders with all filters
            orders_loaded = self.load_new_orders_for_specific_po(
                customer_name, po_number, batch_id, aag_season, customer_season, limit=limit
            )
            if orders_loaded == 0:
                self.staging_ops.update_batch_status(batch_id, 'NO_RECORDS')
                filter_desc = []
                if customer_name:
                    filter_desc.append(f"customer='{customer_name}'")
                if po_number:
                    filter_desc.append(f"PO='{po_number}'")
                if aag_season:
                    filter_desc.append(f"AAG_season='{aag_season}'")
                if customer_season:
                    filter_desc.append(f"customer_season='{customer_season}'")
                
                return {
                    'success': False,
                    'error': f'No orders loaded with filters: {", ".join(filter_desc)}',
                    'batch_id': batch_id,
                    'orders_loaded': 0,
                    'items_created': 0,
                    'errors': 0
                }
            
            # Step 4: Create Monday.com items
            items_created, errors = self.create_monday_items_from_staging(batch_id)
            
            # Step 5: Create Monday.com subitems
            subitems_created, subitems_errors = self.create_monday_subitems_from_staging(batch_id)
            
            # Step 6: Promote successful records to production MON_ tables
            orders_promoted, subitems_promoted = self.staging_ops.promote_successful_orders_to_production(batch_id)
            
            # Step 7: Validate promotion success
            promotion_validation = self.staging_ops.validate_promotion_success(batch_id)
            
            # Step 8: Cleanup promoted staging records
            cleanup_results = self.staging_ops.cleanup_promoted_staging_records(batch_id)
            
            # Step 7: Update final status
            total_errors = subitems_errors
            if total_errors == 0:
                self.staging_ops.update_batch_status(batch_id, 'COMPLETED')
                final_status = 'COMPLETED'
            else:
                self.staging_ops.update_batch_status(batch_id, 'COMPLETED_WITH_ERRORS')
                final_status = 'COMPLETED_WITH_ERRORS'
            
            logger.info(f"Targeted processing {final_status}: {orders_loaded} loaded, {items_created} items, {subitems_created} subitems, {total_errors} errors")
            logger.info(f"Cleanup results: {cleanup_results}")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'orders_loaded': orders_loaded,
                'items_created': items_created,
                'subitems_created': subitems_created,
                'subitems_errors': subitems_errors,
                'errors': total_errors,
                'status': final_status,
                'cleanup': cleanup_results
            }
        except Exception as e:
            filter_desc = []
            if customer_name:
                filter_desc.append(f"customer='{customer_name}'")
            if po_number:
                filter_desc.append(f"PO='{po_number}'")
            if aag_season:
                filter_desc.append(f"AAG_season='{aag_season}'")
            if customer_season:
                filter_desc.append(f"customer_season='{customer_season}'")
            
            logger.error(f"Failed to process orders with filters {', '.join(filter_desc)}: {e}")
            return {
                'success': False,
                'error': str(e),
                'orders_loaded': 0,
                'items_created': 0,
                'errors': 1
            }
    
    def load_new_orders_for_specific_po(self, customer_name: str = None, po_number: str = None, batch_id: str = "",
                                       aag_season: str = None, customer_season: str = None, limit: int = None) -> int:
        """Load new orders with targeted filters"""
        filter_desc = []
        if customer_name:
            filter_desc.append(f"customer={customer_name}")
        if po_number:
            filter_desc.append(f"PO={po_number}")
        if aag_season:
            filter_desc.append(f"AAG_season={aag_season}")
        if customer_season:
            filter_desc.append(f"customer_season={customer_season}")
        
        logger.info(f"Loading new orders with filters: {', '.join(filter_desc)}")
        
        # Get new orders with filters
        orders_df = self.get_new_orders_for_specific_po(customer_name, po_number, aag_season, customer_season, limit=limit)
        
        if orders_df.empty:
            logger.info(f"No new orders found with filters: {', '.join(filter_desc)}")
            return 0
        
        # Transform orders using complete YAML mapping
        logger.info(f"Transforming {len(orders_df)} orders")
        from customer_master_schedule.order_mapping import transform_orders_batch
        transformed_df = transform_orders_batch(orders_df)
        
        if transformed_df.empty:
            logger.warning(f"No orders successfully transformed")
            return 0
        
        # Generate batch name for insertion
        batch_name_parts = []
        if customer_name:
            batch_name_parts.append(customer_name.replace(' ', '_'))
        if po_number:
            batch_name_parts.append(f"PO_{po_number}")
        batch_name = "_".join(batch_name_parts) if batch_name_parts else "FILTERED_ORDERS"
        
        # Insert to staging
        rows_inserted = self.staging_ops.insert_orders_to_staging(
            transformed_df, batch_name, batch_id
        )
        
        # Update batch status
        self.staging_ops.update_batch_status(
            batch_id, 'STAGING_LOADED', total_records=rows_inserted
        )
        return rows_inserted

    def get_new_orders_for_specific_po(self, customer_name: str = None, po_number: str = None,
                                      aag_season: str = None, customer_season: str = None, limit: int = None) -> pd.DataFrame:
        """Get new orders with targeted filters"""
        
        # Build dynamic query with all possible filters
        where_conditions = [
            "cms.[AAG ORDER NUMBER] IS NULL",
            "ou.[AAG ORDER NUMBER] IS NOT NULL",
            "ou.[CUSTOMER STYLE] IS NOT NULL"
        ]
        params = []
        
        if customer_name:
            where_conditions.append("ou.[CUSTOMER NAME] = ?")
            params.append(customer_name)
        
        if po_number:
            where_conditions.append("ou.[PO NUMBER] LIKE ?")
            params.append(f'%{po_number}%')
        
        if aag_season:
            where_conditions.append("ou.[AAG SEASON] = ?")
            params.append(aag_season)
            
        if customer_season:
            where_conditions.append("ou.[CUSTOMER SEASON] = ?")
            params.append(customer_season)
        
        top_clause = f"TOP {limit} " if limit is not None else ""
        query = f"""
        SELECT {top_clause}ou.*
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
            ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
            -- AND ou.[CUSTOMER NAME] = cms.[CUSTOMER] removed as canonical names won't always match so not needed given AAG order number unique to a customer
            AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
        WHERE {' AND '.join(where_conditions)}
        ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
        """
        
        # print(f"Executing query: {query}")

        with self.staging_ops.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        filter_desc = []
        if customer_name:
            filter_desc.append(f"customer={customer_name}")
        if po_number:
            filter_desc.append(f"PO={po_number}")
        if aag_season:
            filter_desc.append(f"AAG_season={aag_season}")
        if customer_season:
            filter_desc.append(f"customer_season={customer_season}")
        
        logger.info(f"Found {len(df)} new orders with filters: {', '.join(filter_desc)}")
        return df
