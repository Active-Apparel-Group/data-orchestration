"""
Main batch processor for Monday.com staging workflow
Orchestrates the complete customer batch processing pipeline
"""

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from .staging_operations import StagingOperations
from .monday_api_client import MondayApiClient
from .error_handler import ErrorHandler
from .staging_config import get_config

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
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.config = get_config()
        
        # Initialize components
        self.staging_ops = StagingOperations(connection_string)
        self.monday_client = MondayApiClient()
        self.error_handler = ErrorHandler(connection_string)
        
        # Load mapping configuration once
        self.mapping_config = load_mapping_config()
        self.customer_lookup = load_customer_mapping()
    def get_customers_with_new_orders(self) -> List[str]:
        """Get list of customers with new orders not yet in MON_CustMasterSchedule"""
        
        query = """
        SELECT DISTINCT ou.[CUSTOMER NAME] as customer_name
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
            ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
            AND ou.[CUSTOMER NAME] = cms.[CUSTOMER]
            AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
        WHERE cms.[AAG ORDER NUMBER] IS NULL
            AND ou.[AAG ORDER NUMBER] IS NOT NULL
            AND ou.[CUSTOMER STYLE] IS NOT NULL
            AND ou.[CUSTOMER COLOUR DESCRIPTION] IS NOT NULL
            AND ou.[CUSTOMER NAME] IS NOT NULL
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
            AND ou.[CUSTOMER NAME] = cms.[CUSTOMER]
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
        """Step 2: Create Monday.com items from staging records"""
        
        logger.info(f"Creating Monday.com items for batch {batch_id}...")
        
        # Get pending orders from staging
        pending_orders = self.staging_ops.get_pending_staging_orders(batch_id)
        
        if pending_orders.empty:
            logger.info(f"No pending orders found for batch {batch_id}")
            return 0, 0
        
        success_count = 0
        error_count = 0
        
        for _, order_row in pending_orders.iterrows():
            stg_id = order_row['stg_id']
            order_number = order_row.get('AAG ORDER NUMBER', 'Unknown')
            
            try:
                # Create item name and group name
                item_name = self.create_item_name(order_row)
                group_name = self.create_group_name(order_row)
                
                # Get column values for Monday.com
                column_values = self.get_monday_column_values_for_staged_order(order_row)
                
                # Ensure group exists
                group_success, group_id, group_error = self.monday_client.ensure_group_exists(group_name)
                if not group_success:
                    error_msg = f"Failed to ensure group exists: {group_error}"
                    self.staging_ops.mark_staging_as_failed(stg_id, error_msg)
                    
                    # Log to error table
                    self.error_handler.log_api_error('ITEM', {
                        'stg_id': stg_id,
                        'batch_id': batch_id,
                        'customer_batch': order_row.get('stg_customer_batch'),
                        'order_number': order_number,
                        'item_name': item_name,
                        'group_name': group_name,
                        'retry_count': 0
                    }, {
                        'error_type': 'GROUP_CREATION_ERROR',
                        'error_message': error_msg,
                        'api_payload': json.dumps({'group_name': group_name})
                    })
                    
                    error_count += 1
                    continue
                
                # Create item
                item_success, monday_item_id, item_error = self.monday_client.create_item(
                    item_name, group_id, column_values
                )
                
                if item_success:
                    # Update staging with Monday.com item ID
                    api_payload = json.dumps({
                        'item_name': item_name,
                        'group_id': group_id,
                        'column_values': column_values
                    })
                    
                    self.staging_ops.update_staging_with_monday_id(
                        stg_id, int(monday_item_id), api_payload
                    )
                    success_count += 1
                    logger.info(f"Created Monday.com item {monday_item_id} for order {order_number}")
                    
                else:
                    # Mark staging as failed
                    self.staging_ops.mark_staging_as_failed(stg_id, item_error)
                    
                    # Log to error table
                    self.error_handler.log_api_error('ITEM', {
                        'stg_id': stg_id,
                        'batch_id': batch_id,
                        'customer_batch': order_row.get('stg_customer_batch'),
                        'order_number': order_number,
                        'item_name': item_name,
                        'group_name': group_name,
                        'retry_count': 0
                    }, {
                        'error_type': 'ITEM_CREATION_ERROR',
                        'error_message': item_error,
                        'api_payload': json.dumps({
                            'item_name': item_name,
                            'group_id': group_id,
                            'column_values': column_values
                        })
                    })
                    
                    error_count += 1
                    logger.error(f"Failed to create Monday.com item for order {order_number}: {item_error}")
            
            except Exception as e:
                error_msg = f"Unexpected error creating item: {str(e)}"
                self.staging_ops.mark_staging_as_failed(stg_id, error_msg)
                error_count += 1
                logger.error(f"Unexpected error processing order {order_number}: {e}")
        
        # Update batch status
        self.staging_ops.update_batch_status(
            batch_id, 'ITEMS_CREATED', 
            successful_records=success_count,
            failed_records=error_count
        )
        
        logger.info(f"Item creation completed: {success_count} success, {error_count} errors")
        return success_count, error_count
    
    def create_monday_subitems_from_staging(self, batch_id: str) -> Tuple[int, int]:
        """Step 3: Create Monday.com subitems from staging records"""
        
        logger.info(f"Creating Monday.com subitems for batch {batch_id}...")
        
        # Get successful orders for subitem processing
        successful_orders = self.staging_ops.get_successful_orders_for_subitems(batch_id)
        
        if successful_orders.empty:
            logger.info(f"No successful orders found for subitem processing in batch {batch_id}")
            return 0, 0
        
        success_count = 0
        error_count = 0
        
        for _, order_row in successful_orders.iterrows():
            stg_id = order_row['stg_id']
            monday_item_id = order_row['stg_monday_item_id']
            order_number = order_row.get('AAG ORDER NUMBER', 'Unknown')
            
            try:
                # Get sizes from ORDERS_UNIFIED and unpivot
                subitems_df = self.get_subitems_for_order(order_row)
                
                if subitems_df.empty:
                    logger.info(f"No subitems found for order {order_number}")
                    continue
                
                # Insert subitems to staging
                subitems_inserted = self.staging_ops.insert_subitems_to_staging(subitems_df, batch_id)
                
                # Create subitems via Monday.com API
                for _, subitem_row in subitems_df.iterrows():
                    size_name = subitem_row.get('Size', 'Unknown Size')
                    order_qty = subitem_row.get('Order Qty', 0)
                    
                    # Create subitem column values
                    subitem_column_values = {
                        # Add column mappings for subitems here
                        # This would come from your YAML mapping for subitems
                    }
                    
                    # Create subitem via API
                    subitem_success, subitem_id, subitem_error = self.monday_client.create_subitem(
                        monday_item_id, size_name, subitem_column_values
                    )
                    
                    if subitem_success:
                        # Update staging subitem with Monday.com subitem ID
                        # Implementation would go here
                        success_count += 1
                        logger.info(f"Created subitem {subitem_id} for order {order_number}, size {size_name}")
                    else:
                        # Log subitem error
                        self.error_handler.log_api_error('SUBITEM', {
                            'parent_stg_id': stg_id,
                            'batch_id': batch_id,
                            'order_number': order_number,
                            'size_name': size_name,
                            'order_qty': order_qty,
                            'retry_count': 0
                        }, {
                            'error_type': 'SUBITEM_CREATION_ERROR',
                            'error_message': subitem_error,
                            'api_payload': json.dumps({
                                'parent_item_id': monday_item_id,
                                'size_name': size_name,
                                'column_values': subitem_column_values
                            })
                        })
                        error_count += 1
                        logger.error(f"Failed to create subitem for order {order_number}: {subitem_error}")
                        
            except Exception as e:
                error_msg = f"Unexpected error creating subitems: {str(e)}"
                error_count += 1
                logger.error(f"Unexpected error processing subitems for order {order_number}: {e}")
        
        logger.info(f"Subitem creation completed: {success_count} success, {error_count} errors")
        return success_count, error_count
    
    def get_subitems_for_order(self, order_row: pd.Series) -> pd.DataFrame:
        """Get and unpivot size data for an order to create subitems"""
        
        order_number = order_row.get('AAG ORDER NUMBER')
        style = order_row.get('STYLE')
        color = order_row.get('COLOR')
          # Query to get size data from ORDERS_UNIFIED  
        size_query = """
        SELECT [AAG ORDER NUMBER], [CUSTOMER STYLE] as STYLE, [CUSTOMER COLOUR DESCRIPTION] as COLOR,
               [XS], [S], [M], [L], [XL], [XXL], [XXXL], [OS] as [ONE SIZE]
        FROM [dbo].[ORDERS_UNIFIED]
        WHERE [AAG ORDER NUMBER] = ? AND [CUSTOMER STYLE] = ? AND [CUSTOMER COLOUR DESCRIPTION] = ?
        """
        
        with self.staging_ops.get_connection() as conn:
            size_df = pd.read_sql(size_query, conn, params=[order_number, style, color])
        
        if size_df.empty:
            return pd.DataFrame()
        
        # Unpivot sizes to create subitem records
        size_row = size_df.iloc[0]
        subitems = []
        size_columns = {
            'XS': 'XS',
            'S': 'S', 
            'M': 'M',
            'L': 'L',
            'XL': 'XL',
            'XXL': 'XXL',
            'XXXL': 'XXXL',
            'ONE SIZE': 'ONE SIZE'
        }
        
        for qty_col, size_name in size_columns.items():
            order_qty = size_row.get(qty_col, 0)
            
            # Only create subitem if quantity > 0
            if pd.notna(order_qty) and float(order_qty) > 0:
                subitems.append({
                    'parent_item_id': order_row.get('stg_monday_item_id'),
                    'Size': size_name,
                    'Order Qty': int(float(order_qty)),
                    'Item ID': order_row.get('stg_monday_item_id'),
                    'AAG ORDER NUMBER': order_number,
                    'STYLE': style,
                    'COLOR': color
                })
        
        return pd.DataFrame(subitems)

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
            
            # Step 4: Promote successful records to production
            orders_promoted, subitems_promoted = self.staging_ops.promote_successful_records(batch_id)
            
            # Step 5: Cleanup staging
            cleanup_count = self.staging_ops.cleanup_successful_staging(batch_id)
            
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
                'cleanup_count': cleanup_count
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
                           aag_season: str = None, customer_season: str = None) -> Dict[str, Any]:
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
                    AND ou.[CUSTOMER NAME] = cms.[CUSTOMER]
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
                customer_name, po_number, batch_id, aag_season, customer_season
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
            
            # Step 5: Update final status
            if errors == 0:
                self.staging_ops.update_batch_status(batch_id, 'COMPLETED')
                final_status = 'COMPLETED'
            else:
                self.staging_ops.update_batch_status(batch_id, 'COMPLETED_WITH_ERRORS')
                final_status = 'COMPLETED_WITH_ERRORS'
            
            logger.info(f"Targeted processing {final_status}: {orders_loaded} loaded, {items_created} created, {errors} errors")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'orders_loaded': orders_loaded,
                'items_created': items_created,
                'errors': errors,
                'status': final_status
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
                                       aag_season: str = None, customer_season: str = None) -> int:
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
        orders_df = self.get_new_orders_for_specific_po(customer_name, po_number, aag_season, customer_season)
        
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
                                      aag_season: str = None, customer_season: str = None) -> pd.DataFrame:
        """Get new orders with targeted filters"""
        
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
        
        query = f"""
        SELECT ou.*
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
            ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
            AND ou.[CUSTOMER NAME] = cms.[CUSTOMER]
            AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
        WHERE {' AND '.join(where_conditions)}
        ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
        """
        
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
