"""
Database Query Functions for Customer Master Schedule Orders

This module handles all database operations for the order management workflow:
- Querying new orders from ORDERS_UNIFIED
- Managing MON_CustMasterSchedule staging table
- Updating Monday.com item IDs and sync status

Dependencies:
- pandas, pyodbc, os
"""

import pandas as pd
import pyodbc
import os
import warnings
from datetime import datetime
from typing import Optional, Dict, List

# Suppress pandas warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

def load_env():
    """Load .env file from repo root."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return False

def get_db_config(db_key='ORDERS'):
    """Get DB config from environment variables."""
    load_env()
    
    # Get password from either SECRET_xxx_PWD (base64) or DB_xxx_PASSWORD (plain)
    import base64
    password = os.getenv(f'SECRET_{db_key.upper()}_PWD')
    if password:
        try:
            password = base64.b64decode(password).decode()
        except:
            pass
    else:
        password = os.getenv(f'DB_{db_key.upper()}_PASSWORD')
    
    return {
        'host': os.getenv(f'DB_{db_key.upper()}_HOST'),
        'port': int(os.getenv(f'DB_{db_key.upper()}_PORT', 1433)),
        'database': os.getenv(f'DB_{db_key.upper()}_DATABASE'),
        'username': os.getenv(f'DB_{db_key.upper()}_USERNAME'),
        'password': password
    }

def get_database_connection():
    """Create database connection using environment variables"""
    try:
        orders_cfg = get_db_config('ORDERS')
        
        # Use ODBC Driver 17 for SQL Server if available, fallback to SQL Server
        driver = "{ODBC Driver 17 for SQL Server}"
        try:
            test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
            pyodbc.connect(test_conn_str, timeout=1)
        except:
            driver = "{SQL Server}"
        
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={orders_cfg['host']},{orders_cfg['port']};"
            f"DATABASE={orders_cfg['database']};"
            f"UID={orders_cfg['username']};PWD={orders_cfg['password']};"
            "Encrypt=no;TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_new_orders_from_unified(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Query ORDERS_UNIFIED for new orders not yet in MON_CustMasterSchedule
    
    Args:
        limit: Optional limit on number of records to return
          Returns:
        DataFrame with new order records
    """
    limit = 2
    limit_clause = f"TOP {limit}" if limit else ""
    
    query = f"""
    SELECT {limit_clause} ou.*
    FROM [dbo].[ORDERS_UNIFIED] ou
    LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
        ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
        AND ou.[CUSTOMER STYLE] = cms.[STYLE] 
        AND ou.[CUSTOMER COLOUR DESCRIPTION] = cms.[COLOR]
    WHERE cms.[AAG ORDER NUMBER] IS NULL
        AND LEFT(ou.[CUSTOMER NAME], 3) <> 'LOR'
        AND ou.[AAG ORDER NUMBER] IS NOT NULL
        AND ou.[CUSTOMER STYLE] IS NOT NULL
        AND ou.[CUSTOMER COLOUR DESCRIPTION] IS NOT NULL
    ORDER BY ou.[ORDER DATE PO RECEIVED] DESC
    """
    
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        print(f"Querying new orders from ORDERS_UNIFIED...")
        df = pd.read_sql(query, conn)
        print(f"Found {len(df)} new orders to process")
        return df
    except Exception as e:
        print(f"Error querying new orders: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def insert_orders_to_staging(orders_df: pd.DataFrame) -> bool:
    """
    Insert transformed orders into MON_CustMasterSchedule staging table
    
    Args:
        orders_df: DataFrame with transformed order data
        
    Returns:
        True if successful, False otherwise
    """
    if orders_df.empty:
        print("No orders to insert into staging table")
        return True
    
    conn = get_database_connection()
    if conn is None:
        return False
    
    try:
        print(f"Inserting {len(orders_df)} orders into MON_CustMasterSchedule...")
        
        # Insert using pandas to_sql method
        orders_df.to_sql(
            name='MON_CustMasterSchedule',
            con=conn,
            if_exists='append',
            index=False,
            method='multi'
        )
        
        print(f"Successfully inserted {len(orders_df)} orders into staging table")
        return True
        
    except Exception as e:
        print(f"Error inserting orders to staging: {e}")
        return False
    finally:
        conn.close()

def get_pending_monday_sync(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Get orders from MON_CustMasterSchedule that need to be synced to Monday.com
    
    Args:
        limit: Optional limit on number of records to return
        
    Returns:
        DataFrame with orders pending Monday.com sync
    """
    limit_clause = f"TOP {limit}" if limit else ""
    
    query = f"""
    SELECT {limit_clause} *
    FROM [dbo].[MON_CustMasterSchedule]
    WHERE [MONDAY_ITEM_ID] IS NULL 
        OR [MONDAY_ITEM_ID] = ''
        OR [SYNC_STATUS] = 'PENDING'
    ORDER BY [CREATED_DATE] ASC
    """
    
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        print(f"Querying orders pending Monday.com sync...")
        df = pd.read_sql(query, conn)
        print(f"Found {len(df)} orders pending sync")
        return df
    except Exception as e:
        print(f"Error querying pending sync orders: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def update_monday_item_id(order_key: Dict[str, str], item_id: str, group_id: str = None) -> bool:
    """
    Update Monday.com item ID in MON_CustMasterSchedule after successful creation
    
    Args:
        order_key: Dictionary with AAG ORDER NUMBER, CUSTOMER STYLE, COLOR
        item_id: Monday.com item ID
        group_id: Optional Monday.com group ID
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_database_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        update_query = """
        UPDATE [dbo].[MON_CustMasterSchedule]
        SET [MONDAY_ITEM_ID] = ?,
            [MONDAY_GROUP_ID] = ?,
            [SYNC_STATUS] = 'SYNCED',
            [UPDATED_DATE] = GETDATE()
        WHERE [AAG ORDER NUMBER] = ? 
            AND [CUSTOMER STYLE] = ?
            AND [COLOR] = ?
        """
        
        cursor.execute(update_query, (
            item_id,
            group_id,
            order_key['AAG ORDER NUMBER'],
            order_key['CUSTOMER STYLE'], 
            order_key['COLOR']
        ))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"Updated Monday.com item ID {item_id} for order {order_key['AAG ORDER NUMBER']}")
            return True
        else:
            print(f"No rows updated for order {order_key['AAG ORDER NUMBER']}")
            return False
            
    except Exception as e:
        print(f"Error updating Monday.com item ID: {e}")
        return False
    finally:
        conn.close()

def mark_sync_status(order_key: Dict[str, str], status: str, error_message: str = None) -> bool:
    """
    Mark sync status for an order (PENDING, SYNCED, ERROR)
    
    Args:
        order_key: Dictionary with AAG ORDER NUMBER, CUSTOMER STYLE, COLOR
        status: Sync status (PENDING, SYNCED, ERROR)
        error_message: Optional error message for ERROR status
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_database_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        update_query = """
        UPDATE [dbo].[MON_CustMasterSchedule]
        SET [SYNC_STATUS] = ?,
            [ERROR_MESSAGE] = ?,
            [UPDATED_DATE] = GETDATE()
        WHERE [AAG ORDER NUMBER] = ? 
            AND [CUSTOMER STYLE] = ?
            AND [COLOR] = ?
        """
        
        cursor.execute(update_query, (
            status,
            error_message,
            order_key['AAG ORDER NUMBER'],
            order_key['CUSTOMER STYLE'],
            order_key['COLOR']
        ))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"Updated sync status to {status} for order {order_key['AAG ORDER NUMBER']}")
            return True
        else:
            print(f"No rows updated for order {order_key['AAG ORDER NUMBER']}")
            return False
            
    except Exception as e:
        print(f"Error updating sync status: {e}")
        return False
    finally:
        conn.close()

def get_sync_statistics() -> Dict[str, int]:
    """
    Get sync statistics from MON_CustMasterSchedule
    
    Returns:
        Dictionary with sync status counts
    """
    query = """
    SELECT 
        [SYNC_STATUS],
        COUNT(*) as count
    FROM [dbo].[MON_CustMasterSchedule]
    GROUP BY [SYNC_STATUS]
    
    UNION ALL
    
    SELECT 
        'TOTAL' as SYNC_STATUS,
        COUNT(*) as count
    FROM [dbo].[MON_CustMasterSchedule]
    """
    
    conn = get_database_connection()
    if conn is None:
        return {}
    
    try:
        df = pd.read_sql(query, conn)
        return dict(zip(df['SYNC_STATUS'], df['count']))
    except Exception as e:
        print(f"Error getting sync statistics: {e}")
        return {}
    finally:
        conn.close()

def cleanup_old_pending_records(days_old: int = 7) -> int:
    """
    Clean up old pending records that might be stuck
    
    Args:
        days_old: Number of days old to consider for cleanup
        
    Returns:
        Number of records cleaned up
    """
    conn = get_database_connection()
    if conn is None:
        return 0
    
    try:
        cursor = conn.cursor()
        
        cleanup_query = """
        UPDATE [dbo].[MON_CustMasterSchedule]
        SET [SYNC_STATUS] = 'ERROR',            [ERROR_MESSAGE] = 'Cleanup: Record stuck in PENDING status',
            [UPDATED_DATE] = GETDATE()
        WHERE [SYNC_STATUS] = 'PENDING'
            AND [CREATED_DATE] < DATEADD(day, -?, GETDATE())
            AND ([MONDAY_ITEM_ID] IS NULL OR [MONDAY_ITEM_ID] = '')
        """
        
        cursor.execute(cleanup_query, (days_old,))
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"Cleaned up {rows_affected} old pending records")
        
        return rows_affected
        
    except Exception as e:
        print(f"Error cleaning up old records: {e}")
        return 0
    finally:
        conn.close()

# Compatibility functions for refactored add_order.py
def get_new_orders_for_monday(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Alias for get_new_orders_from_unified for compatibility with refactored add_order.py
    """
    return get_new_orders_from_unified(limit)

def insert_orders_to_staging(orders_list: List[Dict]) -> bool:
    """
    Insert list of transformed order dictionaries into staging table
    
    Args:
        orders_list: List of transformed order dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    if not orders_list:
        print("No orders to insert into staging table")
        return True
    
    # Convert list of dicts to DataFrame
    orders_df = pd.DataFrame(orders_list)
    
    conn = get_database_connection()
    if conn is None:
        return False
    
    try:
        print(f"Inserting {len(orders_df)} orders into MON_CustMasterSchedule...")
        
        # Insert using pandas to_sql method
        orders_df.to_sql(
            name='MON_CustMasterSchedule',
            con=conn,
            if_exists='append',
            index=False,
            method='multi'
        )
        
        print(f"Successfully inserted {len(orders_df)} orders into staging table")
        return True
        
    except Exception as e:
        print(f"Error inserting orders to staging: {e}")
        return False
    finally:
        conn.close()

def get_orders_pending_monday_sync(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Alias for get_pending_monday_sync for compatibility with refactored add_order.py
    """
    return get_pending_monday_sync(limit)

def update_monday_item_id(order_number: str, customer_style: str, color: str, item_id: str, group_id: str = None) -> bool:
    """
    Update Monday.com item ID - simplified interface for add_order.py
    
    Args:
        order_number: AAG ORDER NUMBER
        customer_style: CUSTOMER STYLE
        color: COLOR
        item_id: Monday.com item ID
        group_id: Optional Monday.com group ID
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_database_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        update_query = """
        UPDATE [dbo].[MON_CustMasterSchedule]
        SET [MONDAY_ITEM_ID] = ?,
            [MONDAY_GROUP_ID] = ?,
            [SYNC_STATUS] = 'SYNCED',
            [UPDATED_DATE] = GETDATE()
        WHERE [AAG ORDER NUMBER] = ? 
            AND [CUSTOMER STYLE] = ?
            AND [COLOR] = ?
        """
        
        cursor.execute(update_query, (
            item_id,
            group_id,
            order_number,
            customer_style, 
            color
        ))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"Updated Monday.com item ID {item_id} for order {order_number}")
            return True
        else:
            print(f"No rows updated for order {order_number}")
            return False
            
    except Exception as e:
        print(f"Error updating Monday.com item ID: {e}")
        return False
    finally:
        conn.close()

# Test functions
if __name__ == "__main__":
    print("Testing Database Query Functions")
    print("=" * 50)
    
    # Test database connection
    conn = get_database_connection()
    if conn:
        print("✅ Database connection successful")
        conn.close()
    else:
        print("❌ Database connection failed")
        exit(1)
    
    # Test querying new orders (limit to 5 for testing)
    print("\n📋 Testing new orders query...")
    new_orders = get_new_orders_from_unified(limit=5)
    print(f"Sample new orders: {len(new_orders)} records")
    
    if not new_orders.empty:
        print("\nSample columns:")
        for col in new_orders.columns[:10]:  # Show first 10 columns
            print(f"  - {col}")
    
    # Test sync statistics
    print("\n📊 Current sync statistics:")
    stats = get_sync_statistics()
    for status, count in stats.items():
        print(f"  {status}: {count}")
    
    print("\n✅ Database query tests completed")