#!/usr/bin/env python3
"""
Working End-to-End Test: Monday.com API -> Database Insert -> Verification
FIXED VERSION with proper Monday.com value extraction
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
    return pyodbc.connect(conn_str, timeout=60)

def gql(query_string):
    """Execute GraphQL query against Monday.com API"""
    response = requests.post(
        "https://api.monday.com/v2",
        headers=HEADERS,
        json={"query": query_string}
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
              ... on DependencyValue {{
                display_value
              }}
              ... on MirrorValue {{
                display_value
              }}
              ... on BoardRelationValue {{
                display_value
              }}
              ... on FormulaValue {{
                display_value
              }}
              ... on TextValue {{
                text
              }}
              ... on LongTextValue {{
                text
              }}
              ... on StatusValue {{
                label
              }}
              ... on PeopleValue {{
                text
              }}
              ... on DropdownValue {{
                text
              }}
              ... on ItemIdValue {{
                item_id
              }}
              ... on NumbersValue {{
                number
              }}
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
        column_title = cv["column"]["title"]
        column_type = cv["column"]["type"]
        
        # Extract value based on column type and available fields
        extracted_value = None
        
        if column_type == "dropdown" and cv.get("text"):
            # For dropdown, use text field (e.g., "SPRING SUMMER 2026")
            extracted_value = cv["text"]
        elif column_type == "status" and cv.get("label"):
            # For status, use label field
            extracted_value = cv["label"]
        elif column_type == "numbers" and cv.get("number") is not None:
            # For numbers, use number field
            extracted_value = cv["number"]
        elif column_type == "item_id" and cv.get("item_id"):
            # For item ID, use item_id field
            extracted_value = cv["item_id"]
        elif cv.get("display_value") and cv.get("display_value") != "":
            # For mirror, formula, dependency, board_relation - use display_value
            extracted_value = cv["display_value"]
        elif cv.get("text"):
            # For text, long_text, people - use text field
            extracted_value = cv["text"]
        elif cv.get("value"):
            # Fallback to value field if nothing else available
            extracted_value = cv["value"]
        
        record[column_title] = extracted_value
    
    print(f"✅ Fetched record: {record['Title']}")
    return record, board_data["name"]

def prepare_record_for_insert(record):
    """Convert Monday.com record to DataFrame and prepare for database insert"""
    print("🔄 Preparing record for database insert...")
    
    # Create DataFrame
    df = pd.DataFrame([record])
    
    print(f"📋 Original DataFrame columns ({len(df.columns)}): {list(df.columns)}")
    
    # Drop unwanted columns that we know cause issues
    df = df.drop(columns=[c for c in ["AM (linked)", "board_name"] if c in df.columns])
    
    # Identify all date columns - look for columns with DATE in name or known date fields
    date_columns = [col for col in df.columns if 'DATE' in col.upper() or col in ['UpdateDate']]
    print(f"🔄 Found date columns: {date_columns}")
    
    # Identify numeric columns that should be integers/bigints
    numeric_columns = [
        'BULK PO QTY', 'Fabric Lead Time', 'Precut Quantity', 'Item ID',
        'QTY WIP', 'QTY FG', 'QTY INVOICED', 'QTY FCST',
        'QTY WIP CUT', 'QTY WIP SEW', 'QTY WIP FIN', 'QTY SCRAP', 'board_id'
    ]
    print(f"🔄 Found numeric columns: {[col for col in numeric_columns if col in df.columns]}")
    
    # Process date columns - Monday.com format is YYYY-MM-DD
    for col in date_columns:
        if col in df.columns and df[col].notna().any():
            try:
                original_val = df[col].iloc[0]
                print(f"🔍 Processing date column '{col}': original value = '{original_val}' (type: {type(original_val).__name__})")
                
                # Handle different date formats
                if pd.isna(original_val) or original_val in ['None', 'nan', None, '']:
                    df[col] = None
                    print(f"  → Set to None (was null/empty)")
                else:
                    # Try to parse the date
                    if isinstance(original_val, str):
                        # Remove any extra formatting or timezone info
                        clean_date = original_val.split('T')[0]  # Remove time part if present
                        if len(clean_date) == 10 and clean_date.count('-') == 2:
                            # Already in YYYY-MM-DD format
                            df[col] = clean_date
                            print(f"  → Kept as-is: '{clean_date}'")
                        else:
                            # Try to parse and reformat
                            parsed_date = pd.to_datetime(clean_date, errors='coerce')
                            if pd.notna(parsed_date):
                                df[col] = parsed_date.strftime('%Y-%m-%d')
                                print(f"  → Converted to: '{df[col].iloc[0]}'")
                            else:
                                df[col] = None
                                print(f"  → Could not parse, set to None")
                    else:
                        # Try to convert non-string to date
                        parsed_date = pd.to_datetime(original_val, errors='coerce')
                        if pd.notna(parsed_date):
                            df[col] = parsed_date.strftime('%Y-%m-%d')
                            print(f"  → Converted to: '{df[col].iloc[0]}'")
                        else:
                            df[col] = None
                            print(f"  → Could not parse, set to None")
                            
            except Exception as e:
                print(f"⚠️ Error processing date column {col}: {e}")
                df[col] = None
    
    # Process numeric columns
    for col in numeric_columns:
        if col in df.columns:
            try:
                original_val = df[col].iloc[0]
                print(f"🔍 Processing numeric column '{col}': original value = '{original_val}' (type: {type(original_val).__name__})")
                
                if pd.isna(original_val) or original_val in ['None', 'nan', None, '']:
                    df[col] = None
                    print(f"  → Set to None (was null/empty)")
                else:
                    # Convert to numeric
                    if isinstance(original_val, str):
                        # Clean the string first
                        clean_val = original_val.strip()
                        if clean_val == '' or clean_val.lower() in ['none', 'nan', 'null']:
                            df[col] = None
                            print(f"  → Set to None (was empty string)")
                        else:
                            # Try to convert to number
                            try:
                                # Try integer first
                                if '.' not in clean_val:
                                    numeric_val = int(clean_val)
                                else:
                                    numeric_val = float(clean_val)
                                df[col] = numeric_val
                                print(f"  → Converted to: {numeric_val}")
                            except ValueError:
                                df[col] = None
                                print(f"  → Could not convert '{clean_val}' to number, set to None")
                    else:
                        # Already numeric, just ensure no NaN
                        if pd.isna(original_val):
                            df[col] = None
                            print(f"  → Set to None (was NaN)")
                        else:
                            df[col] = original_val
                            print(f"  → Kept as-is: {original_val}")
                            
            except Exception as e:
                print(f"⚠️ Error processing numeric column {col}: {e}")
                df[col] = None
    
    # Convert remaining columns to strings, handling nulls properly
    for col in df.columns:
        if col not in date_columns and col not in numeric_columns:
            if df[col].dtype == 'object':
                current_val = df[col].iloc[0]
                if current_val is None or pd.isna(current_val):
                    df[col] = None
                else:
                    # Convert to string and clean
                    str_val = str(current_val).strip()
                    if str_val in ['None', 'nan', 'null', '']:
                        df[col] = None
                    else:
                        df[col] = str_val
            elif 'float' in str(df[col].dtype):
                # Replace NaN with None for proper NULL handling
                df[col] = df[col].where(pd.notna(df[col]), None)
    
    # Add test marker to REMARK field for identification
    if 'REMARK' in df.columns:
        if pd.isna(df['REMARK'].iloc[0]) or df['REMARK'].iloc[0] == 'None' or df['REMARK'].iloc[0] is None:
            df['REMARK'] = "[TEST_INSERT]"
        else:
            df['REMARK'] = str(df['REMARK'].iloc[0]) + " [TEST_INSERT]"
    else:
        df['REMARK'] = "[TEST_INSERT]"
    
    print(f"✅ Prepared DataFrame with {df.shape[0]} rows and {df.shape[1]} columns")
    return df

def main():
    """Main test function"""
    print("🚀 === Monday.com to Database End-to-End Test ===")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Test database connection
        print("\n=== STEP 1: Testing Database Connection ===")
        conn = get_db_connection()
        print("✅ Database connection successful!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning")
        original_count = cursor.fetchone()[0]
        print(f"📊 Current records in MON_COO_Planning: {original_count:,}")
        
        # Step 2: Fetch record from Monday.com
        print("\n=== STEP 2: Fetching Record from Monday.com ===")
        record, board_name = fetch_monday_record()
        
        # Step 3: Prepare record for insert
        print("\n=== STEP 3: Preparing Record for Insert ===")
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
        
        # Step 4: Insert record into database
        print("\n=== STEP 4: Inserting Record into Database ===")
        
        # Build the insert statement
        columns = list(df.columns)
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join([f'[{col}]' for col in columns])
        
        insert_sql = f"INSERT INTO dbo.MON_COO_Planning ({column_names}) VALUES ({placeholders})"
        
        # Get the values from the first row and debug them thoroughly
        values = []
        print("\n🔍 DEBUG: Values being inserted:")
        for i, col in enumerate(columns):
            val = df.iloc[0][col]
            if pd.isna(val) or val is None or val == 'None' or val == 'nan':
                final_val = None
                print(f"  [{i:2d}] {col:20} = None (was: {val})")
            else:
                final_val = val
                print(f"  [{i:2d}] {col:20} = {final_val} (type: {type(final_val).__name__})")
            values.append(final_val)
        
        print(f"\n🔄 SQL Statement: {insert_sql}")
        print(f"🔄 Executing insert with {len(values)} values...")
        
        try:
            cursor.execute(insert_sql, values)
            conn.commit()
            print("✅ Record inserted successfully!")
        except Exception as e:
            print(f"❌ INSERT FAILED: {e}")
            print("\n🔍 Detailed error analysis:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            
            # Let's try to identify the problematic value
            error_str = str(e).lower()
            if 'conversion' in error_str:
                print("🔍 This appears to be a data type conversion error")
                print("🔍 Values that might be causing issues:")
                for i, (col, val) in enumerate(zip(columns, values)):
                    if val is not None and isinstance(val, str):
                        if any(char.isdigit() for char in str(val)) or 'date' in col.lower():
                            print(f"  - Column {col}: '{val}' (might need conversion)")
            raise
        
        # Step 5: Verify the insert
        print("\n=== STEP 5: Verifying Insert ===")
        cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning")
        new_count = cursor.fetchone()[0]
        print(f"📊 Records after insert: {new_count:,}")
        print(f"📊 Records added: {new_count - original_count}")
        
        # Query for our specific test record
        cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning WHERE REMARK LIKE '%[TEST_INSERT]%'")
        test_records = cursor.fetchone()[0]
        print(f"📊 Test records found: {test_records}")
        
        if new_count > original_count:
            print("✅ SUCCESS: Record successfully inserted and verified!")
        else:
            print("⚠️  WARNING: Record count did not increase as expected")
        
        cursor.close()
        conn.close()
        print(f"\n✅ End-to-end test completed for board '{board_name}'")
        print("\n🧹 TO CLEAN UP: Run cleanup_test_records() function")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
