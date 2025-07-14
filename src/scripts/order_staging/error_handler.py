"""
Error handling and logging for staging workflow
"""

import json
import pandas as pd
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# NEW STANDARD: Find repository root, then find utils (Option 2)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path using repository root method
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import centralized modules
import db_helper as db
import logger_helper

# Initialize logger with script-specific name
logger = logger_helper.get_logger("error_handler")

from .staging_config import get_config

class ErrorHandler:
    """Handles error logging and retry logic for staging workflow"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.config = get_config()
    
    def get_connection(self):
        """Get database connection"""
        import pyodbc
        return pyodbc.connect(self.connection_string)
    
    def log_api_error(self, record_type: str, record_data: Dict[str, Any], 
                     error_details: Dict[str, Any]) -> bool:
        """Log failed API call to appropriate error table"""
        
        try:
            if record_type == 'ITEM':
                return self._log_item_error(record_data, error_details)
            elif record_type == 'SUBITEM':
                return self._log_subitem_error(record_data, error_details)
            else:
                logger.error(f"Unknown record type for error logging: {record_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")
            return False
    
    def _log_item_error(self, record_data: Dict[str, Any], error_details: Dict[str, Any]) -> bool:
        """Log main item error to ERR_MON_CustMasterSchedule"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO [dbo].[ERR_MON_CustMasterSchedule]
                ([original_stg_id], [batch_id], [customer_batch], [order_number], 
                 [item_name], [group_name], [api_payload], [error_type], 
                 [error_message], [http_status_code], [retry_count], [original_data])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data.get('stg_id'),
                record_data.get('batch_id'),
                record_data.get('customer_batch'),
                record_data.get('order_number'),
                record_data.get('item_name'),
                record_data.get('group_name'),
                error_details.get('api_payload'),
                error_details.get('error_type'),
                error_details.get('error_message'),
                error_details.get('http_status_code'),
                record_data.get('retry_count', 0),
                json.dumps(record_data, default=str)
            ))
            conn.commit()
        
        logger.error(f"Logged item error for order {record_data.get('order_number')}: {error_details.get('error_message')}")
        return True
    
    def _log_subitem_error(self, record_data: Dict[str, Any], error_details: Dict[str, Any]) -> bool:
        """Log subitem error to ERR_MON_CustMasterSchedule_Subitems"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO [dbo].[ERR_MON_CustMasterSchedule_Subitems]
                ([original_stg_subitem_id], [parent_item_id], [batch_id], [customer_batch], 
                 [order_number], [size_label], [order_qty], [subitem_name], [api_payload], 
                 [error_type], [error_message], [http_status_code], [retry_count], [original_data])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data.get('stg_subitem_id'),
                record_data.get('parent_item_id'),
                record_data.get('batch_id'),
                record_data.get('customer_batch'),
                record_data.get('order_number'),
                record_data.get('size_label'),
                record_data.get('order_qty'),
                record_data.get('subitem_name'),
                error_details.get('api_payload'),
                error_details.get('error_type'),
                error_details.get('error_message'),
                error_details.get('http_status_code'),
                record_data.get('retry_count', 0),
                json.dumps(record_data, default=str)
            ))
            conn.commit()
        
        logger.error(f"Logged subitem error for {record_data.get('subitem_name')}: {error_details.get('error_message')}")
        return True
    
    def get_retry_eligible_errors(self, record_type: str, max_retries: int = 3) -> pd.DataFrame:
        """Get errors eligible for retry"""
        
        if record_type == 'ITEM':
            table_name = 'ERR_MON_CustMasterSchedule'
        elif record_type == 'SUBITEM':
            table_name = 'ERR_MON_CustMasterSchedule_Subitems'
        else:
            return pd.DataFrame()
        
        query = f"""
            SELECT *
            FROM [dbo].[{table_name}]
            WHERE [max_retries_reached] = 0
              AND [retry_count] < ?
              AND [error_type] IN ({', '.join(['?' for _ in self.config['error']['retryable_errors']])})
              AND [resolved_date] IS NULL
            ORDER BY [created_date]
        """
        
        params = [max_retries] + self.config['error']['retryable_errors']
        
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        logger.info(f"Found {len(df)} {record_type.lower()} errors eligible for retry")
        return df
    
    def mark_error_as_retried(self, record_type: str, err_id: int) -> bool:
        """Mark error record as retried"""
        
        table_name = 'ERR_MON_CustMasterSchedule' if record_type == 'ITEM' else 'ERR_MON_CustMasterSchedule_Subitems'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE [dbo].[{table_name}]
                SET [retry_count] = [retry_count] + 1,
                    [last_retry_date] = GETDATE()
                WHERE [err_id] = ?
            """, (err_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
        
        return rows_affected > 0
    
    def mark_error_as_max_retries_reached(self, record_type: str, err_id: int) -> bool:
        """Mark error as having reached max retries"""
        
        table_name = 'ERR_MON_CustMasterSchedule' if record_type == 'ITEM' else 'ERR_MON_CustMasterSchedule_Subitems'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE [dbo].[{table_name}]
                SET [max_retries_reached] = 1,
                    [last_retry_date] = GETDATE()
                WHERE [err_id] = ?
            """, (err_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
        
        return rows_affected > 0
    
    def mark_error_as_resolved(self, record_type: str, err_id: int, resolved_by: str) -> bool:
        """Mark error as resolved"""
        
        table_name = 'ERR_MON_CustMasterSchedule' if record_type == 'ITEM' else 'ERR_MON_CustMasterSchedule_Subitems'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE [dbo].[{table_name}]
                SET [resolved_date] = GETDATE(),
                    [resolved_by] = ?
                WHERE [err_id] = ?
            """, (resolved_by, err_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
        
        return rows_affected > 0
    
    def get_error_summary(self, batch_id: Optional[str] = None, 
                         customer_batch: Optional[str] = None) -> Dict[str, Any]:
        """Get error summary for reporting"""
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if batch_id:
            where_conditions.append("[batch_id] = ?")
            params.append(batch_id)
        
        if customer_batch:
            where_conditions.append("[customer_batch] = ?")
            params.append(customer_batch)
        
        if not where_conditions:
            where_conditions.append("1=1")  # Get all errors
        
        where_clause = " AND ".join(where_conditions)
        
        # Get item errors summary
        item_query = f"""
            SELECT 
                [error_type],
                COUNT(*) as error_count,
                COUNT(CASE WHEN [max_retries_reached] = 1 THEN 1 END) as max_retries_count,
                COUNT(CASE WHEN [resolved_date] IS NOT NULL THEN 1 END) as resolved_count
            FROM [dbo].[ERR_MON_CustMasterSchedule]
            WHERE {where_clause}
            GROUP BY [error_type]
            ORDER BY error_count DESC
        """
        
        # Get subitem errors summary
        subitem_query = f"""
            SELECT 
                [error_type],
                COUNT(*) as error_count,
                COUNT(CASE WHEN [max_retries_reached] = 1 THEN 1 END) as max_retries_count,
                COUNT(CASE WHEN [resolved_date] IS NOT NULL THEN 1 END) as resolved_count
            FROM [dbo].[ERR_MON_CustMasterSchedule_Subitems]
            WHERE {where_clause}
            GROUP BY [error_type]
            ORDER BY error_count DESC
        """
        
        with self.get_connection() as conn:
            item_errors = pd.read_sql(item_query, conn, params=params)
            subitem_errors = pd.read_sql(subitem_query, conn, params=params)
        
        summary = {
            'item_errors': item_errors.to_dict('records'),
            'subitem_errors': subitem_errors.to_dict('records'),
            'total_item_errors': item_errors['error_count'].sum() if not item_errors.empty else 0,
            'total_subitem_errors': subitem_errors['error_count'].sum() if not subitem_errors.empty else 0
        }
        
        return summary
    
    def cleanup_old_errors(self, days_to_keep: int = 30) -> int:
        """Clean up old resolved error records"""
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean up old resolved item errors
            cursor.execute("""
                DELETE FROM [dbo].[ERR_MON_CustMasterSchedule]
                WHERE [resolved_date] IS NOT NULL
                  AND [resolved_date] < DATEADD(DAY, -?, GETDATE())
            """, (days_to_keep,))
            
            item_deleted = cursor.rowcount
            
            # Clean up old resolved subitem errors
            cursor.execute("""
                DELETE FROM [dbo].[ERR_MON_CustMasterSchedule_Subitems]
                WHERE [resolved_date] IS NOT NULL
                  AND [resolved_date] < DATEADD(DAY, -?, GETDATE())
            """, (days_to_keep,))
            
            subitem_deleted = cursor.rowcount
            total_deleted = item_deleted + subitem_deleted
            
            conn.commit()
        
        logger.info(f"Cleaned up {total_deleted} old error records")
        return total_deleted
