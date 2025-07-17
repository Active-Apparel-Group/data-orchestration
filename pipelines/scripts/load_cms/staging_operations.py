"""
Database operations for staging workflow
Handles all staging table CRUD operations
"""

import pandas as pd
import pyodbc
import json
import uuid
import asyncio
import concurrent.futures
import time
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from .staging_config import get_config, DATABASE_CONFIG

# Add project root to path for utils imports
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import db_helper

logger = logging.getLogger(__name__)

class StagingOperations:    
    def __init__(self, db_key: str):
        self.db_key = db_key  # Store db_key instead of connection_string
        self.config = get_config()
    
    def get_connection(self) -> pyodbc.Connection:
        """Get database connection using db_helper"""
        return db_helper.get_connection(self.db_key)
    
    def _clean_numeric_fields(self, df: pd.DataFrame, numeric_columns: list) -> pd.DataFrame:
        """Clean numeric columns to handle empty strings and nulls for SQL Server compatibility"""
        cleaned_df = df.copy()
        
        for col in numeric_columns:
            if col in cleaned_df.columns:
                def clean_value(val):
                    if pd.isna(val) or val == '' or str(val).upper() in ['NULL', 'NONE']:
                        return 0  # Default to 0 for empty/null values
                    try:
                        # Handle decimal strings by converting to float first, then int
                        return int(float(val))
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert '{val}' in column '{col}' to numeric, using 0")
                        return 0
                
                original_count = len(cleaned_df[col].unique())
                cleaned_df[col] = cleaned_df[col].apply(clean_value)
                cleaned_count = len(cleaned_df[col].unique())
                
                logger.info(f"Cleaned numeric field '{col}': {original_count} -> {cleaned_count} unique values")
        
        return cleaned_df
    
    def get_dynamic_numeric_fields_with_schema(self) -> Dict[str, Dict]:
        """Get numeric columns with their exact data types and precision from staging table schema"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get detailed schema information for numeric columns
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
                AND TABLE_SCHEMA = 'dbo'
                AND COLUMN_NAME NOT LIKE 'stg_%'
                AND DATA_TYPE IN ('decimal', 'numeric', 'int', 'bigint', 'float', 'real', 'money', 'smallmoney', 'smallint', 'tinyint')
                ORDER BY COLUMN_NAME
            """)
            
            schema_info = {}
            for row in cursor.fetchall():
                column_name = row[0]
                data_type = row[1]
                precision = row[2]
                scale = row[3]
                is_nullable = row[4]
                
                schema_info[column_name] = {
                    'data_type': data_type,
                    'precision': precision,
                    'scale': scale,
                    'is_nullable': is_nullable == 'YES'
                }
        
        logger.info(f"Dynamically identified {len(schema_info)} numeric columns with schema info")
        return schema_info
    
    def _clean_numeric_fields_dynamic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean numeric columns dynamically based on exact staging table schema with precision"""
        
        # Get detailed schema information
        numeric_schema = self.get_dynamic_numeric_fields_with_schema()
        
        if not numeric_schema:
            logger.info("No numeric columns found in staging table schema")
            return df
        
        # Filter to only columns that exist in the DataFrame
        existing_numeric_columns = [col for col in numeric_schema.keys() if col in df.columns]
        
        if not existing_numeric_columns:
            logger.info("No numeric columns found in DataFrame that need conversion")
            return df
        
        logger.info(f"Cleaning {len(existing_numeric_columns)} numeric fields with precise schema info")
        
        cleaned_df = df.copy()
        
        for col in existing_numeric_columns:
            schema_info = numeric_schema[col]
            data_type = schema_info['data_type']
            precision = schema_info['precision']
            scale = schema_info['scale']
            is_nullable = schema_info['is_nullable']
            
            def clean_value(val):
                # Handle null/empty values
                if pd.isna(val) or val == '' or str(val).strip().upper() in ['NULL', 'NONE', 'NAN']:
                    return None if is_nullable else 0
                
                try:
                    # Handle boolean-like strings
                    val_str = str(val).strip().upper()
                    if val_str in ['TRUE', 'FALSE']:
                        val = 1 if val_str == 'TRUE' else 0
                    
                    # Clean the string value
                    if isinstance(val, str):
                        # Remove currency symbols, commas, etc.
                        val = val.replace('$', '').replace(',', '').replace('%', '').strip()
                        if val == '':
                            return None if is_nullable else 0
                    
                    # Convert based on target data type
                    if data_type in ['int', 'bigint', 'smallint', 'tinyint']:
                        # Integer types
                        return int(float(val))
                        
                    elif data_type in ['decimal', 'numeric']:
                        # Decimal types with precision and scale
                        float_val = float(val)
                        
                        # Apply scale (decimal places)
                        if scale is not None and scale > 0:
                            # Round to the specified decimal places
                            rounded_val = round(float_val, scale)
                            return rounded_val
                        else:
                            # No decimal places, treat as integer
                            return int(float_val)
                            
                    elif data_type in ['float', 'real']:
                        # Float types
                        return float(val)
                        
                    elif data_type in ['money', 'smallmoney']:
                        # Money types (4 decimal places)
                        return round(float(val), 4)
                        
                    else:
                        # Default to float
                        return float(val)
                        
                except (ValueError, TypeError, OverflowError) as e:
                    default_val = None if is_nullable else 0
                    logger.warning(f"Could not convert '{val}' in column '{col}' ({data_type}) to numeric, using {default_val}: {e}")
                    return default_val
            
            original_count = len(cleaned_df[col].unique())
            cleaned_df[col] = cleaned_df[col].apply(clean_value)
            cleaned_count = len(cleaned_df[col].unique())
            
            # Log the conversion details
            logger.info(f"Cleaned numeric field '{col}' ({data_type}({precision},{scale})): {original_count} -> {cleaned_count} unique values")
        
        return cleaned_df
    
    def start_batch(self, customer_name: str, batch_type: str = 'FULL_BATCH') -> str:
        """Start a new batch and return batch_id"""
        batch_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO [dbo].[MON_BatchProcessing] 
                ([batch_id], [customer_name], [batch_type], [status], [start_time])
                VALUES (?, ?, ?, 'STARTED', GETDATE())
            """, (batch_id, customer_name, batch_type))
            conn.commit()
        
        logger.info(f"Started batch {batch_id} for customer {customer_name}")
        return batch_id
    
    def update_batch_status(self, batch_id: str, status: str, 
                           total_records: Optional[int] = None,
                           successful_records: Optional[int] = None,
                           failed_records: Optional[int] = None,
                           error_summary: Optional[str] = None) -> None:
        """Update batch processing status"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            update_parts = ["[status] = ?", "[end_time] = CASE WHEN ? IN ('COMPLETED', 'FAILED') THEN GETDATE() ELSE [end_time] END"]
            params = [status, status]
            
            if total_records is not None:
                update_parts.append("[total_records] = ?")
                params.append(total_records)
            
            if successful_records is not None:
                update_parts.append("[successful_records] = ?")
                params.append(successful_records)
            
            if failed_records is not None:
                update_parts.append("[failed_records] = ?")
                params.append(failed_records)
            
            if error_summary is not None:
                update_parts.append("[error_summary] = ?")
                params.append(error_summary)
            
            params.append(batch_id)
            
            query = f"""
                UPDATE [dbo].[MON_BatchProcessing] 
                SET {', '.join(update_parts)}
                WHERE [batch_id] = ?
            """
            cursor.execute(query, params)
            conn.commit()
        
        logger.info(f"Updated batch {batch_id} status to {status}")
    
    def concurrent_insert_chunk(self, chunk_data, columns, table_name):
        """Insert a chunk of data using concurrent processing"""
        chunk_df, chunk_id = chunk_data
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build insert statement
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join([f'[{col}]' for col in columns])
                insert_sql = f"INSERT INTO [dbo].[{table_name}] ({column_names}) VALUES ({placeholders})"
                
                # Prepare all rows for this chunk
                values_list = []
                for _, row in chunk_df.iterrows():
                    values = []
                    for col in columns:
                        value = row[col]
                        # Handle pandas NA/NaN values for SQL Server
                        if pd.isna(value):
                            values.append(None)
                        elif isinstance(value, (pd.Timestamp, pd.NaT.__class__)):
                            values.append(value if not pd.isna(value) else None)
                        else:
                            values.append(value)
                    values_list.append(tuple(values))
                  # Use executemany for bulk insert
                cursor.executemany(insert_sql, values_list)
                conn.commit()
                
                return len(chunk_df), 0, chunk_id  # success_count, fail_count, chunk_id
                
        except Exception as e:
            logger.error(f"Chunk {chunk_id} insert error: {e}")
            return 0, len(chunk_df), chunk_id  # success_count, fail_count, chunk_id

    def concurrent_bulk_insert(self, filtered_df, table_name, chunk_size=500, max_workers=4):
        """Production-grade concurrent database insert"""
        logger.info(f"Starting concurrent bulk insert of {len(filtered_df)} records...")
        logger.info(f"Chunk size: {chunk_size}, Max concurrent workers: {max_workers}")
        
        columns = list(filtered_df.columns)
        
        # Split DataFrame into chunks
        chunks = []
        for i in range(0, len(filtered_df), chunk_size):
            chunk = filtered_df.iloc[i:i + chunk_size]
            chunks.append((chunk, f"chunk_{i//chunk_size + 1}"))
        
        logger.info(f"Split into {len(chunks)} chunks for concurrent processing")
        
        # Use ThreadPoolExecutor for concurrent database operations
        total_success = 0
        total_failed = 0
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:            # Submit all chunks for concurrent processing
            futures = {
                executor.submit(self.concurrent_insert_chunk, chunk_data, columns, table_name): chunk_data[1] 
                for chunk_data in chunks
            }
            
            # Process completed chunks as they finish
            for future in concurrent.futures.as_completed(futures):
                chunk_name = futures[future]
                try:
                    success_count, fail_count, chunk_id = future.result()
                    total_success += success_count
                    total_failed += fail_count
                    
                    if success_count > 0:
                        logger.info(f"   SUCCESS {chunk_name}: {success_count} records inserted")
                    if fail_count > 0:
                        logger.error(f"   FAILED {chunk_name}: {fail_count} records failed")
                except Exception as e:
                    logger.error(f"   ERROR {chunk_name}: Exception occurred: {e}")
                    total_failed += chunk_size        
        elapsed_time = time.time() - start_time
        records_per_second = total_success / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"Concurrent insert completed: {total_success} success, {total_failed} failed")
        logger.info(f"Performance: {elapsed_time:.2f} seconds, {records_per_second:.1f} records/sec")
        
        return total_success

    def insert_orders_to_staging(self, orders_df: pd.DataFrame,
                                customer_batch: str, batch_id: str) -> int:
        """Insert transformed orders to staging table"""
        
        if orders_df.empty:
            return 0
        
        # Get the actual columns that exist in the staging table
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
                AND TABLE_SCHEMA = 'dbo'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]

        # --- UUID mapping logic (YAML-agnostic) ---
        # If the staging table expects a 'source_uuid', ensure it is present in the DataFrame.
        if 'source_uuid' in existing_columns:
            # If already present, do nothing
            if 'source_uuid' in orders_df.columns:
                pass
            # Try to map from common UUID columns
            elif 'record_uuid' in orders_df.columns:
                orders_df['source_uuid'] = orders_df['record_uuid']
            elif 'order_uuid' in orders_df.columns:
                orders_df['source_uuid'] = orders_df['order_uuid']
            else:
                logger.warning("No UUID field found in orders_df to map to source_uuid!")
        
        # If the staging table does not expect a source_uuid, do nothing
        # ─────────────────────────────────────────────────

        # Filter the DataFrame to only include columns that exist in the staging table
        available_data_columns = [col for col in orders_df.columns if col in existing_columns]
        filtered_df = orders_df[available_data_columns].copy()
        
        # DEBUG: Log basic column filtering information
        logger.info(f"Column filtering: {len(orders_df.columns)} -> {len(available_data_columns)} columns")
        
        # Check CUSTOMER SEASON specifically (key business logic)
        if 'CUSTOMER SEASON' in orders_df.columns and 'CUSTOMER SEASON' in available_data_columns:
            customer_season_value = orders_df.iloc[0]['CUSTOMER SEASON'] if not orders_df.empty else 'NO_DATA'
            logger.info(f"CUSTOMER SEASON value: '{customer_season_value}'")
        
        # Show columns that are being excluded (condensed)
        excluded_columns = [col for col in orders_df.columns if col not in existing_columns]
        if excluded_columns:
            logger.info(f"Excluded columns ({len(excluded_columns)}): {excluded_columns[:5]}{'...' if len(excluded_columns) > 5 else ''}")
        
        # Add staging-specific columns
        filtered_df['stg_batch_id'] = batch_id
        filtered_df['stg_customer_batch'] = customer_batch
        filtered_df['stg_status'] = 'PENDING'
        filtered_df['stg_created_date'] = datetime.now()
        
        # Apply Group naming business rule (CUSTOMER SEASON → AAG SEASON fallback)
        if 'CUSTOMER' in filtered_df.columns and 'CUSTOMER SEASON' in filtered_df.columns and 'AAG SEASON' in filtered_df.columns:
            def calculate_group_name(row):
                customer = str(row.get('CUSTOMER', '')).strip().upper()
                customer_season = str(row.get('CUSTOMER SEASON', '')).strip()
                aag_season = str(row.get('AAG SEASON', '')).strip()
                
                # Use AAG SEASON when CUSTOMER SEASON is blank/null
                if not customer_season or customer_season.lower() in ['', 'nan', 'none', 'null']:
                    effective_season = aag_season if aag_season else 'UNKNOWN_SEASON'
                else:
                    effective_season = customer_season
                
                return f"{customer} {effective_season}"
            
            filtered_df['Group'] = filtered_df.apply(calculate_group_name, axis=1)
            logger.info(f"Applied Group naming logic: CUSTOMER SEASON -> AAG SEASON fallback")            # Log sample group names for debugging
            if not filtered_df.empty:
                sample_groups = filtered_df['Group'].head(3).tolist()
                logger.info(f"Sample group names: {sample_groups}")
        else:
            logger.warning("Missing columns for Group naming logic (CUSTOMER, CUSTOMER SEASON, AAG SEASON)")
        
        # Clean numeric fields dynamically based on staging table schema
        filtered_df = self._clean_numeric_fields_dynamic(filtered_df)
        
        # SIMPLE INSERT to avoid MemoryError issues
        logger.info(f"Using simple insert for {len(filtered_df)} records...")
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get column names for dynamic insert
                columns = list(filtered_df.columns)
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join([f'[{col}]' for col in columns])
                
                insert_query = f"""
                    INSERT INTO [dbo].[STG_MON_CustMasterSchedule] ({column_names})
                    VALUES ({placeholders})
                """
                
                rows_inserted = 0
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    try:
                        values = []
                        for col in columns:
                            value = row[col]
                            if pd.isna(value):
                                values.append(None)
                            elif isinstance(value, (pd.Timestamp, pd.NaT.__class__)):
                                values.append(value if not pd.isna(value) else None)
                            else:
                                # Truncate very long strings to prevent issues
                                if isinstance(value, str) and len(value) > 4000:
                                    value = value[:4000]
                                values.append(value)
                        
                        cursor.execute(insert_query, values)
                        rows_inserted += 1
                        
                        if i % 10 == 0 and i > 0:
                            logger.info(f"Inserted {i}/{len(filtered_df)} records...")
                            
                    except Exception as row_error:
                        logger.error(f"Failed to insert row {i+1}: {row_error}")
                        # Continue with other rows instead of failing completely
                        
                conn.commit()
            
            elapsed_time = time.time() - start_time
            records_per_second = rows_inserted / elapsed_time if elapsed_time > 0 else 0
            logger.info(f"Simple insert completed: {rows_inserted}/{len(filtered_df)} records in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Simple insert failed: {e}")
            raise e        
        logger.info(f"Inserted {rows_inserted} orders to staging for batch {batch_id}")
        
        # Generate and insert subitems with foreign key relationship
        try:
            subitems_inserted = self.generate_and_insert_subitems(batch_id)
            logger.info(f"Generated and inserted {subitems_inserted} subitems for batch {batch_id}")
        except Exception as e:
            logger.error(f"Failed to generate subitems for batch {batch_id}: {e}")
            # Don't fail the entire operation for subitem generation issues
        
        return rows_inserted
    
    def get_pending_staging_orders(self, batch_id: str) -> pd.DataFrame:
        """Get orders ready for Monday.com API with ALL production columns"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all columns from staging table, excluding staging-specific ones
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
                AND TABLE_SCHEMA = 'dbo'
                AND COLUMN_NAME NOT LIKE 'stg_%'
                ORDER BY ORDINAL_POSITION
            """)
            production_columns = [row[0] for row in cursor.fetchall()]
            
            # Add required staging columns for processing
            staging_columns = ['stg_id', 'stg_batch_id', 'stg_customer_batch', 'stg_status']
            all_columns = staging_columns + production_columns
            
            # Build dynamic query with all available columns
            column_list = ', '.join([f'[{col}]' for col in all_columns])
            query = f"""
                SELECT {column_list}
                FROM [dbo].[STG_MON_CustMasterSchedule]
                WHERE [stg_batch_id] = ? AND [stg_status] = 'PENDING'
                ORDER BY [stg_id]
            """
            
            df = pd.read_sql(query, conn, params=[batch_id])
        
        logger.info(f"Retrieved {len(df)} pending orders for batch {batch_id} (columns: {len(all_columns)} total, {len(production_columns)} production)")
        return df
    
    def update_staging_with_monday_id(self, stg_id: int, monday_item_id: int, 
                                     api_payload: Optional[str] = None) -> bool:
        """Update staging record with Monday.com item ID and propagate to subitems"""
        
        # Convert numpy types to native Python types
        stg_id = int(stg_id)
        monday_item_id = int(monday_item_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if stg_api_payload column exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
                AND TABLE_SCHEMA = 'dbo'
                AND COLUMN_NAME = 'stg_api_payload'
            """)
            has_api_payload = len(cursor.fetchall()) > 0
            
            if has_api_payload:
                cursor.execute("""
                    UPDATE [dbo].[STG_MON_CustMasterSchedule]
                    SET [stg_status] = 'API_SUCCESS',
                        [stg_monday_item_id] = ?,
                        [stg_processed_date] = GETDATE(),
                        [stg_api_payload] = ?
                    WHERE [stg_id] = ?
                """, (monday_item_id, api_payload, stg_id))
            else:
                cursor.execute("""
                    UPDATE [dbo].[STG_MON_CustMasterSchedule]
                    SET [stg_status] = 'API_SUCCESS',
                        [stg_monday_item_id] = ?,
                        [stg_processed_date] = GETDATE()
                    WHERE [stg_id] = ?
                """, (monday_item_id, stg_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
        
        if rows_affected > 0:
            logger.info(f"Updated staging record {stg_id} with Monday item ID {monday_item_id}")
            
            # CRITICAL FIX: Propagate Monday.com item ID to subitems
            # This enables subitems to be found by create_monday_subitems_from_staging()
            try:
                subitems_updated = self.update_subitems_parent_item_id(stg_id, monday_item_id)
                logger.info(f"Propagated Monday item ID {monday_item_id} to {subitems_updated} subitems for parent stg_id {stg_id}")
            except Exception as e:
                logger.error(f"❌ Failed to propagate Monday item ID to subitems for stg_id {stg_id}: {e}")
                # Don't fail the entire operation for subitem propagation issues
            
        else:
            logger.warning(f"No staging record found with ID {stg_id}")
        return rows_affected > 0
    
    def mark_staging_as_failed(self, stg_id: int, error_message: str, 
                              api_payload: Optional[str] = None) -> bool:
        """Mark staging record as failed"""
        
        # Convert numpy types to native Python types
        stg_id = int(stg_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if optional columns exist
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
                AND TABLE_SCHEMA = 'dbo'
                AND COLUMN_NAME IN ('stg_api_payload', 'stg_retry_count')
            """)
            existing_optional_columns = [row[0] for row in cursor.fetchall()]
            
            has_api_payload = 'stg_api_payload' in existing_optional_columns
            has_retry_count = 'stg_retry_count' in existing_optional_columns
            
            # Build update query based on available columns
            if has_api_payload and has_retry_count:
                cursor.execute("""
                    UPDATE [dbo].[STG_MON_CustMasterSchedule]
                    SET [stg_status] = 'API_FAILED',
                        [stg_error_message] = ?,
                        [stg_processed_date] = GETDATE(),
                        [stg_api_payload] = ?,
                        [stg_retry_count] = [stg_retry_count] + 1
                    WHERE [stg_id] = ?
                """, (error_message, api_payload, stg_id))
            elif has_api_payload:
                cursor.execute("""
                    UPDATE [dbo].[STG_MON_CustMasterSchedule]
                    SET [stg_status] = 'API_FAILED',
                        [stg_error_message] = ?,
                        [stg_processed_date] = GETDATE(),
                        [stg_api_payload] = ?
                    WHERE [stg_id] = ?
                """, (error_message, api_payload, stg_id))
            else:
                cursor.execute("""
                    UPDATE [dbo].[STG_MON_CustMasterSchedule]
                    SET [stg_status] = 'API_FAILED',
                        [stg_error_message] = ?,
                        [stg_processed_date] = GETDATE()
                    WHERE [stg_id] = ?
                """, (error_message, stg_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
        
        if rows_affected > 0:
            logger.warning(f"Marked staging record {stg_id} as failed: {error_message}")
        
        return rows_affected > 0
    
    def get_successful_orders_for_subitems(self, batch_id: str) -> pd.DataFrame:
        """Get successfully created orders for subitem processing"""
        
        # Get the actual columns that exist in the staging table
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
                AND TABLE_SCHEMA = 'dbo'
                ORDER BY ORDINAL_POSITION            """)
            all_columns = [row[0] for row in cursor.fetchall()]
        
        # Define columns we want to select (Monday.com target names after transformation)
        desired_columns = [
            'stg_id', 'stg_batch_id', 'stg_customer_batch', 
            'stg_monday_item_id', 'AAG ORDER NUMBER', 'STYLE', 'COLOR',
            'PO NUMBER', 'CUSTOMER ALT PO'
        ]
        
        # Filter to only include columns that actually exist
        available_columns = [col for col in desired_columns if col in all_columns]
        
        # Build dynamic query
        column_list = ', '.join([f'[{col}]' for col in available_columns])
        query = f"""
            SELECT {column_list}
            FROM [dbo].[STG_MON_CustMasterSchedule]
            WHERE [stg_batch_id] = ? AND [stg_status] = 'API_SUCCESS'
            ORDER BY [stg_id]
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=[batch_id])
        
        logger.info(f"Retrieved {len(df)} successful orders for subitem processing (columns: {available_columns})")
        return df
    
    def insert_subitems_to_staging(self, subitems_df: pd.DataFrame, 
                                batch_id: str) -> int:
        """Insert unpivoted subitems to staging table using direct INSERT"""
        """We should only be using this code path for new subitem records."""
        
        if subitems_df.empty:
            return 0
        
        # Add required staging columns
        insert_df = subitems_df.copy()
        insert_df['stg_batch_id'] = batch_id
        insert_df['stg_status'] = 'PENDING'
        insert_df['stg_created_date'] = datetime.now()
        insert_df['stg_retry_count'] = 0
        
        # Get the actual columns that exist in the target table
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
                AND TABLE_SCHEMA = 'dbo'
                ORDER BY ORDINAL_POSITION
            """)
            target_columns = [row[0] for row in cursor.fetchall()]
        
        # Filter DataFrame to only include columns that exist in target table
        available_columns = [col for col in insert_df.columns if col in target_columns]
        filtered_df = insert_df[available_columns].copy()
        
        logger.info(f"Column filtering: {len(insert_df.columns)} -> {len(available_columns)} columns")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.fast_executemany = True
            
            try:
                # Build dynamic INSERT based on available columns
                columns = list(filtered_df.columns)
                placeholders = ','.join(['?' for _ in columns])
                column_list = ','.join([f'[{col}]' for col in columns])
                
                insert_query = f"""
                    INSERT INTO [dbo].[STG_MON_CustMasterSchedule_Subitems]
                    ({column_list})
                    VALUES ({placeholders})
                """
                
                start_time = time.time()
                logger.info(f"Starting bulk insert of {len(filtered_df)} records...")
                
                # Prepare values list with proper type handling
                values = []
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    row_values = []
                    for col in columns:
                        val = row[col]
                        if pd.isna(val):
                            row_values.append(None)
                        elif isinstance(val, (np.integer, int)):
                            row_values.append(int(val))
                        elif isinstance(val, (np.floating, float)):
                            row_values.append(float(val))
                        elif isinstance(val, pd.Timestamp):
                            row_values.append(val.to_pydatetime())
                        elif isinstance(val, datetime):
                            row_values.append(val)
                        else:
                            row_values.append(str(val))
                    row_values_tuple = tuple(row_values)
                    values.append(row_values_tuple)
                    
                    # Log first few rows for debugging
                    if i < 3:
                        logger.debug(f"Row {i}: {row_values_tuple}")
                
                logger.info(f"Prepared {len(values)} value tuples for insertion")
                
                # Execute bulk insert
                cursor.executemany(insert_query, values)
                rows_inserted = len(values)
                conn.commit()
                
                elapsed_time = time.time() - start_time
                records_per_second = rows_inserted / elapsed_time if elapsed_time > 0 else 0
                
                logger.info(f"Completed bulk insert: {rows_inserted} records in {elapsed_time:.2f} seconds")
                logger.info(f"Performance: {records_per_second:.1f} records/second")
                
                return rows_inserted
                
            except Exception as e:
                logger.error(f"Failed to perform bulk insert: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception args: {e.args}")
                
                # Enhanced error logging
                import traceback
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                
                # Log the problematic data for debugging
                logger.error(f"DataFrame shape: {filtered_df.shape}")
                logger.error(f"DataFrame columns: {list(filtered_df.columns)}")
                logger.error(f"DataFrame dtypes:\n{filtered_df.dtypes}")
                
                # Log sample data
                if not filtered_df.empty:
                    logger.error(f"Sample row:\n{filtered_df.iloc[0].to_dict()}")
                
                # Log sample prepared values
                if values:
                    logger.error(f"Sample prepared value tuple: {values[0]}")
                    logger.error(f"Value tuple types: {[type(v) for v in values[0]]}")
                
                conn.rollback()
                raise
    
    def cleanup_successful_staging(self, batch_id: str) -> int:
        """Clean up successful staging records after promotion"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete promoted subitems first (due to FK constraint)
            cursor.execute("""
                DELETE FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
                WHERE [stg_batch_id] = ? AND [stg_status] = 'PROMOTED'
            """, (batch_id,))
            
            subitems_deleted = cursor.rowcount
            
            # Delete promoted orders
            cursor.execute("""
                DELETE FROM [dbo].[STG_MON_CustMasterSchedule]
                WHERE [stg_batch_id] = ? AND [stg_status] = 'PROMOTED'
            """, (batch_id,))
            
            orders_deleted = cursor.rowcount
            total_deleted = orders_deleted + subitems_deleted
            
            conn.commit()
        
        logger.info(f"Cleaned up {total_deleted} staging records for batch {batch_id}")
        return total_deleted

    def _fast_executemany_insert(self, filtered_df, table_name):
        """Fallback fast bulk insert using pyodbc fast_executemany"""
        logger.info(f"Using fast_executemany for {len(filtered_df)} records...")
        start_time = time.time()
        
        # Debug: Check data size and types
        logger.info(f"DataFrame memory usage: {filtered_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        logger.info(f"DataFrame shape: {filtered_df.shape}")
        
        # Check for very large text fields that might cause memory issues
        for col in filtered_df.columns:
            if filtered_df[col].dtype == 'object':  # String columns
                max_len = filtered_df[col].astype(str).str.len().max()
                if max_len > 1000:  # Flag very long text fields
                    logger.warning(f"Column '{col}' has max length {max_len} characters")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.fast_executemany = True  # Enable fast bulk inserts
                
                # Get column names for dynamic insert
                columns = list(filtered_df.columns)
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join([f'[{col}]' for col in columns])
                
                insert_query = f"""
                    INSERT INTO [dbo].[{table_name}] ({column_names})
                    VALUES ({placeholders})
                """
                
                logger.info(f"Preparing bulk data for {len(filtered_df)} records...")
                
                # Prepare bulk data with better memory management
                bulk_values = []
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    if i % 1000 == 0:  # Progress logging
                        logger.info(f"Processed {i}/{len(filtered_df)} records for bulk insert...")
                    
                    values = []
                    for col in columns:
                        value = row[col]
                        if pd.isna(value):
                            values.append(None)
                        elif isinstance(value, (pd.Timestamp, pd.NaT.__class__)):
                            values.append(value if not pd.isna(value) else None)
                        else:
                            # Truncate very long strings to prevent memory issues
                            if isinstance(value, str) and len(value) > 8000:
                                logger.warning(f"Truncating long string in column '{col}' from {len(value)} to 8000 chars")
                                value = value[:8000]
                            values.append(value)
                    bulk_values.append(tuple(values))
                
                logger.info(f"Executing bulk insert with {len(bulk_values)} records...")
                
                # Use smaller batches to avoid memory issues
                batch_size = 10  # Much smaller batches
                for i in range(0, len(bulk_values), batch_size):
                    batch = bulk_values[i:i + batch_size]
                    logger.info(f"Inserting batch {i//batch_size + 1}: records {i+1}-{min(i+batch_size, len(bulk_values))}")
                    cursor.executemany(insert_query, batch)
                    conn.commit()
                    logger.info(f"Batch {i//batch_size + 1} completed successfully")
            
            elapsed_time = time.time() - start_time
            records_per_second = len(filtered_df) / elapsed_time if elapsed_time > 0 else 0
            logger.info(f"Fast_executemany completed: {len(filtered_df)} records in {elapsed_time:.2f} seconds, {records_per_second:.1f} records/sec")
            
            return len(filtered_df)
            
        except Exception as e:
            logger.error(f"Fast_executemany failed with error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'args') and e.args:
                logger.error(f"Error details: {e.args}")
            raise

    def generate_and_insert_subitems(self, orders_df: pd.DataFrame, batch_id: str) -> int:
        """Generate subitems with proper parent relationship using foreign key"""
        
        if orders_df.empty:
            logger.info("No orders provided for subitem generation")
            return 0
        
        logger.info(f"Generating SUBITEMS for {len(orders_df)} orders in batch {batch_id}")
        
        # First, get the stg_id values for inserted orders
        parent_query = """
            SELECT stg_id, [AAG ORDER NUMBER], [STYLE], [COLOR]
            FROM STG_MON_CustMasterSchedule
            WHERE stg_batch_id = ?
        """
        
        with self.get_connection() as conn:
            parent_mapping = pd.read_sql(parent_query, conn, params=[batch_id])
        
        if parent_mapping.empty:
            logger.warning(f"No parent orders found in staging for batch {batch_id}")
            return 0
        
        logger.info(f"Found {len(parent_mapping)} parent orders for subitem generation")
        
        # Generate subitems with parent_stg_id
        all_subitems = []
        
        for _, order in orders_df.iterrows():
            # Find parent stg_id
            parent_row = parent_mapping[
                (parent_mapping['AAG ORDER NUMBER'] == order['AAG ORDER NUMBER']) &
                (parent_mapping['STYLE'] == order.get('STYLE', '')) &
                (parent_mapping['COLOR'] == order.get('COLOR', ''))
            ]
            
            if parent_row.empty:
                logger.warning(f"No parent found for order {order.get('AAG ORDER NUMBER', 'Unknown')}")
                continue
                
            parent_stg_id = parent_row['stg_id'].iloc[0]
            
            # Define size columns to process (between UNIT_OF_MEASURE and TOTAL_QTY)
            size_columns = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'OS']
            
            # Generate subitem for each size with positive quantity
            for size_col in size_columns:
                if size_col in order.index:
                    qty = order[size_col]
                    if pd.notna(qty) and float(qty) > 0:
                        subitem = {
                            'stg_parent_stg_id': parent_stg_id,
                            'stg_batch_id': batch_id,
                            'stg_status': 'PENDING',
                            'stg_created_date': datetime.now(),
                            'stg_retry_count': 0,
                            'AAG_ORDER_NUMBER': order.get('AAG ORDER NUMBER'),
                            'STYLE': order.get('STYLE'),
                            'COLOR': order.get('COLOR'),
                            'PO_NUMBER': order.get('PO NUMBER'),
                            'CUSTOMER_ALT_PO': order.get('CUSTOMER ALT PO'),
                            'CUSTOMER': order.get('CUSTOMER'),
                            'Size': size_col,
                            'ORDER_QTY': float(qty),
                            'UNIT_OF_MEASURE': order.get('UNIT OF MEASURE'),
                            'Order Qty': str(int(float(qty)))  # Monday.com format
                        }
                        all_subitems.append(subitem)
        
        if not all_subitems:
            logger.info("No subitems generated (no positive quantities found)")
            return 0
        
        # Convert to DataFrame and insert
        subitems_df = pd.DataFrame(all_subitems)
        logger.info(f"Generated {len(subitems_df)} subitems for insertion")

        # print subitems_df as table
        print(f"Sending batch id {batch_id} to get added to staging table")
        print(subitems_df.to_string(index=False))
        
        # Use existing bulk insert method
        return self.insert_subitems_to_staging(subitems_df, batch_id)

    def update_subitems_parent_item_id(self, parent_stg_id: int, monday_item_id: int) -> int:
        """Update subitems with parent Monday.com item ID using foreign key"""
        
        query = """
            UPDATE STG_MON_CustMasterSchedule_Subitems
            SET stg_monday_parent_item_id = ?
            WHERE stg_parent_stg_id = ?
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (monday_item_id, parent_stg_id))
            updated = cursor.rowcount
            conn.commit()
            
        logger.info(f"Updated {updated} subitems with parent_item_id {monday_item_id} for parent stg_id {parent_stg_id}")
        return updated

    def cleanup_staging_batch(self, batch_id: str) -> Dict[str, int]:
        """Clean up successfully processed staging records using CASCADE DELETE"""
        
        results = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, count what we're about to delete (before deletion)
            count_query = """
                SELECT COUNT(*) 
                FROM STG_MON_CustMasterSchedule_Subitems sub
                INNER JOIN STG_MON_CustMasterSchedule parent
                    ON sub.stg_parent_stg_id = parent.stg_id
                WHERE parent.stg_batch_id = ? AND parent.stg_status = 'API_SUCCESS'
            """
            cursor.execute(count_query, (batch_id,))
            results['subitems_deleted'] = cursor.fetchone()[0]
            
            # With CASCADE DELETE, we only need to delete parent records
            # Children will be automatically deleted
            order_query = """
                DELETE FROM STG_MON_CustMasterSchedule
                WHERE stg_batch_id = ? AND stg_status = 'API_SUCCESS'
            """
            
            cursor.execute(order_query, (batch_id,))
            results['orders_deleted'] = cursor.rowcount
            
            conn.commit()
        
        logger.info(f"Cleaned up batch {batch_id}: {results}")
        return results

    def update_subitem_with_monday_id(self, stg_subitem_id: int, monday_subitem_id: int) -> None:
        """Update staging subitem with Monday.com subitem ID"""
        
        query = """
            UPDATE STG_MON_CustMasterSchedule_Subitems
            SET stg_monday_subitem_id = ?,
                stg_status = 'API_SUCCESS',
                stg_processed_date = GETDATE()
            WHERE stg_id = ?
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (monday_subitem_id, stg_subitem_id))
            conn.commit()
            
        logger.info(f"Updated subitem stg_id {stg_subitem_id} with Monday.com subitem ID {monday_subitem_id}")

    def mark_subitem_as_failed(self, stg_subitem_id: int, error_message: str) -> None:
        """Mark staging subitem as failed"""
        
        query = """
            UPDATE STG_MON_CustMasterSchedule_Subitems
            SET stg_status = 'API_FAILED',
                stg_error_message = ?,
                stg_processed_date = GETDATE(),
                stg_retry_count = stg_retry_count + 1
            WHERE stg_id = ?
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (error_message, stg_subitem_id))
            conn.commit()
            
        logger.warning(f"Marked subitem stg_id {stg_subitem_id} as failed: {error_message}")

    def generate_and_insert_subitems(self, batch_id: str) -> int:
        """Generate subitems using SQL JOIN + smart column detection"""
        
        logger.info(f"Generating subitems from second function for batch {batch_id}")
        
        # OPTION 3: Single query to get staging metadata + original size data
        combined_query = """
            SELECT 
                stg.stg_id as stg_parent_stg_id, 
                stg.stg_batch_id, 
                'PENDING' as stg_status, 
                GETDATE() as stg_created_date,
                ou.*
            FROM [dbo].[STG_MON_CustMasterSchedule] as stg
            JOIN [dbo].[ORDERS_UNIFIED] ou ON ou.record_uuid = stg.source_uuid
            WHERE stg.stg_batch_id = ?
        """
        
        with self.get_connection() as conn:
            combined_df = pd.read_sql(combined_query, conn, params=[batch_id])

        
        if combined_df.empty:
            logger.warning(f"No orders found for subitem generation in batch {batch_id}")
            return 0
        
        logger.info(f"Found {len(combined_df)} orders for subitem generation")
        
        # Apply smart column detection (borrowed from get_subitems_for_order)
        all_subitems = []
        
        for _, row in combined_df.iterrows():
            # Identify candidate size columns by slicing between markers
            cols = combined_df.columns.tolist()
            try:
                start = cols.index('UNIT OF MEASURE') + 1
                end = cols.index('TOTAL QTY')
                candidate_cols = cols[start:end]
            except ValueError:
                # Fallback: everything except the known key fields
                candidate_cols = [c for c in cols
                                  if c not in
                                  ['AAG ORDER NUMBER', 'CUSTOMER STYLE',
                                   'CUSTOMER COLOUR DESCRIPTION', 'stg_parent_stg_id',
                                   'stg_batch_id', 'stg_status', 'stg_created_date']]
            
            # Create a single-row DataFrame for melting
            row_df = pd.DataFrame([row])
            
            # Unpivot & filter in one go
            melted = (
                row_df
                .melt(
                    id_vars=['AAG ORDER NUMBER', 'CUSTOMER STYLE', 'CUSTOMER COLOUR DESCRIPTION', 
                             'stg_parent_stg_id', 'stg_batch_id', 'stg_status', 'stg_created_date'],
                    value_vars=candidate_cols,
                    var_name='Size',
                    value_name='Qty'
                )
                # coerce to numeric and drop zeros / NaN
                .assign(
                    Qty=lambda df: pd.to_numeric(df['Qty'], errors='coerce')
                )
                .query("Qty > 0")
            )
            
            if not melted.empty:
                # Map columns for staging table
                melted = melted.rename(columns={
                    'CUSTOMER STYLE': 'STYLE',
                    'CUSTOMER COLOUR DESCRIPTION': 'COLOR',
                    'Qty': 'ORDER_QTY'
                })
                
                # Add required staging columns
                melted['AAG_ORDER_NUMBER'] = melted['AAG ORDER NUMBER'] 
                melted['Order Qty'] = melted['ORDER_QTY'].astype(str)
                
                # Keep only required columns for staging insert
                final_cols = [
                    'stg_parent_stg_id', 'stg_batch_id', 'stg_status', 'stg_created_date',
                    'AAG_ORDER_NUMBER', 'STYLE', 'COLOR', 'Size', 'ORDER_QTY', 'Order Qty'
                ]
                
                subitem_df = melted[final_cols]
                all_subitems.append(subitem_df)


        
        if not all_subitems:
            logger.info("No subitems generated (no positive quantities found)")
            return 0
        
        # Combine all subitems and insert
        final_subitems_df = pd.concat(all_subitems, ignore_index=True)
        logger.info(f"Generated {len(final_subitems_df)} subitems for insertion")
        
        # Use existing insert method (which already adds stg_batch_id, etc.)
        return self.insert_subitems_to_staging(final_subitems_df, batch_id)

    def cleanup_all_completed_staging(self) -> Dict[str, int]:
        """Clean up all completed staging records regardless of batch ID"""
        
        results = {'orders_deleted': 0, 'subitems_deleted': 0, 'orphans_deleted': 0}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, count and delete orphaned subitems (subitems without parents)
            orphan_count_query = """
                SELECT COUNT(*) 
                FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
                LEFT JOIN [dbo].[STG_MON_CustMasterSchedule] parent
                    ON sub.stg_parent_stg_id = parent.stg_id
                WHERE parent.stg_id IS NULL
            """
            cursor.execute(orphan_count_query)
            orphan_count = cursor.fetchone()[0]
            
            if orphan_count > 0:
                orphan_delete_query = """
                    DELETE FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
                    WHERE NOT EXISTS (
                        SELECT 1 FROM [dbo].[STG_MON_CustMasterSchedule]
                        WHERE [dbo].[STG_MON_CustMasterSchedule].stg_id = [dbo].[STG_MON_CustMasterSchedule_Subitems].stg_parent_stg_id
                    )
                """
                cursor.execute(orphan_delete_query)
                results['orphans_deleted'] = cursor.rowcount
                logger.info(f"Deleted {results['orphans_deleted']} orphaned subitems")
            
            # Count subitems that will be deleted with successful parents
            subitem_count_query = """
                SELECT COUNT(*) 
                FROM STG_MON_CustMasterSchedule_Subitems sub
                INNER JOIN STG_MON_CustMasterSchedule parent
                    ON sub.stg_parent_stg_id = parent.stg_id
                WHERE parent.stg_status = 'API_SUCCESS'
            """
            cursor.execute(subitem_count_query)
            results['subitems_deleted'] = cursor.fetchone()[0]
            
            # Delete successful orders (CASCADE will handle subitems)
            order_delete_query = """
                DELETE FROM STG_MON_CustMasterSchedule
                WHERE stg_status = 'API_SUCCESS'
            """
            cursor.execute(order_delete_query)
            results['orders_deleted'] = cursor.rowcount
            
            conn.commit()
        
        logger.info(f"Cleaned up all completed staging: {results}")
        return results

    def promote_dbhelper(self, batch_id: str = None) -> Tuple[int, int]:
        """
        Test DB connection and query using db_helper.
        Returns (row_count, 0) for compatibility.
        """
        import utils.db_helper as db
        try:
            result = db.run_query("SELECT TOP 5 * FROM dbo.ORDERS_UNIFIED", "orders")
            print("Sample from ORDERS:\n", result)
            return (len(result), 0)
        except Exception as e:
            print(f"❌ DB test failed: {e}")
            return (0, 0)


    def promote_successful_orders_to_production(self, batch_id: str) -> Tuple[int, int]:
        """
        Promote successful staging records to production MON_ tables using mapping file
        
        Args:
            batch_id: The batch to promote
            
        Returns:
            Tuple of (orders_promoted, subitems_promoted)
        """
        logger.info(f"Promoting successful records from batch {batch_id} to production")

        # Load mapping file
        try:
            mapping_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'mapping', 'stg_to_mon_promotion_mapping.json')
            with open(mapping_file_path, 'r') as f:
                mapping = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load mapping file: {e}")
            raise

        # Get column mappings for orders
        orders_mappings = mapping['tables']['orders']['mappings']
        
        # Build column lists for INSERT
        mapped_columns = []
        select_columns = []
        
        for mon_col, mapping_info in orders_mappings.items():
            if 'stg_column' in mapping_info and 'mon_column' in mapping_info:
                mapped_columns.append(f"[{mapping_info['mon_column']}]")
                select_columns.append(f"[{mapping_info['stg_column']}]")
                
        orders_promoted = 0
        subitems_promoted = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Build dynamic INSERT based on mapping
                promote_orders_query = f"""
                    INSERT INTO [dbo].[MON_CustMasterSchedule] (
                        {', '.join(mapped_columns)}
                    )
                    SELECT 
                        {', '.join(select_columns)}
                    FROM [dbo].[STG_MON_CustMasterSchedule]
                    WHERE stg_batch_id = ? 
                      AND stg_status = 'API_SUCCESS'
                      AND stg_monday_item_id IS NOT NULL
                """
                
                # logger.info(f"Generated promotion query:\n{promote_orders_query}")
                
                cursor.execute(promote_orders_query, (batch_id,))
                orders_promoted = cursor.rowcount
                
                # Step 2: Promote successful subitems using mapping file
                subitems_mappings = mapping['tables']['subitems']['mappings']
                
                # Build column lists for subitem INSERT
                subitem_mapped_columns = []
                subitem_select_columns = []
                
                for mon_col, mapping_info in subitems_mappings.items():
                    if 'stg_column' in mapping_info and 'mon_column' in mapping_info:
                        subitem_mapped_columns.append(f"[{mapping_info['mon_column']}]")
                        subitem_select_columns.append(f"sub.[{mapping_info['stg_column']}]")
                
                promote_subitems_query = f"""
                    INSERT INTO [dbo].[MON_CustMasterSchedule_Subitems] (
                        {', '.join(subitem_mapped_columns)}
                    )
                    SELECT 
                        {', '.join(subitem_select_columns)}
                    FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
                    INNER JOIN [dbo].[STG_MON_CustMasterSchedule] parent
                        ON sub.stg_parent_stg_id = parent.stg_id
                    WHERE parent.stg_batch_id = ?
                      AND parent.stg_status = 'API_SUCCESS' 
                      AND sub.stg_status = 'API_SUCCESS'
                      AND sub.stg_monday_subitem_id IS NOT NULL
                """
                
                # logger.info(f"Generated subitem promotion query:\n{promote_subitems_query}")
                
                cursor.execute(promote_subitems_query, (batch_id,))
                subitems_promoted = cursor.rowcount
                
                # Step 3: Update staging records to mark as promoted
                mark_promoted_query = """
                    UPDATE [dbo].[STG_MON_CustMasterSchedule] 
                    SET stg_status = 'PROMOTED'
                    WHERE stg_batch_id = ? 
                      AND stg_status = 'API_SUCCESS'
                      AND stg_monday_item_id IS NOT NULL
                """
                cursor.execute(mark_promoted_query, (batch_id,))
                
                # Mark subitems as promoted
                # Note: This assumes subitems are linked to parent items via stg_parent_stg_id
                mark_subitems_promoted_query = """
                    UPDATE sub
                    SET stg_status = 'PROMOTED'
                    FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
                    INNER JOIN [dbo].[STG_MON_CustMasterSchedule] parent
                        ON sub.stg_parent_stg_id = parent.stg_id
                    WHERE parent.stg_batch_id = ?
                    AND parent.stg_status = 'PROMOTED'
                    AND sub.stg_monday_subitem_id IS NOT NULL
                """


                cursor.execute(mark_subitems_promoted_query, (batch_id,))
                
                conn.commit()
                
                logger.info(f"Promoted to production: {orders_promoted} orders, {subitems_promoted} subitems")
                return orders_promoted, subitems_promoted
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to promote records to production: {e}")
                raise

    def validate_promotion_success(self, batch_id: str) -> Dict[str, any]:
        """
        Validate that promotion was successful by comparing staging vs production counts
        
        Args:
            batch_id: The batch to validate
            
        Returns:
            Dictionary with validation results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count staging records that should have been promoted
            cursor.execute("""
                SELECT COUNT(*) FROM [dbo].[STG_MON_CustMasterSchedule]
                WHERE stg_batch_id = ? AND stg_status = 'PROMOTED'
            """, (batch_id,))
            staging_orders_promoted = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
                INNER JOIN [dbo].[STG_MON_CustMasterSchedule] parent
                    ON sub.stg_parent_stg_id = parent.stg_id
                WHERE parent.stg_batch_id = ? AND sub.stg_status = 'PROMOTED'
            """, (batch_id,))
            staging_subitems_promoted = cursor.fetchone()[0]
            
            # Get Monday.com item IDs from promoted staging records
            cursor.execute("""
                SELECT stg_monday_item_id FROM [dbo].[STG_MON_CustMasterSchedule]
                WHERE stg_batch_id = ? AND stg_status = 'PROMOTED'
                  AND stg_monday_item_id IS NOT NULL
            """, (batch_id,))
            promoted_item_ids = [row[0] for row in cursor.fetchall()]
            
            # Count corresponding records in production tables
            production_orders_count = 0
            production_subitems_count = 0
            
            if promoted_item_ids:
                item_ids_str = ','.join(map(str, promoted_item_ids))
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM [dbo].[MON_CustMasterSchedule]
                    WHERE [Item ID] IN ({item_ids_str})
                """)
                production_orders_count = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM [dbo].[MON_CustMasterSchedule_Subitems]
                    WHERE [parent_item_id] IN ({item_ids_str})
                """)
                production_subitems_count = cursor.fetchone()[0]
            
            validation_result = {
                'batch_id': batch_id,
                'staging_orders_promoted': staging_orders_promoted,
                'staging_subitems_promoted': staging_subitems_promoted,
                'production_orders_found': production_orders_count,
                'production_subitems_found': production_subitems_count,
                'orders_match': staging_orders_promoted == production_orders_count,
                'subitems_match': staging_subitems_promoted == production_subitems_count,
                'validation_passed': (staging_orders_promoted == production_orders_count and 
                                    staging_subitems_promoted == production_subitems_count),
                'promoted_item_ids': promoted_item_ids
            }
            
            logger.info(f"Promotion validation: {validation_result}")
            return validation_result

    def cleanup_promoted_staging_records(self, batch_id: str) -> Dict[str, int]:
        """
        Clean up staging records that have been successfully promoted to production
        
        Args:
            batch_id: The batch to clean up
            
        Returns:
            Dictionary with cleanup results
        """
        logger.info(f"Cleaning up promoted staging records for batch {batch_id}")
        
        results = {'orders_deleted': 0, 'subitems_deleted': 0}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Count subitems that will be deleted (for reporting)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
                    INNER JOIN [dbo].[STG_MON_CustMasterSchedule] parent
                        ON sub.stg_parent_stg_id = parent.stg_id
                    WHERE parent.stg_batch_id = ? AND parent.stg_status = 'PROMOTED'
                """, (batch_id,))
                results['subitems_deleted'] = cursor.fetchone()[0]
                
                # Delete promoted orders (CASCADE will handle subitems)
                cursor.execute("""
                    DELETE FROM [dbo].[STG_MON_CustMasterSchedule]
                    WHERE stg_batch_id = ? AND stg_status = 'PROMOTED'
                """, (batch_id,))
                results['orders_deleted'] = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleaned up promoted staging: {results}")
                return results
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to clean up promoted staging records: {e}")
                raise
