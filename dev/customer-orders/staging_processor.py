#!/usr/bin/env python3
"""
Staging Processor - Handles staging table operations and Monday.com integration

Manages the staging workflow:
- Load customer batches to staging tables
- Process master schedule records (create Monday.com items)
- Process subitems with UUID joins
- Promote successful records to production
- Clean up staging tables

Features:
- UUID-based joins between staging tables
- Size melting/pivoting during staging
- Monday.com API integration
- Error handling and retry logic
"""

import os
import sys
from pathlib import Path
import pandas as pd
import uuid
from datetime import datetime
import yaml

# Add utils to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

# Import from the same package directory
from monday_api_adapter import MondayApiAdapter

class StagingProcessor:
    """Processes customer batches through staging tables"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.database = "ORDERS"
        
        # Initialize Monday.com API adapter
        self.monday_api = MondayApiAdapter()
        
        # Load subitem mapping configuration from YAML
        self.subitem_config = self._load_subitem_mapping()
        
        # Size columns will be detected dynamically per batch
        self.size_columns = []  # Will be populated by detect_size_columns()
    
    def _load_subitem_mapping(self) -> dict:
        """Load subitem mapping configuration from YAML"""
        try:
            subitem_mapping_path = repo_root / "sql" / "mappings" / "subitem-field-mapping.yaml"
            with open(subitem_mapping_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.info("Loaded subitem mapping configuration")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load subitem mapping: {e}")
            # Fallback to hardcoded sizes
            return {
                'fallback_sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL', '4XL', '5XL']
            }
    
    def detect_size_columns(self, df: pd.DataFrame) -> list:
        """
        Detect size columns between UNIT OF MEASURE and TOTAL QTY
        Based on algorithm from subitem-field-mapping.yaml
        """
        try:
            if 'UNIT OF MEASURE' in df.columns and 'TOTAL QTY' in df.columns:
                start = df.columns.get_loc('UNIT OF MEASURE')
                end = df.columns.get_loc('TOTAL QTY')
                detected_sizes = df.columns[start+1:end].tolist()
                
                # Filter out non-numeric or clearly non-size columns
                size_columns = [col for col in detected_sizes if col not in ['', 'NULL', 'N/A']]
                
                self.logger.info(f"Detected {len(size_columns)} size columns: {size_columns[:10]}...")
                return size_columns
            else:
                self.logger.warning("Could not detect size columns - missing UNIT OF MEASURE or TOTAL QTY markers")
                # Fallback to configured default sizes
                fallback = self.subitem_config.get('fallback_sizes', ['XS', 'S', 'M', 'L', 'XL'])
                self.logger.info(f"Using fallback size columns: {fallback}")
                return fallback
                
        except Exception as e:
            self.logger.error(f"Error detecting size columns: {e}")
            # Return minimal fallback
            return ['XS', 'S', 'M', 'L', 'XL']
    
    def stage_customer_batch(self, customer: str, batch_data: pd.DataFrame) -> str:
        """
        Stage a customer batch for processing
        
        Args:
            customer: Customer name
            batch_data: Customer's order data
            
        Returns:
            str: Batch ID for tracking
        """
        
        batch_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"Staging batch for {customer} ({len(batch_data)} records)")
            
            # Prepare staging data
            staging_data = self._prepare_staging_data(batch_data, customer, batch_id)
              # Insert to staging orders table and get back data with actual database IDs
            orders_with_ids = self._insert_to_staging_orders(staging_data, batch_id)
            
            # Create subitems from size columns using the data with actual IDs
            subitems_data = self._create_subitems_from_sizes(orders_with_ids, batch_id)
            
            # Insert to staging subitems table
            subitems_inserted = self._insert_to_staging_subitems(subitems_data, batch_id)
            
            self.logger.info(f"Staged {len(orders_with_ids)} orders, {subitems_inserted} subitems for {customer}")
            return batch_id
            
        except Exception as e:
            self.logger.error(f"Staging failed for {customer}: {str(e)}")
            raise
    
    def process_master_schedule(self, batch_id: str) -> dict:
        """
        Process master schedule records (create Monday.com items)
        
        Args:
            batch_id: Batch to process
            
        Returns:
            dict: Processing results
        """
        
        try:
            self.logger.info(f"Processing master schedule for batch {batch_id}")
            
            # Get pending orders from staging
            pending_orders = self._get_pending_staging_orders(batch_id)
            
            if pending_orders.empty:
                return {'success': True, 'processed': 0}
            
            processed = 0
            
            # Process each order through Monday.com API
            for _, order in pending_orders.iterrows():
                try:
                    # Use Monday.com API adapter to create master schedule item
                    result = self.monday_api.create_master_schedule_item(order)
                    
                    if result['success']:
                        # Update staging record with success
                        self._update_staging_order_success(
                            order['stg_id'], 
                            result['monday_item_id']
                        )
                        processed += 1
                    else:
                        # Update staging record with error
                        self._update_staging_order_error(
                            order['stg_id'], 
                            result.get('error', 'Unknown error')
                        )
                        
                except Exception as e:
                    self.logger.error(f"   ERROR: Failed to process order {order.get('AAG ORDER NUMBER', 'unknown')}: {str(e)}")
                    self._update_staging_order_error(order['stg_id'], str(e))
            
            self.logger.info(f"   SUCCESS: Processed {processed}/{len(pending_orders)} master schedule items")
            
            return {
                'success': processed > 0,
                'processed': processed,
                'total': len(pending_orders)
            }
            
        except Exception as e:
            self.logger.error(f"CRITICAL: Master schedule processing failed: {str(e)}")
            raise
    
    def process_subitems(self, batch_id: str) -> dict:
        """
        Process subitems with UUID joins
        
        Args:
            batch_id: Batch to process
            
        Returns:
            dict: Processing results
        """
        
        try:
            self.logger.info(f"Processing subitems for batch {batch_id}")
            
            # Get successful orders to create subitems for
            successful_orders = self._get_successful_staging_orders(batch_id)
            
            if successful_orders.empty:
                return {'success': True, 'processed': 0}
            
            # Get pending subitems linked to successful orders
            pending_subitems = self._get_pending_staging_subitems(batch_id)
            
            if pending_subitems.empty:
                return {'success': True, 'processed': 0}
              
            # Process subitems through Monday.com API
            processed = 0
            
            # Group subitems by parent order for batch processing
            for parent_uuid, subitem_group in pending_subitems.groupby('parent_source_uuid'):
                try:
                    # Find the parent Monday.com item ID
                    parent_order = successful_orders[
                        successful_orders['source_uuid'] == parent_uuid
                    ]
                    
                    if parent_order.empty:
                        self.logger.warning(f"   ⚠️ No successful parent order found for UUID: {parent_uuid}")
                        continue
                    
                    parent_monday_id = parent_order.iloc[0].get('monday_item_id')
                    
                    if not parent_monday_id:
                        self.logger.warning(f"   ⚠️ No Monday item ID for parent UUID: {parent_uuid}")
                        continue
                      # Create subitems using Monday.com API
                    subitem_results = self.monday_api.create_subitems(
                        parent_monday_id, 
                        subitem_group
                    )
                    
                    # Safety check: ensure results is not None
                    if subitem_results is None:
                        self.logger.error(f"   ERROR: create_subitems returned None for parent {parent_uuid}")
                        continue
                    
                    # Update staging records with results
                    for i, result in enumerate(subitem_results):
                        subitem_row = subitem_group.iloc[i]
                        stg_subitem_id = subitem_row['stg_subitem_id']
                        
                        if result['success']:
                            self._update_staging_subitem_success(
                                stg_subitem_id, 
                                result['monday_subitem_id']
                            )
                            processed += 1
                        else:
                            self._update_staging_subitem_error(
                                stg_subitem_id, 
                                result.get('error', 'Unknown error')
                            )
                    
                except Exception as e:
                    self.logger.error(f"   ERROR: Failed to process subitems for parent {parent_uuid}: {str(e)}")
                    # Update all subitems in this group with error
                    for _, subitem in subitem_group.iterrows():
                        self._update_staging_subitem_error(subitem['stg_subitem_id'], str(e))
            
            self.logger.info(f"   SUCCESS: Processed {processed}/{len(pending_subitems)} subitems")
            
            return {
                'success': processed > 0,
                'processed': processed,
                'total': len(pending_subitems)
            }
            
        except Exception as e:
            self.logger.error(f"CRITICAL: Subitem processing failed: {str(e)}")
            raise
    
    def promote_to_production(self, batch_id: str) -> dict:
        """
        Promote successful staging records to production tables
        
        Args:
            batch_id: Batch to promote
            
        Returns:
            dict: Promotion results
        """
        
        try:
            self.logger.info(f"📈 Promoting successful records for batch {batch_id}")
            
            # Promote orders
            orders_promoted = self._promote_staging_orders(batch_id)
            
            # Promote subitems
            subitems_promoted = self._promote_staging_subitems(batch_id)
            
            self.logger.info(f"   SUCCESS: Promoted {orders_promoted} orders, {subitems_promoted} subitems")
            
            return {
                'success': True,
                'orders_promoted': orders_promoted,
                'subitems_promoted': subitems_promoted
            }
            
        except Exception as e:
            self.logger.error(f"CRITICAL: Promotion failed: {str(e)}")
            raise
    
    def cleanup_staging(self, batch_id: str) -> int:
        """Clean up staging records after successful promotion"""
        
        try:
            deleted = self._delete_promoted_staging_records(batch_id)
            self.logger.info(f"🧹 Cleaned up {deleted} staging records")
            return deleted
        except Exception as e:
            self.logger.error(f"Failed to cleanup staging: {e}")
            raise
            
    # Helper methods 
    
    def _prepare_staging_data(self, batch_data: pd.DataFrame, customer: str, batch_id: str) -> pd.DataFrame:
        """Prepare data for staging table insertion"""
        
        staging_data = batch_data.copy()
        
        # Add staging metadata
        staging_data['stg_id'] = [str(uuid.uuid4()) for _ in range(len(staging_data))]
        staging_data['batch_id'] = batch_id
        staging_data['customer_canonical'] = customer
        staging_data['stg_status'] = 'PENDING'
        staging_data['created_datetime'] = datetime.now()
        staging_data['updated_datetime'] = datetime.now()
        staging_data['monday_item_id'] = None
        staging_data['error_message'] = None
          # Ensure we have required source fields
        staging_data['source_uuid'] = staging_data.get('record_uuid', None)
        staging_data['source_hash'] = staging_data.get('record_hash', None)
        
        return staging_data
      
    def _map_to_staging_schema(self, source_data: pd.DataFrame) -> pd.DataFrame:
        """Map ORDERS_UNIFIED columns to STG_MON_CustMasterSchedule schema dynamically using DDL and master mapping"""
        
        # Get staging schema from DDL
        staging_schema = self._get_staging_schema_from_ddl()
        self.logger.info(f"   Debug: DDL schema found {len(staging_schema['columns'])} columns")
        self.logger.info(f"   Debug: DDL columns: {staging_schema['columns'][:10]}...")  # First 10 columns
        
        # Get field mappings from master mapping JSON
        from master_mapping_helper import load_master_mapping
        mapping = load_master_mapping()
          # Create empty DataFrame with exact DDL column order
        mapped_df = pd.DataFrame()
        
        # Map each staging column dynamically
        for staging_col in staging_schema['columns']:
            if staging_col == 'stg_id':
                continue  # Skip IDENTITY column
            elif staging_col == 'stg_batch_id':
                mapped_df[staging_col] = source_data['batch_id'] if 'batch_id' in source_data.columns else None
            elif staging_col == 'stg_status':
                mapped_df[staging_col] = 'PENDING'
            elif staging_col == 'stg_created_date':
                mapped_df[staging_col] = None  # Let SQL Server use DEFAULT GETDATE()
            elif staging_col == 'stg_processed_date':
                mapped_df[staging_col] = None  # Set during processing
            elif staging_col == 'stg_retry_count':
                mapped_df[staging_col] = 0
            elif staging_col == 'stg_monday_item_id':
                mapped_df[staging_col] = None
            elif staging_col == 'stg_error_message':
                mapped_df[staging_col] = None
            elif staging_col == 'stg_api_payload':
                mapped_df[staging_col] = None
            elif staging_col == 'stg_customer_batch':
                mapped_df[staging_col] = None
            elif staging_col == 'CUSTOMER':
                mapped_df[staging_col] = source_data['customer_canonical'] if 'customer_canonical' in source_data.columns else None
            elif staging_col == 'Group':
                # Implement group name logic: CUSTOMER CUSTOMER_SEASON or CUSTOMER AAG_SEASON or CUSTOMER [RANGE/COLLECTION]
                mapped_df[staging_col] = self._determine_group_name(source_data)
            else:
                # Find source column from master mapping or direct match
                source_col = self._find_source_column_for_staging(staging_col, source_data.columns, mapping)
                
                if source_col and source_col in source_data.columns:
                    mapped_df[staging_col] = source_data[source_col]
                else:
                    mapped_df[staging_col] = None
        
        self.logger.info(f"   Dynamically mapped {len(source_data)} records to staging schema ({len(mapped_df.columns)} columns)")
        return mapped_df
    
    def _get_staging_schema_from_ddl(self) -> dict:
        """Extract staging table schema from DDL file"""
        
        ddl_file = Path(__file__).parent.parent.parent / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule.sql"
        
        if not ddl_file.exists():
            raise FileNotFoundError(f"DDL file not found: {ddl_file}")
        
        with open(ddl_file, 'r') as f:
            ddl_content = f.read()
        
        # Extract column names from DDL (simple regex approach)
        import re
        
        # Find all column definitions between CREATE TABLE and constraints
        pattern = r'\[([^\]]+)\]\s+(?:NVARCHAR|BIGINT|DECIMAL|FLOAT|DATE|BIT|UNIQUEIDENTIFIER|DATETIME2)'
        columns = re.findall(pattern, ddl_content)
        
        return {
            'table': 'STG_MON_CustMasterSchedule',
            'columns': columns
        }
    
    def _find_source_column_for_staging(self, staging_col: str, source_columns: list, mapping: dict) -> str:
        """Find the source column that maps to a staging column"""
        
        # Check master mapping first
        for field_group in ['main_order_fields', 'subitem_essential_fields', 'subitem_update_fields']:
            if field_group in mapping.get('field_mappings', {}):
                for field_key, field_def in mapping['field_mappings'][field_group].items():
                    # Check various mapping targets
                    for target_key in ['staging_audit', 'staging_business', 'staging_monday']:
                        if field_def.get(target_key) == staging_col:
                            # Found staging column in mapping, now find source
                            source_col = field_def.get('orders_unified')
                            if source_col and source_col in source_columns:
                                return source_col
        
        # Direct column name match as fallback
        if staging_col in source_columns:
            return staging_col
        
        # Common variations
        variations = [
            staging_col.replace('_', ' '),
            staging_col.replace(' ', '_'),
            staging_col.upper(),
            staging_col.lower()
        ]
        
        for variation in variations:
            if variation in source_columns:
                return variation
        
        return None

    def _determine_group_name(self, source_data: pd.DataFrame) -> pd.Series:
        """
        Determine Monday.com group name using the logic:
        1. CUSTOMER CUSTOMER_SEASON
        2. If CUSTOMER_SEASON is blank: CUSTOMER AAG_SEASON  
        3. If AAG_SEASON is blank: CUSTOMER [RANGE/COLLECTION]
        4. Fallback: CUSTOMER_NAME only
        """
        
        def create_group_name(row):
            customer = row.get('customer_canonical', row.get('CUSTOMER NAME', 'Unknown'))
            customer_season = row.get('CUSTOMER SEASON', '')
            aag_season = row.get('AAG SEASON', '')
            
            # Clean up customer name (remove spaces/special chars for group ID)
            customer_clean = str(customer).strip().replace(' ', '_').upper()
            
            # Option 1: CUSTOMER CUSTOMER_SEASON
            if customer_season and pd.notna(customer_season) and str(customer_season).strip():
                season_clean = str(customer_season).strip().replace(' ', '_').upper()
                return f"{customer_clean}_{season_clean}"
            
            # Option 2: CUSTOMER AAG_SEASON 
            elif aag_season and pd.notna(aag_season) and str(aag_season).strip():
                aag_clean = str(aag_season).strip().replace(' ', '_').upper()
                return f"{customer_clean}_{aag_clean}"
            
            # Option 3: CUSTOMER [RANGE/COLLECTION] - using customer as fallback
            else:
                return customer_clean
        
        # Apply the logic to each row
        return source_data.apply(create_group_name, axis=1)
    
    def _insert_to_staging_orders(self, staging_data: pd.DataFrame, batch_id: str) -> pd.DataFrame:
        """Insert to STG_MON_CustMasterSchedule and return data with actual stg_id values"""
        
        try:
            # First, map the data to the staging table schema
            mapped_data = self._map_to_staging_schema(staging_data)
            
            # Ensure batch_id is set
            mapped_data['stg_batch_id'] = batch_id
              # Remove internal tracking columns that shouldn't go to staging table
            columns_to_exclude = ['source_uuid', 'source_hash']
            staging_columns = [col for col in mapped_data.columns if col not in columns_to_exclude]
            df_to_insert = mapped_data[staging_columns].copy()
            
            # Clean data types for database insertion
            df_to_insert = self._clean_data_types_for_insert(df_to_insert)
            
            # Debug: Check for any remaining problematic values
            self.logger.info(f"   Debug: Checking for empty strings or problematic values...")
            for col_idx, col in enumerate(df_to_insert.columns):
                if df_to_insert[col].dtype == 'object':
                    empty_count = (df_to_insert[col] == '').sum()
                    if empty_count > 0:
                        self.logger.warning(f"   Debug: Column {col_idx+1} ({col}) has {empty_count} empty strings")
                        # Show first few problematic values
                        problematic = df_to_insert[df_to_insert[col] == ''][col].head(3)
                        self.logger.warning(f"   Debug: Sample problematic values: {problematic.tolist()}")
            
            # Debug: Show data types and problematic column 28
            self.logger.info(f"   Debug: DataFrame info - Shape: {df_to_insert.shape}")
            column_28_name = df_to_insert.columns[27] if len(df_to_insert.columns) > 27 else "N/A"
            self.logger.info(f"   Debug: Column 28 is '{column_28_name}' with dtype: {df_to_insert[column_28_name].dtype if column_28_name != 'N/A' else 'N/A'}")
            if column_28_name != "N/A":
                unique_vals = df_to_insert[column_28_name].unique()[:5]  # First 5 unique values
                self.logger.info(f"   Debug: Column 28 sample values: {unique_vals}")
                null_count = df_to_insert[column_28_name].isnull().sum()
                self.logger.info(f"   Debug: Column 28 null count: {null_count}")
            
            # Debug: More detailed analysis of parameter 37
            column_37_name = df_to_insert.columns[36] if len(df_to_insert.columns) > 36 else "N/A"
            self.logger.info(f"   Debug: Column 37 is '{column_37_name}' with dtype: {df_to_insert[column_37_name].dtype if column_37_name != 'N/A' else 'N/A'}")
            if column_37_name != "N/A":
                unique_vals = df_to_insert[column_37_name].unique()[:5]
                self.logger.info(f"   Debug: Column 37 sample values: {unique_vals}")
                empty_string_count = (df_to_insert[column_37_name] == "").sum()
                self.logger.info(f"   Debug: Column 37 empty string count: {empty_string_count}")
                if empty_string_count > 0:
                    self.logger.error(f"   ERROR: Column 37 ({column_37_name}) still has empty strings after cleaning!")
            
            # Debug: More detailed analysis of parameter 4
            column_4_name = df_to_insert.columns[3] if len(df_to_insert.columns) > 3 else "N/A"
            self.logger.info(f"   Debug: Column 4 is '{column_4_name}' with dtype: {df_to_insert[column_4_name].dtype if column_4_name != 'N/A' else 'N/A'}")
            if column_4_name != "N/A":
                unique_vals = df_to_insert[column_4_name].unique()[:5]
                self.logger.info(f"   Debug: Column 4 sample values: {unique_vals}")
                empty_string_count = (df_to_insert[column_4_name] == "").sum()
                self.logger.info(f"   Debug: Column 4 empty string count: {empty_string_count}")
                if empty_string_count > 0:
                    self.logger.error(f"   ERROR: Column 4 ({column_4_name}) still has empty strings after cleaning!")
            
            # Debug: Show column order comparison
            self.logger.info(f"   Debug: DataFrame columns ({len(df_to_insert.columns)}): {list(df_to_insert.columns)}")
            
            # Manual insert using cursor and get the generated IDs
            inserted_ids = []
            with db.get_connection(self.database) as conn:
                cursor = conn.cursor()
                
                # Get column names from DataFrame
                columns = list(df_to_insert.columns)
                
                # Create placeholder string for VALUES clause
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join([f'[{col}]' for col in columns])
                
                insert_query = f"""
                    INSERT INTO [dbo].[STG_MON_CustMasterSchedule] ({column_names})
                    OUTPUT INSERTED.stg_id
                    VALUES ({placeholders})
                """
                
                # Insert each row and capture the generated ID
                for _, row in df_to_insert.iterrows():
                    values = [row[col] for col in columns]
                    cursor.execute(insert_query, values)
                    inserted_id = cursor.fetchone()[0]  # Get the generated stg_id
                    inserted_ids.append(inserted_id)
                
                conn.commit()
            
            # Add the actual database-generated stg_id back to the original data
            result_data = staging_data.copy()
            result_data['actual_stg_id'] = inserted_ids
            
            self.logger.info(f"   Inserted {len(inserted_ids)} records to STG_MON_CustMasterSchedule")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Failed to insert to staging orders table: {e}")
            raise
    
    def _create_subitems_from_sizes(self, staging_data: pd.DataFrame, batch_id: str) -> pd.DataFrame:
        """
        Create subitem records for each size with quantity
        Now uses YAML-based size detection instead of hardcoded columns
        """
        subitems = []

        try:
            # Load YAML mapping for dynamic size detection
            mapping_path = Path(__file__).parent.parent / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
            with open(mapping_path, 'r') as f:
                mapping_config = yaml.safe_load(f)
            
            # Get size detection configuration
            size_detection = mapping_config.get('size_detection', {})
            
            # Process each order row to create subitems
            for idx, order_row in staging_data.iterrows():
                parent_uuid = order_row.get('stg_source_uuid', str(uuid.uuid4()))
                
                # Dynamic size detection based on YAML patterns
                size_columns = []
                
                # Pattern-based detection (e.g., columns ending with 'QTY')
                for pattern_config in size_detection.get('patterns', []):
                    pattern = pattern_config.get('pattern', '')
                    if pattern.startswith('*'):
                        suffix = pattern[1:]
                        size_columns.extend([col for col in order_row.index if col.endswith(suffix)])
                    elif pattern.endswith('*'):
                        prefix = pattern[:-1]
                        size_columns.extend([col for col in order_row.index if col.startswith(prefix)])
                
                # Explicit column list fallback
                if not size_columns:
                    size_columns = size_detection.get('explicit_columns', [])
                
                # Common size labels for pattern matching
                common_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL', '4XL', '5XL']
                
                # Process each size column found
                for size_col in size_columns:
                    if size_col in order_row.index:
                        quantity = order_row.get(size_col, 0)
                        
                        if pd.notna(quantity) and float(quantity) > 0:
                            # Extract size label from column name
                            size_label = size_col
                            for size in common_sizes:
                                if size in size_col.upper():
                                    size_label = size
                                    break
                            
                            subitem = {
                                'stg_source_uuid': str(uuid.uuid4()),
                                'stg_parent_stg_id': order_row.get('stg_id'),
                                'AAG_ORDER_NUMBER': order_row.get('AAG ORDER NUMBER'),
                                'CUSTOMER_NAME': order_row.get('CUSTOMER NAME'),
                                'stg_size_column': size_col,
                                'stg_size_label': size_label,
                                'ORDER_QTY': int(float(quantity)),
                                'stg_created_at': datetime.now(),
                                'stg_batch_id': batch_id,
                                'stg_status': 'STAGED'
                            }
                            subitems.append(subitem)
                        
            self.logger.info(f"Created {len(subitems)} subitem records from sizes")
            
            # Convert to DataFrame
            if subitems:
                return pd.DataFrame(subitems)
            else:
                self.logger.warning("No subitems created - no size data found")
                return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error creating subitems from sizes: {str(e)}")
            return pd.DataFrame()
    
    def _insert_to_staging_subitems(self, subitems_data: pd.DataFrame, batch_id: str) -> int:
        """Insert to STG_MON_CustMasterSchedule_Subitems"""
        
        try:
            # Prepare DataFrame for insertion to subitems staging table
            df_to_insert = subitems_data.copy()
            
            # Remove the stg_subitem_id column (will be auto-generated by IDENTITY)
            if 'stg_subitem_id' in df_to_insert.columns:
                df_to_insert = df_to_insert.drop(columns=['stg_subitem_id'])
            
            # Ensure required columns exist
            if 'stg_retry_count' not in df_to_insert.columns:
                df_to_insert['stg_retry_count'] = 0
            
            # Manual insert using cursor (following existing pattern)
            with db.get_connection(self.database) as conn:
                cursor = conn.cursor()
                  # Get column names from DataFrame
                columns = list(df_to_insert.columns)
                
                # Create placeholder string for VALUES clause
                placeholders = ', '.join(['?' for _ in columns])
                
                # Handle column names - some already have brackets, some don't
                formatted_columns = []
                for col in columns:
                    if col.startswith('[') and col.endswith(']'):
                        formatted_columns.append(col)  # Already has brackets
                    else:
                        formatted_columns.append(f'[{col}]')  # Add brackets
                
                column_names = ', '.join(formatted_columns)
                
                insert_query = f"""
                    INSERT INTO [dbo].[STG_MON_CustMasterSchedule_Subitems] ({column_names})
                    VALUES ({placeholders})
                """
                
                # Insert each row
                rows_inserted = 0
                for _, row in df_to_insert.iterrows():
                    values = [row[col] for col in columns]
                    cursor.execute(insert_query, values)
                    rows_inserted += 1
                
                conn.commit()
                
            self.logger.info(f"   Inserted {rows_inserted} subitems to STG_MON_CustMasterSchedule_Subitems")
            return rows_inserted
            
        except Exception as e:
            self.logger.error(f"Failed to insert to staging subitems table: {e}")
            raise
    
    def _get_pending_staging_orders(self, batch_id: str) -> pd.DataFrame:
        """Get pending staging orders"""
        query = """
        SELECT stg_id, stg_batch_id, [AAG ORDER NUMBER], [CUSTOMER], 
               stg_status, CUSTOMER
        FROM [dbo].[STG_MON_CustMasterSchedule] 
        WHERE stg_batch_id = ? AND stg_status = 'PENDING'        
        """
        try:
            df = db.run_query(query, self.database, params=[batch_id])
            self.logger.info(f"   Found {len(df)} pending orders in batch {batch_id}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to get pending staging orders: {e}")
            return pd.DataFrame()
    
    def _get_successful_staging_orders(self, batch_id: str) -> pd.DataFrame:
        """Get successful staging orders with Monday.com item IDs"""        
        query = """
        SELECT stg_id, stg_batch_id, [AAG ORDER NUMBER], stg_monday_item_id as monday_item_id,
               source_uuid
        FROM [dbo].[STG_MON_CustMasterSchedule] 
        WHERE stg_batch_id = ? AND stg_status = 'API_SUCCESS' AND stg_monday_item_id IS NOT NULL
        """
        try:
            df = db.run_query(query, self.database, params=[batch_id])
            self.logger.info(f"   SUCCESS: Found {len(df)} successful orders in batch {batch_id}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to get successful staging orders: {e}")
            return pd.DataFrame()
    
    def _get_pending_staging_subitems(self, batch_id: str) -> pd.DataFrame:
        """Get pending staging subitems"""
        query = """
        SELECT stg_subitem_id, stg_batch_id, stg_parent_stg_id, parent_source_uuid,
               stg_size_label as size_name, ORDER_QTY as size_qty,
               stg_status
        FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]        WHERE stg_batch_id = ? AND stg_status = 'PENDING'        
        """
        
        try:
            df = db.run_query(query, self.database, params=[batch_id])
            self.logger.info(f"   Found {len(df)} pending subitems in batch {batch_id}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to get pending staging subitems: {e}")
            return pd.DataFrame()
    
    def _update_staging_order_success(self, stg_id: str, monday_item_id: int):
        """Update staging order with success status"""
        query = """
        UPDATE [dbo].[STG_MON_CustMasterSchedule] 
        SET stg_status = 'API_SUCCESS', 
            stg_monday_item_id = ?,
            stg_processed_date = GETDATE()
        WHERE stg_id = ?
        """
        
        try:
            db.run_query(query, self.database, params=[monday_item_id, stg_id])
        except Exception as e:
            self.logger.error(f"Failed to update staging order success: {e}")
    
    def _update_staging_order_error(self, stg_id: str, error_msg: str):
        """Update staging order with error status"""
        query = """
        UPDATE [dbo].[STG_MON_CustMasterSchedule] 
        SET stg_status = 'API_FAILED', 
            stg_error_message = ?,
            stg_processed_date = GETDATE(),
            stg_retry_count = stg_retry_count + 1
        WHERE stg_id = ?
        """
        
        try:
            db.run_query(query, self.database, params=[error_msg, stg_id])
        except Exception as e:
            self.logger.error(f"Failed to update staging order error: {e}")
    
    def _update_staging_subitem_success(self, stg_subitem_id: int, monday_subitem_id: int):
        """Update staging subitem with success"""
        query = """
        UPDATE [dbo].[STG_MON_CustMasterSchedule_Subitems] 
        SET stg_status = 'API_SUCCESS', 
            stg_monday_subitem_id = ?,
            stg_processed_date = GETDATE()
        WHERE stg_subitem_id = ?
        """
        
        try:
            db.run_query(query, self.database, params=[monday_subitem_id, stg_subitem_id])
        except Exception as e:
            self.logger.error(f"Failed to update staging subitem success: {e}")
    
    def _update_staging_subitem_error(self, stg_subitem_id: int, error_msg: str):
        """Update staging subitem with error"""
        query = """
        UPDATE [dbo].[STG_MON_CustMasterSchedule_Subitems] 
        SET stg_status = 'API_FAILED', 
            stg_error_message = ?,
            stg_processed_date = GETDATE(),
            stg_retry_count = stg_retry_count + 1
        WHERE stg_subitem_id = ?
        """
        
        try:
            db.run_query(query, self.database, params=[error_msg, stg_subitem_id])
        except Exception as e:
            self.logger.error(f"Failed to update staging subitem error: {e}")
    
    def _promote_staging_orders(self, batch_id: str) -> int:
        """Promote staging orders to production"""
        # Placeholder - would copy successful records to MON_CustMasterSchedule
        return 0
    
    def _promote_staging_subitems(self, batch_id: str) -> int:
        """Promote staging subitems to production"""
        # Placeholder - would copy successful records to MON_CustMasterSchedule_Subitems
        return 0
    
    def _delete_promoted_staging_records(self, batch_id: str) -> int:
        """Delete promoted staging records"""
        # Placeholder - would delete records with status 'PROMOTED'
        return 0
    
    def process_customer_batch_complete(self, customer: str, batch_data: pd.DataFrame) -> dict:
        """
        Complete end-to-end processing of a customer batch
        
        Steps:
        1. Stage the customer batch (orders + subitems)
        2. Process master schedule (create Monday.com items)
        3. Process subitems (create Monday.com subitems)
        4. Promote successful records
        5. Clean up staging tables
        
        Args:
            customer: Customer name
            batch_data: Customer's order data
            
        Returns:
            dict: Complete processing results
        """
        
        batch_id = None
        results = {
            'customer': customer,
            'batch_id': None,
            'status': 'STARTED',
            'staging': {'success': False, 'orders': 0, 'subitems': 0},
            'master_schedule': {'success': False, 'processed': 0, 'total': 0},
            'subitems': {'success': False, 'processed': 0, 'total': 0},
            'promotion': {'success': False, 'promoted': 0},
            'cleanup': {'success': False, 'cleaned': 0},
            'errors': []
        }
        
        try:
            self.logger.info(f"Starting complete batch processing for {customer} ({len(batch_data)} records)")
            
            # Step 1: Stage the batch
            self.logger.info("Step 1: Staging customer batch...")
            batch_id = self.stage_customer_batch(customer, batch_data)
            results['batch_id'] = batch_id
            results['staging']['success'] = True
            results['staging']['orders'] = len(batch_data)
            
            # Step 2: Process master schedule
            self.logger.info("STEP 2: Processing master schedule...")
            master_results = self.process_master_schedule(batch_id)
            results['master_schedule'] = master_results
            
            # Step 3: Process subitems (only if we have successful masters)
            if master_results['success'] and master_results['processed'] > 0:
                self.logger.info("📏 Step 3: Processing subitems...")
                subitems_results = self.process_subitems(batch_id)
                results['subitems'] = subitems_results
            else:
                self.logger.warning("WARNING: Skipping subitems - no successful master schedule items")
            
            # Step 4: Promote successful records (optional)
            # promotion_results = self.promote_to_production(batch_id)
            # results['promotion'] = promotion_results
              # Step 5: Cleanup (optional)
            # cleanup_count = self.cleanup_staging(batch_id)
            # results['cleanup'] = {'success': True, 'cleaned': cleanup_count}
            
            results['status'] = 'COMPLETED'
            self.logger.info(f"SUCCESS: Completed batch processing for {customer}")
            
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            results['status'] = 'FAILED'
            results['errors'].append(error_msg)
            self.logger.error(f"CRITICAL: {error_msg}")
            
        return results
    
    def _clean_data_types_for_insert(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types for database insertion using master mapping patterns"""
        
        df_clean = df.copy()
        
        # CRITICAL: Follow master mapping data type conversion patterns
        # Reference: utils/master_field_mapping.json > data_type_conversions
        
        # Define FLOAT columns that need robust conversion
        float_columns = [
            'CUSTOMER PRICE', 'USA ONLY LSTP 75% EX WORKS', 'EX WORKS (USD)',
            'ADMINISTRATION FEE', 'DESIGN FEE', 'FX CHARGE', 'HANDLING',
            'SURCHARGE FEE', 'DISCOUNT', 'FINAL FOB (USD)', 'US DUTY RATE',
            'US DUTY', 'FREIGHT', 'US TARIFF RATE', 'US TARIFF', 
            'DDP US (USD)', 'SMS PRICE USD', 'REVENUE (FOB)'
        ]
        
        # Define BIGINT columns that need conversion
        bigint_columns = [
            'FCST QTY', 'FCST CONSUMED QTY', 'ORDER QTY', 'PACKED QTY',
            'SHIPPED QTY', 'Net Demand', 'PRODUCTION QTY', 'Item ID'
        ]
          # CRITICAL: Robust FLOAT conversion - handle empty strings, NaN, etc.
        for col in float_columns:
            if col in df_clean.columns:
                # First replace empty strings and whitespace with NaN
                df_clean[col] = df_clean[col].replace('', pd.NA)
                df_clean[col] = df_clean[col].replace(' ', pd.NA)
                df_clean[col] = df_clean[col].replace('nan', pd.NA)
                df_clean[col] = df_clean[col].replace('NaN', pd.NA)
                
                # Convert to numeric, coercing errors to NaN
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
                # CRITICAL: For SQL Server float columns, use 0.0 instead of None for NULL
                # This prevents the pyodbc empty string conversion issue
                df_clean[col] = df_clean[col].fillna(0.0)
        
        # CRITICAL: Robust BIGINT conversion - pattern from master mapping
        for col in bigint_columns:
            if col in df_clean.columns:
                # Handle empty strings and convert to int for bigint columns
                df_clean[col] = df_clean[col].replace('', pd.NA)
                df_clean[col] = df_clean[col].replace(' ', pd.NA)
                
                # Convert to numeric first
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
                # Convert to int where valid, None where NaN
                df_clean[col] = df_clean[col].apply(
                    lambda x: int(x) if pd.notna(x) else None
                )
                
        # Convert DATE columns (ensure they're proper datetime or None)
        date_columns = [
            'ORDER DATE PO RECEIVED', 'CUSTOMER REQ IN DC DATE', 'CUSTOMER EX FACTORY DATE',
            'EX-FTY (Change Request)', 'EX-FTY (Forecast)', 'EX-FTY (Partner PO)',
            'EX-FTY (Revised LS)', 'PLANNED CUT DATE', 'TRIM ETA DATE', 'FABRIC ETA DATE',
            'PPS CMT DUE', 'PPS CMT RCV'
        ]
        
        for col in date_columns:
            if col in df_clean.columns:
                # Handle empty strings first
                df_clean[col] = df_clean[col].replace('', pd.NA)
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
          # CRITICAL: Handle any remaining object columns that might contain empty strings or NaN
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                # Replace empty strings AND pandas NaN with None for string columns  
                df_clean[col] = df_clean[col].replace('', None)
                df_clean[col] = df_clean[col].replace(' ', None)
                # Convert pandas NaN to None as well
                df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
        
        self.logger.info(f"   Applied robust data type conversions for database compatibility")
        return df_clean

if __name__ == "__main__":
    # For testing
    processor = StagingProcessor()
    print("SUCCESS: Staging processor initialized successfully")
