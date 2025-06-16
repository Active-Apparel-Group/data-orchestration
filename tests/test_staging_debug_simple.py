"""
Debug staging table without relying on missing imports
"""
import sys
import os
import pyodbc
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def get_db_connection():
    """
    Simple database connection function for debugging
    """
    # You'll need to adjust these connection details
    DB_ORDERS_HOST='ross-db-srv-test.database.windows.net'
    DB_ORDERS_PORT='1433'
    DB_ORDERS_DATABASE='ORDERS'
    DB_ORDERS_USERNAME='admin_ross'

    server = os.getenv('DB_ORDERS_HOST', 'your_server_name')
    database = os.getenv('DB_ORDERS_DATABASE', 'your_database_name')
    username = os.getenv('DB_ORDERS_USERNAME', 'your_username')
    password = os.getenv('DB_ORDERS_PASSWORD', 'your_password')

    connection_string = f"""
    DRIVER={{ODBC Driver 17 for SQL Server}};
    SERVER={server};
    DATABASE={database};
    UID={username};
    PWD={password};
    """
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Please check your database connection settings")
        raise

def debug_staging_table():
    """Debug the staging table"""
    print('=== Debugging MON_CustMasterSchedule Staging Table ===')
    
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"Cannot connect to database: {e}")
        return
    
    try:
        # 1. Check if table exists and its structure
        print('\n1. Checking table structure...')
        structure_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'MON_CustMasterSchedule'
        ORDER BY ORDINAL_POSITION
        """
        
        structure_df = pd.read_sql(structure_query, conn)
        print(f'Table columns ({len(structure_df)} total):')
        for _, col in structure_df.iterrows():
            nullable = "Yes" if col["IS_NULLABLE"] == "YES" else "No"
            max_len = col["CHARACTER_MAXIMUM_LENGTH"] if pd.notna(col["CHARACTER_MAXIMUM_LENGTH"]) else "N/A"
            print(f'  - {col["COLUMN_NAME"]} ({col["DATA_TYPE"]}, Max: {max_len}) - Nullable: {nullable}')
        
        # 2. Check current row count
        print('\n2. Checking current row count...')
        count_query = "SELECT COUNT(*) as total_rows FROM [dbo].[MON_CustMasterSchedule]"
        count_df = pd.read_sql(count_query, conn)
        total_rows = count_df.iloc[0]["total_rows"]
        print(f'Total rows in staging table: {total_rows}')
        
        # 3. Check recent entries (if any)
        print('\n3. Checking recent entries...')
        if total_rows > 0:
            recent_query = """
            SELECT TOP 10 [AAG ORDER NUMBER], [STYLE], [COLOR], [Item ID]
            FROM [dbo].[MON_CustMasterSchedule]
            ORDER BY [AAG ORDER NUMBER] DESC
            """
            recent_df = pd.read_sql(recent_query, conn)
            print('Recent entries:')
            print(recent_df)
        else:
            print('No entries found in staging table')
        
        # 4. Check for any entries with NULL Item ID
        print('\n4. Checking for entries needing sync...')
        pending_query = """
        SELECT COUNT(*) as pending_count
        FROM [dbo].[MON_CustMasterSchedule]
        WHERE [Item ID] IS NULL OR [Item ID] = '' OR [Item ID] = '0'
        """
        pending_df = pd.read_sql(pending_query, conn)
        pending_count = pending_df.iloc[0]["pending_count"]
        print(f'Orders pending Monday.com sync: {pending_count}')
        
        # 5. Test a simple insert to verify permissions
        print('\n5. Testing insert permissions...')
        cursor = conn.cursor()
        try:
            test_insert = """
            INSERT INTO [dbo].[MON_CustMasterSchedule] 
            ([AAG ORDER NUMBER], [STYLE], [COLOR])
            VALUES ('DEBUG-TEST', 'TEST-STYLE', 'TEST-COLOR')
            """
            cursor.execute(test_insert)
            conn.commit()
            print('✅ Test insert successful - permissions OK')
            
            # Clean up
            cursor.execute("DELETE FROM [dbo].[MON_CustMasterSchedule] WHERE [AAG ORDER NUMBER] = 'DEBUG-TEST'")
            conn.commit()
            print('✅ Test record cleaned up')
            
        except Exception as e:
            print(f'❌ Test insert failed: {e}')
            print('This might indicate permission issues or column mismatch')
        
        return structure_df
        
    except Exception as e:
        print(f'❌ Error debugging staging table: {e}')
        return None
    finally:
        conn.close()

def check_orders_unified():
    """Check what orders are available in ORDERS_UNIFIED"""
    print('\n=== Checking ORDERS_UNIFIED for Available Orders ===')
    
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"Cannot connect to database: {e}")
        return
    
    try:
        query = """
        SELECT TOP 5 
            [AAG ORDER NUMBER], 
            [CUSTOMER NAME], 
            [CUSTOMER STYLE], 
            [CUSTOMER COLOUR DESCRIPTION],
            [ORDER TYPE]
        FROM [dbo].[ORDERS_UNIFIED] 
        WHERE LEFT([CUSTOMER NAME], 3) <> 'LOR'
            AND LEFT([CUSTOMER NAME], 3) <> 'MAC'
            AND [AAG ORDER NUMBER] IS NOT NULL
            AND [CUSTOMER STYLE] IS NOT NULL
            AND [CUSTOMER COLOUR DESCRIPTION] IS NOT NULL
        ORDER BY [ORDER DATE PO RECEIVED] DESC
        """
        
        df = pd.read_sql(query, conn)
        print(f'Found {len(df)} sample orders in ORDERS_UNIFIED:')
        print(df)
        
    except Exception as e:
        print(f'❌ Error checking ORDERS_UNIFIED: {e}')
    finally:
        conn.close()

if __name__ == "__main__":
    print("Make sure to set your database connection environment variables:")
    print("DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD")
    print("Or modify the get_db_connection() function with your connection details")
    print()
    
    # Debug the staging table
    debug_staging_table()
    
    # Check source orders
    check_orders_unified()
    
    print('\n=== Summary ===')
    print('This will help us understand:')
    print('1. If the staging table structure is correct')
    print('2. If we have insert permissions')
    print('3. If there are already orders in the staging table')
    print('4. What orders are available to process')