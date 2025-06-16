"""
Database operations for staging workflow
Handles all staging table CRUD operations
"""

import pandas as pd
import pyodbc
import json
import uuid
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
    
    def insert_orders_to_staging(self, orders_df: pd.DataFrame, 
                                customer_batch: str, batch_id: str) -> int:
        """Insert transformed orders to staging table"""
        
        if orders_df.empty:
            return 0
        
        # Add staging-specific columns
        orders_df = orders_df.copy()
        orders_df['stg_batch_id'] = batch_id
        orders_df['stg_customer_batch'] = customer_batch
        orders_df['stg_status'] = 'PENDING'
        orders_df['stg_created_date'] = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get column names for dynamic insert
            columns = list(orders_df.columns)
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join([f'[{col}]' for col in columns])
            
            insert_query = f"""
                INSERT INTO [dbo].[STG_MON_CustMasterSchedule] ({column_names})
                VALUES ({placeholders})
            """
            
            rows_inserted = 0
            for _, row in orders_df.iterrows():
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
                
                cursor.execute(insert_query, values)
                rows_inserted += 1
            
            conn.commit()
        
        logger.info(f"Inserted {rows_inserted} orders to staging for batch {batch_id}")
        return rows_inserted
    
    def get_pending_staging_orders(self, batch_id: str) -> pd.DataFrame:
        """Get orders ready for Monday.com API"""
        
        query = """
            SELECT [stg_id], [stg_batch_id], [stg_customer_batch], [stg_status],
                   [AAG ORDER NUMBER], [CUSTOMER], [STYLE], [COLOR], [Title],
                   [Group], [Item ID], [PO NUMBER]
            FROM [dbo].[STG_MON_CustMasterSchedule]
            WHERE [stg_batch_id] = ? AND [stg_status] = 'PENDING'
            ORDER BY [stg_id]
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=[batch_id])
        
        logger.info(f"Retrieved {len(df)} pending orders for batch {batch_id}")
        return df
    
    def update_staging_with_monday_id(self, stg_id: int, monday_item_id: int, 
                                     api_payload: Optional[str] = None) -> bool:
        """Update staging record with Monday.com item ID"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE [dbo].[STG_MON_CustMasterSchedule]
                SET [stg_status] = 'API_SUCCESS',
                    [stg_monday_item_id] = ?,
                    [stg_processed_date] = GETDATE(),
                    [stg_api_payload] = ?
                WHERE [stg_id] = ?
            """, (monday_item_id, api_payload, stg_id))
            
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
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE [dbo].[STG_MON_CustMasterSchedule]
                SET [stg_status] = 'API_FAILED',
                    [stg_error_message] = ?,
                    [stg_processed_date] = GETDATE(),
                    [stg_api_payload] = ?,
                    [stg_retry_count] = [stg_retry_count] + 1
                WHERE [stg_id] = ?
            """, (error_message, api_payload, stg_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
        
        if rows_affected > 0:
            logger.warning(f"Marked staging record {stg_id} as failed: {error_message}")
        
        return rows_affected > 0
    
    def get_successful_orders_for_subitems(self, batch_id: str) -> pd.DataFrame:
        """Get successfully created orders for subitem processing"""
        
        query = """
            SELECT [stg_id], [stg_batch_id], [stg_customer_batch], 
                   [stg_monday_item_id], [AAG ORDER NUMBER], [STYLE], [COLOR],
                   [PO NUMBER], [CUSTOMER ALT PO]
            FROM [dbo].[STG_MON_CustMasterSchedule]
            WHERE [stg_batch_id] = ? AND [stg_status] = 'API_SUCCESS'
            ORDER BY [stg_id]
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=[batch_id])
        
        logger.info(f"Retrieved {len(df)} successful orders for subitem processing")
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
            
            rows_inserted = 0
            for _, row in subitems_df.iterrows():
                values = []
                for col in columns:
                    value = row[col]
                    # Handle pandas NA/NaN values for SQL Server
                    if pd.isna(value):
                        values.append(None)
                    else:
                        values.append(value)
                
                cursor.execute(insert_query, values)
                rows_inserted += 1
            
            conn.commit()
        
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
