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
    limit = 10
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
        and left(ou.[CUSTOMER NAME], 3) = 'MAC'
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

def get_next_staging_id() -> int:
    """
    Get the next available staging ID starting from 1000
    
    Returns:
        Next available staging ID
    """
    conn = get_database_connection()
    if conn is None:
        return 1000  # Default starting ID
    
    try:
        cursor = conn.cursor()
          # Get the highest staging ID that starts with 1000+ range - using BIGINT to handle large numbers
        cursor.execute("""
            SELECT ISNULL(MAX(TRY_CAST([Item ID] AS BIGINT)), 999) 
            FROM [dbo].[MON_CustMasterSchedule] 
            WHERE [Item ID] IS NOT NULL 
            AND ISNUMERIC([Item ID]) = 1 
            AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
            AND TRY_CAST([Item ID] AS BIGINT) < 10000
        """)
        
        max_id = cursor.fetchone()[0]
        return max_id + 1
        
    except Exception as e:
        print(f"Error getting next staging ID: {e}")
        return 1000  # Default starting ID
    finally:
        conn.close()

def insert_orders_to_staging(orders_df: pd.DataFrame) -> bool:
    """
    Insert transformed orders into MON_CustMasterSchedule staging table
    Uses our own ID sequence starting at 1000 to avoid conflicts with Monday.com IDs
    
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
        
        # Add staging IDs to the DataFrame
        orders_df_copy = orders_df.copy()
        next_id = get_next_staging_id()
        
        # Assign sequential staging IDs starting from next_id
        staging_ids = list(range(next_id, next_id + len(orders_df_copy)))
        orders_df_copy['Item ID'] = staging_ids
        
        print(f"Assigned staging IDs: {min(staging_ids)} to {max(staging_ids)}")
        
        # Use manual insert instead of pandas to_sql for better SQL Server compatibility
        cursor = conn.cursor()
        
        # Get column names from DataFrame
        columns = list(orders_df_copy.columns)
        
        # Create placeholder string for VALUES clause
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join([f'[{col}]' for col in columns])
        
        insert_query = f"""
            INSERT INTO [dbo].[MON_CustMasterSchedule] ({column_names})
            VALUES ({placeholders})
        """
        
        # Insert each row
        rows_inserted = 0
        for _, row in orders_df_copy.iterrows():
            values = [row[col] for col in columns]
            cursor.execute(insert_query, values)
            rows_inserted += 1
        
        conn.commit()
        print(f"Successfully inserted {rows_inserted} orders into staging table")
        return True
        
    except Exception as e:
        print(f"Error inserting orders to staging: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def get_pending_monday_sync(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Get orders from MON_CustMasterSchedule that need to be synced to Monday.com
    Uses staging IDs (1000+) to identify records that haven't been updated with Monday.com IDs
    
    Args:
        limit: Optional limit on number of records to return
        
    Returns:
        DataFrame with orders pending Monday.com sync    """
    limit_clause = f"TOP {limit}" if limit else ""
    
    query = f"""
    SELECT {limit_clause} *
    FROM [dbo].[MON_CustMasterSchedule]
    WHERE [Item ID] IS NOT NULL 
        AND ISNUMERIC([Item ID]) = 1 
        AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
        AND TRY_CAST([Item ID] AS BIGINT) < 10000
    ORDER BY TRY_CAST([Item ID] AS BIGINT) ASC
    """
    
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        print(f"Querying orders pending Monday.com sync (staging IDs 1000+)...")
        df = pd.read_sql(query, conn)
        print(f"Found {len(df)} orders pending sync")
        return df
    except Exception as e:
        print(f"Error querying pending sync orders: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def update_monday_item_id(staging_id: str, monday_item_id: str, group_id: str = None) -> bool:
    """
    Update Monday.com item ID using staging ID for precise identification
    
    Args:
        staging_id: Our staging table ID (1000+)
        monday_item_id: Monday.com item ID from API
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
        SET [Item ID] = ?,
            [UpdateDate] = GETDATE()
        WHERE [Item ID] = ?
        """
        
        cursor.execute(update_query, (monday_item_id, staging_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"Updated staging ID {staging_id} with Monday.com item ID {monday_item_id}")
            return True
        else:
            print(f"No rows updated for staging ID {staging_id}")
            return False
            
    except Exception as e:
        print(f"Error updating Monday.com item ID: {e}")
        return False
    finally:
        conn.close()

def mark_sync_status(order_key: Dict[str, str], status: str, error_message: str = None) -> bool:
    """
    DEPRECATED: Mark sync status for an order (PENDING, SYNCED, ERROR)
    
    NOTE: This function references a non-existent SYNC_STATUS column and has been disabled.
    The MON_CustMasterSchedule table doesn't have a SYNC_STATUS column.
    
    Args:
        order_key: Dictionary with AAG ORDER NUMBER, CUSTOMER STYLE, COLOR
        status: Sync status (PENDING, SYNCED, ERROR)
        error_message: Optional error message for ERROR status
        
    Returns:
        True if successful, False otherwise
    """
    print(f"⚠️ DEPRECATED: mark_sync_status called for order {order_key.get('AAG ORDER NUMBER', 'Unknown')}")
    print("   This function is disabled because SYNC_STATUS column doesn't exist in the table")
    return True  # Return True to avoid breaking existing code

def get_sync_statistics() -> Dict[str, int]:
    """
    DEPRECATED: Get sync statistics from MON_CustMasterSchedule
    
    NOTE: This function references a non-existent SYNC_STATUS column and has been disabled.
    The MON_CustMasterSchedule table doesn't have a SYNC_STATUS column.
    
    Returns:
        Dictionary with sync status counts (empty since function is disabled)
    """
    print("⚠️ DEPRECATED: get_sync_statistics called")
    print("   This function is disabled because SYNC_STATUS column doesn't exist in the table")
    return {"DISABLED": 0}  # Return placeholder to avoid breaking existing code

def cleanup_old_pending_records(days_old: int = 7) -> int:
    """
    DEPRECATED: Clean up old pending records that might be stuck
    
    NOTE: This function references a non-existent SYNC_STATUS column and has been disabled.
    The MON_CustMasterSchedule table doesn't have a SYNC_STATUS column.
    
    Args:
        days_old: Number of days old to consider for cleanup
        
    Returns:
        Number of records cleaned up (always 0 since function is disabled)
    """
    print("⚠️ DEPRECATED: cleanup_old_pending_records called")
    print("   This function is disabled because SYNC_STATUS column doesn't exist in the table")
    return 0  # Return 0 to indicate no records cleaned

# Compatibility functions for refactored add_order.py
def get_new_orders_for_monday(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Alias for get_new_orders_from_unified for compatibility with refactored add_order.py
    """
    return get_new_orders_from_unified(limit)

def insert_orders_to_staging_list(orders_list: List[Dict]) -> bool:
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
    
    # Convert list of dicts to DataFrame and call the main function
    orders_df = pd.DataFrame(orders_list)
    return insert_orders_to_staging(orders_df)

def get_orders_pending_monday_sync(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Alias for get_pending_monday_sync for compatibility with refactored add_order.py
    """
    return get_pending_monday_sync(limit)

# REMOVED: Duplicate update_monday_item_id function with parameter mismatch bug
# The correct function is above (line 262) that uses staging_id

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
