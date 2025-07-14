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
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from .staging_config import get_config, DATABASE_CONFIG

logger = logging.getLogger(__name__)

class StagingOperations:
    """Handles all staging table operations"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.config = get_config()
    
    def get_connection(self) -> pyodbc.Connection:
        """Get database connection with proper configuration"""
        return pyodbc.connect(
            self.connection_string,
            timeout=DATABASE_CONFIG['connection_timeout']
        )
    
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
            existing_columns = [row[0] for row in cursor.fetchall()]        # Filter the DataFrame to only include columns that exist in the staging table
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
        """Update staging record with Monday.com item ID"""
        
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
        """Insert unpivoted subitems to staging table"""
        
        if subitems_df.empty:
            return 0
        
        # Add staging-specific columns
        subitems_df = subitems_df.copy()
        subitems_df['stg_batch_id'] = batch_id
        subitems_df['stg_status'] = 'PENDING'
        subitems_df['stg_created_date'] = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
              # Get column names for dynamic insert
            columns = list(subitems_df.columns)
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join([f'[{col}]' for col in columns])
            
            insert_query = f"""
                INSERT INTO [dbo].[STG_MON_CustMasterSchedule_Subitems] ({column_names})
                VALUES ({placeholders})
            """
            
            # Prepare bulk data for executemany (much faster than row-by-row)
            bulk_values = []
            for _, row in subitems_df.iterrows():
                values = []
                for col in columns:
                    value = row[col]
                    # Handle pandas NA/NaN values for SQL Server
                    if pd.isna(value):
                        values.append(None)
                    else:
                        values.append(value)
                bulk_values.append(tuple(values))
              # Execute bulk insert in chunks for better performance
            chunk_size = DATABASE_CONFIG.get('bulk_insert_batch_size', 1000)
            logger.info(f"Executing bulk insert of {len(bulk_values)} subitem records in chunks of {chunk_size}...")
            
            rows_inserted = 0
            for i in range(0, len(bulk_values), chunk_size):
                chunk = bulk_values[i:i + chunk_size]
                logger.info(f"Inserting subitem chunk {i//chunk_size + 1}: {len(chunk)} records...")
                cursor.executemany(insert_query, chunk)
                rows_inserted += len(chunk)
                
                # Commit each chunk
                conn.commit()
                
            logger.info(f"Completed subitem bulk insert: {rows_inserted} records")
        
        logger.info(f"Inserted {rows_inserted} subitems to staging for batch {batch_id}")
        return rows_inserted
    
    def promote_successful_records(self, batch_id: str) -> Tuple[int, int]:
        """Move successful records from staging to production tables"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Promote main orders
            cursor.execute("""
                INSERT INTO [dbo].[MON_CustMasterSchedule] 
                SELECT [Title], [UpdateDate], [Group], [Subitems], [CUSTOMER], 
                       [AAG ORDER NUMBER], [AAG SEASON], [ORDER DATE PO RECEIVED],
                       [CUSTOMER SEASON], [DROP], [PO NUMBER], [CUSTOMER ALT PO],
                       [STYLE], [STYLE DESCRIPTION], [ALIAS RELATED ITEM], [COLOR],
                       [CATEGORY], [PATTERN ID], [UNIT OF MEASURE], [FCST QTY],
                       [FCST CONSUMED QTY], [ORDER QTY], [PACKED QTY], [SHIPPED QTY],
                       [Net Demand], [ORDER TYPE], [DESTINATION], [DESTINATION WAREHOUSE],
                       [CUSTOMER REQ IN DC DATE], [CUSTOMER EX FACTORY DATE], [DELIVERY TERMS],
                       [PLANNED DELIVERY METHOD], [NOTES], [CUSTOMER PRICE], 
                       [USA ONLY LSTP 75% EX WORKS], [EX WORKS (USD)], [ADMINISTRATION FEE],
                       [DESIGN FEE], [FX CHARGE], [HANDLING], [SURCHARGE FEE], [DISCOUNT],
                       [FINAL FOB (USD)], [HS CODE], [US DUTY RATE], [US DUTY], [FREIGHT],
                       [US TARIFF RATE], [US TARIFF], [DDP US (USD)], [SMS PRICE USD],
                       [FINAL PRICES Y/N], [NOTES FOR PRICE], [stg_monday_item_id] as [Item ID],
                       [matchAlias], [PLANNING BOARD], [REQUESTED XFD STATUS], 
                       [EX-FTY (Change Request)], [EX-FTY (Forecast)], [EX-FTY (Partner PO)],
                       [EX-FTY (Revised LS)], [PRODUCTION TYPE], [AQL INSPECTION], [AQL TYPE],
                       [PLANNED CUT DATE], [MO NUMBER], [PRODUCTION STATUS], [FACTORY COUNTRY],
                       [FACTORY], [ALLOCATION STATUS], [PRODUCTION QTY], [TRIM ETA DATE],
                       [FABRIC ETA DATE], [TRIM STATUS], [ADD TO PLANNING], [FABRIC STATUS],
                       [PPS STATUS], [PPS CMT DUE], [PPS CMT RCV], [REVENUE (FOB)], [ORDER STATUS]
                FROM [dbo].[STG_MON_CustMasterSchedule]
                WHERE [stg_batch_id] = ? AND [stg_status] = 'API_SUCCESS'
            """, (batch_id,))
            
            orders_promoted = cursor.rowcount
            
            # Promote subitems
            cursor.execute("""
                INSERT INTO [dbo].[MON_CustMasterSchedule_Subitems]
                SELECT [parent_item_id], [stg_monday_subitem_id] as [subitem_id], 
                       [stg_monday_subitem_board_id] as [subitem_board_id], [Size], 
                       [Order Qty], [Cut Qty], [Sew Qty], [Finishing Qty], 
                       [Received not Shipped Qty], [Packed Qty], [Shipped Qty], 
                       [ORDER LINE STATUS], [Item ID]
                FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
                WHERE [stg_batch_id] = ? AND [stg_status] = 'API_SUCCESS'
            """, (batch_id,))
            
            subitems_promoted = cursor.rowcount
            
            # Mark staging records as promoted
            cursor.execute("""
                UPDATE [dbo].[STG_MON_CustMasterSchedule]
                SET [stg_status] = 'PROMOTED'
                WHERE [stg_batch_id] = ? AND [stg_status] = 'API_SUCCESS'
            """, (batch_id,))
            
            cursor.execute("""
                UPDATE [dbo].[STG_MON_CustMasterSchedule_Subitems]
                SET [stg_status] = 'PROMOTED'
                WHERE [stg_batch_id] = ? AND [stg_status] = 'API_SUCCESS'
            """, (batch_id,))
            
            conn.commit()
        
        logger.info(f"Promoted {orders_promoted} orders and {subitems_promoted} subitems to production")
        return orders_promoted, subitems_promoted
    
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
