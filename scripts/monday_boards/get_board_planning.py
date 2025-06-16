#!/usr/bin/env python3
"""
End-to-End Test: Monday.com API -> Database Insert -> Verification
================================================================

This script:
1. Fetches a record from Monday.com API
2. Maps columns to MON_COO_Planning table schema
3. Inserts the record into the database
4. Queries to confirm the insert worked
5. Provides cleanup functionality

For testing purposes only!
"""

import os, re, requests, pandas as pd, pyodbc
from datetime import datetime

# Configuration
BOARD_ID = 8709134353
API_VER = "2025-04"
MONDAY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"

HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

# Database connection parameters
DB_CONFIG = {
    'host': 'ross-db-srv-test.database.windows.net',
    'port': '1433',
    'database': 'ORDERS',
    'username': 'admin_ross',
    'password': 'Active@IT2023'
}

def get_db_connection():
    """Get a database connection using pyodbc"""
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={DB_CONFIG['host']},{DB_CONFIG['port']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)

def gql(query_string):
    """Execute GraphQL query against Monday.com API"""
    response = requests.post(
        "https://api.monday.com/v2",
        headers=HEADERS,
        json={"query": query_string},
        verify=False
    )
    response.raise_for_status()
    return response.json()["data"]

def fetch_monday_record():
    """Fetch a specific record from Monday.com board"""
    print("📡 Fetching record from Monday.com API...")
    
    # Get board metadata
    board_query = f"query {{ boards(ids:{BOARD_ID}) {{ id name }} }}"
    board_data = gql(board_query)["boards"][0]
    
    # Fetch specific item
    item_id = 9378053930
    item_query = f'''
    query GetBoardItems {{
      boards(ids: {BOARD_ID}) {{
        name
        items_page(query_params: {{ids: [{item_id}]}}) {{
          items {{
            id
            name
            updated_at
            group {{
              id
              title
            }}
            column_values {{
              column {{
                title
                id
                type
                description
              }}
              value
              text
              id
            }}
          }}
        }}
      }}
    }}
    '''
    
    data = gql(item_query)
    items = data["boards"][0]["items_page"]["items"]
    
    if not items:
        raise ValueError(f"No item found with ID {item_id}")
    
    item = items[0]
    
    # Flatten the record
    record = {
        "Title": item["name"],
        "UpdateDate": item["updated_at"],
        "Group": item["group"]["title"],
        "board_id": int(board_data["id"]),
        "board_name": board_data["name"],
    }
    
    for cv in item["column_values"]:
        record[cv["column"]["title"]] = cv.get("display_value") or cv.get("value") or cv.get("text")
    
    print(f"✅ Fetched record: {record['Title']}")
    return record, board_data["name"]

def prepare_record_for_insert(record):
    """Convert Monday.com record to DataFrame and prepare for database insert"""
    print("🔄 Preparing record for database insert...")
    
    # Create DataFrame
    df = pd.DataFrame([record])
    
    print(f"📋 Original DataFrame columns ({len(df.columns)}): {list(df.columns)}")
    
    # Drop unwanted columns that we know cause issues
    df = df.drop(columns=[c for c in ["AM (linked)"] if c in df.columns])
    
    # Process data types to match database schema
    date_cols = [c for c in df.columns if re.search(r"DATE\)", c)]
    bigint_cols = [
        "BULK PO QTY", "Fabric Lead Time", "Precut Quantity", "Item ID",
        "QTY WIP", "QTY FG", "QTY INVOICED", "QTY FCST",
        "QTY WIP CUT", "QTY WIP SEW", "QTY WIP FIN", "QTY SCRAP",
    ]
    
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    
    for c in bigint_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    
    # Add test marker to REMARK field for identification
    if 'REMARK' in df.columns:
        df['REMARK'] = df['REMARK'].astype(str) + " [TEST_INSERT]"
    else:
        df['REMARK'] = "[TEST_INSERT]"
    
    print(f"✅ Prepared DataFrame with {df.shape[0]} rows and {df.shape[1]} columns")
    return df

def main():
    """Main end-to-end test function"""
    print("🚀 === Monday.com to Database End-to-End Test ===")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Test database connection
        print("\n=== STEP 1: Testing Database Connection ===")
        conn = get_db_connection()
        print("✅ Database connection successful!")
        
        # Step 2: Check current record count
        print("\n=== STEP 2: Checking Current Record Count ===")
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning")
            original_count = cursor.fetchone()[0]
            print(f"📊 Current records in MON_COO_Planning: {original_count:,}")
        except Exception as e:
            print(f"⚠️  Could not query MON_COO_Planning (table may not exist): {e}")
            original_count = 0
        
        # Step 3: Fetch record from Monday.com
        print("\n=== STEP 3: Fetching Record from Monday.com ===")
        record, board_name = fetch_monday_record()
        
        # Step 4: Prepare record for insert
        print("\n=== STEP 4: Preparing Record for Insert ===")
        df = prepare_record_for_insert(record)
        
        # --- keep only columns that exist in the target table ------------
        print("🔄 Querying actual table columns...")
        cursor.execute("""
            SELECT name
            FROM sys.columns
            WHERE object_id = OBJECT_ID('dbo.MON_COO_Planning')
        """)
        valid_cols = {row[0] for row in cursor.fetchall()}
        print(f"📋 Valid SQL table columns: {sorted(valid_cols)}")
        
        # rename any columns so they match the table
        df = df.rename(columns={"Title": "StyleKey"})  # add more as needed
        print(f"📋 DataFrame columns after rename: {list(df.columns)}")
        
        df = df[[c for c in df.columns if c in valid_cols]]
        print(f"📋 Final DataFrame columns ({len(df.columns)}): {list(df.columns)}")
        # -----------------------------------------------------------------
        
        # Step 5: Insert record into database
        print("\n=== STEP 5: Inserting Record into Database ===")
        
        # Build the insert statement
        columns = list(df.columns)
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join([f'[{col}]' for col in columns])
        
        insert_sql = f"INSERT INTO dbo.MON_COO_Planning ({column_names}) VALUES ({placeholders})"
        
        # Get the values from the first row, handle NaN/None
        values = []
        for col in columns:
            val = df.iloc[0][col]
            if pd.isna(val) or val is None:
                values.append(None)
            else:
                values.append(val)
        
        print(f"🔄 Executing insert with {len(values)} values...")
        cursor.execute(insert_sql, values)
        conn.commit()
        print("✅ Record inserted successfully!")
        
        # Step 6: Verify the insert
        print("\n=== STEP 6: Verifying Insert ===")
        cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning")
        new_count = cursor.fetchone()[0]
        print(f"📊 Records after insert: {new_count:,}")
        print(f"📊 Records added: {new_count - original_count}")
        
        # Query for our specific test record
        cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning WHERE REMARK LIKE '%[TEST_INSERT]%'")
        test_records = cursor.fetchone()[0]
        print(f"📊 Test records found: {test_records}")
        
        # Show the inserted record details
        query_sql = '''
            SELECT TOP 1 Title, [Group], CUSTOMER, [BULK PO QTY], REMARK 
            FROM dbo.MON_COO_Planning 
            WHERE REMARK LIKE '%[TEST_INSERT]%'
            ORDER BY UpdateDate DESC
        '''
        cursor.execute(query_sql)
        test_record = cursor.fetchone()
        
        if test_record:
            print("📄 Inserted test record details:")
            print(f"   Title: {test_record[0]}")
            print(f"   Group: {test_record[1]}")
            print(f"   Customer: {test_record[2]}")
            print(f"   Bulk PO QTY: {test_record[3]}")
            print(f"   Remark: {test_record[4]}")
        
        if new_count > original_count:
            print("✅ SUCCESS: Record successfully inserted and verified!")
        else:
            print("⚠️  WARNING: Record count did not increase as expected")
        
        cursor.close()
        conn.close()
        print(f"\n✅ End-to-end test completed for board '{board_name}'")
        print("\n🧹 TO CLEAN UP: Run cleanup_test_records() function or SQL:")
        print("   DELETE FROM dbo.MON_COO_Planning WHERE REMARK LIKE '%[TEST_INSERT]%';")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_records():
    """Remove test records from the database"""
    print("\n🧹 === CLEANUP: Removing Test Records ===")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check how many test records exist
        cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning WHERE REMARK LIKE '%[TEST_INSERT]%'")
        test_count = cursor.fetchone()[0]
        print(f"📊 Test records found: {test_count}")
        
        if test_count > 0:
            # Delete test records
            cursor.execute("DELETE FROM dbo.MON_COO_Planning WHERE REMARK LIKE '%[TEST_INSERT]%'")
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"🗑️  Deleted {deleted_count} test records")
            
            # Verify deletion
            cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning WHERE REMARK LIKE '%[TEST_INSERT]%'")
            remaining_count = cursor.fetchone()[0]
            print(f"📊 Remaining test records: {remaining_count}")
            
            if remaining_count == 0:
                print("✅ All test records successfully removed!")
            else:
                print(f"⚠️  {remaining_count} test records still remain")
        else:
            print("ℹ️  No test records found to clean up")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    
    # Uncomment the line below to run cleanup after confirming the test worked
    # cleanup_test_records()