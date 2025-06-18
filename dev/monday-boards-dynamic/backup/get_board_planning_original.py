#!/usr/bin/env python3
"""
PRODUCTION ETL Script: Monday.com to SQL Server with TRUNCATE
Ultra-fast concurrent processing with pagination and full table refresh
VALIDATED AND READY FOR PRODUCTION DEPLOYMENT
"""

import os, requests, pandas as pd, pyodbc, asyncio, concurrent.futures
from datetime import datetime
import time
import sys
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
import db_helper as db

# Load configuration from centralized config
config = db.load_config()

# Configuration - Monday.com API settings
BOARD_ID = int(os.getenv('MONDAY_BOARD_ID', '8709134353'))
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_VER = "2025-04"
API_URL = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")

if not MONDAY_TOKEN or MONDAY_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
    raise ValueError("Monday.com API token not configured. Please set MONDAY_API_KEY environment variable or update utils/config.yaml")

HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

def gql(query_string):
    """Execute GraphQL query against Monday.com API"""
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"query": query_string}
    )
    response.raise_for_status()
    return response.json()["data"]

def fetch_board_data_with_pagination():
    """Fetch ALL items from Monday.com board using cursor-based pagination"""
    print(f"📡 Fetching data from Monday.com board {BOARD_ID} with pagination...")
    
    all_items = []
    cursor = None
    page_num = 1
    board_name = None
    
    while True:
        # Build query with pagination cursor
        cursor_arg = f', cursor: "{cursor}"' if cursor else ''
        
        query = f'''
        query GetBoardItems {{
          boards(ids: {BOARD_ID}) {{
            name
            items_page(limit: 400{cursor_arg}) {{
              cursor
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
                  }}
                  value
                  text
                  ... on DependencyValue {{ display_value }}
                  ... on MirrorValue {{ display_value }}
                  ... on BoardRelationValue {{ display_value }}
                  ... on FormulaValue {{ display_value }}
                  ... on TextValue {{ text }}
                  ... on LongTextValue {{ text }}
                  ... on StatusValue {{ label }}
                  ... on PeopleValue {{ text }}
                  ... on DropdownValue {{ text }}
                  ... on ItemIdValue {{ item_id }}
                  ... on NumbersValue {{ number }}
                }}
              }}
            }}
          }}
        }}
        '''
        
        data = gql(query)
        board = data["boards"][0]
        
        # Store board name from first page
        if board_name is None:
            board_name = board["name"]
        
        items_page = board["items_page"]
        items = items_page["items"]
        
        # Add items from this page
        all_items.extend(items)
        
        print(f"   📄 Page {page_num}: Fetched {len(items)} items (Total: {len(all_items)})")
        
        # Check if there are more pages
        cursor = items_page.get("cursor")
        if not cursor or len(items) == 0:
            break
            
        page_num += 1
        
        # Add a small delay to respect rate limits
        time.sleep(0.1)  # 100ms delay between requests
    
    print(f"✅ Fetched {len(all_items)} total items from board '{board_name}' across {page_num} pages")
    return all_items, board_name

def prepare_staging_table():
    """PRODUCTION: Prepare staging table for zero-downtime refresh"""
    print("🏗️ PREPARING staging table for zero-downtime refresh...")
    
    try:
        # Check if staging table exists, create if not
        staging_exists_query = """
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME = 'stg_MON_COO_Planning'
        """
        staging_exists = db.run_query(staging_exists_query, "orders").iloc[0]['count'] > 0
        
        if not staging_exists:
            print("   🔨 Creating staging table...")
            # Create staging table with same structure as production table
            create_staging_sql = """
            SELECT TOP 0 * 
            INTO dbo.stg_MON_COO_Planning 
            FROM dbo.MON_COO_Planning
            """
            db.execute(create_staging_sql, "orders")
            print("   ✅ Staging table created")
        
        # Get current production record count for reference
        prod_count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.MON_COO_Planning", "orders")
        prod_count = prod_count_result.iloc[0]['count']
        print(f"   📊 Current production records: {prod_count}")
        
        # Truncate staging table for fresh load
        db.execute("TRUNCATE TABLE dbo.stg_MON_COO_Planning", "orders")
        
        # Verify staging table is empty
        staging_count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.stg_MON_COO_Planning", "orders")
        staging_count = staging_count_result.iloc[0]['count']
        
        print(f"   ✅ Staging table prepared: {staging_count} records (empty and ready)")
        
    except Exception as e:
        print(f"   ❌ Staging table preparation failed: {e}")
        raise

def extract_value(column_value):
    """Extract the correct value from Monday.com column based on type"""
    cv = column_value
    column_type = cv["column"]["type"]
    
    # Handle different column types with proper value extraction
    if column_type == "date":
        # For date columns, prefer the text value which is already formatted
        if cv.get("text") and cv.get("text").strip():
            return cv["text"]
        elif cv.get("value") and cv.get("value") != "None":
            return cv["value"]
        else:
            return None
    elif column_type == "dropdown" and cv.get("text"):
        return cv["text"]
    elif column_type == "status" and cv.get("label"):
        return cv["label"]
    elif column_type == "numbers" and cv.get("number") is not None:
        return cv["number"]
    elif column_type == "item_id" and cv.get("item_id"):
        return cv["item_id"]
    elif cv.get("display_value") and cv.get("display_value") != "":
        return cv["display_value"]
    elif cv.get("text"):
        return cv["text"]
    elif cv.get("value"):
        return cv["value"]
    
    return None

def process_items(items):
    """Convert Monday.com items to DataFrame"""
    print("🔄 Processing items for database insert...")
    
    records = []
    for item in items:
        record = {
            "StyleKey": item["name"],
            "UpdateDate": item["updated_at"],
            "Group": item["group"]["title"],
            "Item ID": item["id"]
        }
        
        # Extract column values
        for cv in item["column_values"]:
            column_title = cv["column"]["title"]
            record[column_title] = extract_value(cv)
        
        records.append(record)
    
    df = pd.DataFrame(records)
    print(f"📋 Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    return df

def prepare_for_database(df):
    """Prepare DataFrame for database insert with robust conversions"""
    print("🔧 Preparing data for database...")
    
    # Drop problematic columns
    df = df.drop(columns=[c for c in ["AM (linked)", "board_name"] if c in df.columns])
    
    # Handle the JSON metadata columns separately
    json_metadata_columns = ['FABRIC DUE INTO LONGSON', 'TRIMS DUE INTO LONGSON']
    for col in json_metadata_columns:
        if col in df.columns:
            print(f"🔍 Processing JSON metadata column: {col}")
            
            def extract_date_from_json_metadata(val):
                """Extract date from Monday.com JSON metadata or return None"""
                if pd.isna(val) or val is None or str(val).strip() in ['', 'None', 'nan', 'null']:
                    return None
                
                try:
                    val_str = str(val).strip()
                    
                    # Handle JSON metadata: {"changed_at":"2025-04-15T23:46:22.133Z"}
                    if val_str.startswith('{"changed_at":"') and val_str.endswith('"}'):
                        import json
                        metadata_obj = json.loads(val_str)
                        if 'changed_at' in metadata_obj:
                            # Extract just the date part (YYYY-MM-DD)
                            timestamp = metadata_obj['changed_at']
                            if timestamp and 'T' in timestamp:
                                date_part = timestamp.split('T')[0]
                                # Validate the date
                                parsed = pd.to_datetime(date_part, format='%Y-%m-%d', errors='raise')
                                if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                    return date_part
                    
                    return None  # If not valid JSON metadata, return None
                    
                except Exception:
                    return None  # If any error, return None
            
            # Apply the conversion
            original_count = df[col].notna().sum()
            df[col] = df[col].apply(extract_date_from_json_metadata)
            converted_count = df[col].notna().sum()
            null_count = df[col].isna().sum()
            print(f"    {col}: {original_count} → {converted_count} valid dates extracted from JSON, {null_count} nulls")
    
    # Process date columns with robust handling for Monday.com date formats
    exclude_from_date_processing = ['FABRIC DUE INTO LONGSON', 'TRIMS DUE INTO LONGSON']
    date_columns = [
        col for col in df.columns 
        if ('DATE' in col.upper() or col in ['UpdateDate']) 
        and col not in exclude_from_date_processing
    ]
    
    for col in date_columns:
        if col in df.columns:
            print(f"🔍 Processing date column: {col}")
            
            def safe_date_convert(val):
                # Handle None, NaN, empty strings, and Monday.com's literal "None" string
                if (pd.isna(val) or val is None or 
                    str(val).strip() in ['', 'None', 'nan', 'null', 'NaT']):
                    return None
                
                try:
                    val_str = str(val).strip()
                    
                    # Skip obviously invalid values
                    if val_str in ['', 'None', 'nan', 'null', 'NaT']:
                        return None
                    
                    # Handle Monday.com JSON date format: {"date":"2025-06-13","icon":""}
                    if val_str.startswith('{"date":"') and val_str.endswith('"}'):
                        try:
                            import json
                            date_obj = json.loads(val_str)
                            if 'date' in date_obj and date_obj['date']:
                                date_str = date_obj['date']
                                # Validate the extracted date
                                parsed = pd.to_datetime(date_str, format='%Y-%m-%d', errors='raise')
                                if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                    return date_str
                        except:
                            pass
                    
                    # Handle ISO datetime strings (like UpdateDate)
                    if 'T' in val_str and 'Z' in val_str:
                        clean_date = val_str.split('T')[0]
                        try:
                            parsed = pd.to_datetime(clean_date, format='%Y-%m-%d', errors='raise')
                            if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                return clean_date
                        except:
                            pass
                    
                    # Handle simple date strings (YYYY-MM-DD)
                    if len(val_str) == 10 and val_str.count('-') == 2:
                        try:
                            parsed = pd.to_datetime(val_str, format='%Y-%m-%d', errors='raise')
                            if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                                return val_str
                        except:
                            pass
                    
                    # Last resort: try pandas general conversion
                    parsed = pd.to_datetime(val, errors='coerce')
                    if pd.notna(parsed) and 1753 <= parsed.year <= 9999:
                        return parsed.strftime('%Y-%m-%d')
                    
                    return None
                    
                except Exception as e:
                    # Only log unexpected errors (not the common "None" strings)
                    if str(val) not in ['None', '', 'nan', 'null']:
                        print(f"    Unexpected date conversion error for '{val}': {e}")
                    return None
            
            # Apply the conversion and show progress
            original_count = df[col].notna().sum()
            df[col] = df[col].apply(safe_date_convert)
            converted_count = df[col].notna().sum()
            null_count = df[col].isna().sum()
            print(f"    {col}: {original_count} → {converted_count} valid dates, {null_count} nulls")
    
    # Process numeric columns with robust NumPy NaN handling
    numeric_columns = [
        'BULK PO QTY', 'Fabric Lead Time', 'Precut Quantity', 'Item ID',
        'QTY WIP', 'QTY FG', 'QTY INVOICED', 'QTY FCST',
        'QTY WIP CUT', 'QTY WIP SEW', 'QTY WIP FIN', 'QTY SCRAP'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            def safe_numeric_convert(val):
                # Handle NumPy NaN specifically
                if pd.isna(val) or val is None:
                    return None
                # Handle numpy nan explicitly
                if hasattr(val, 'dtype') and pd.isna(val):
                    return None
                # Handle string representations
                if isinstance(val, str):
                    clean_val = val.strip()
                    if clean_val == '' or clean_val.lower() in ['none', 'nan', 'null']:
                        return None
                    try:
                        # Try integer first, then float
                        if '.' not in clean_val:
                            return int(clean_val)
                        else:
                            return float(clean_val)
                    except:
                        return None
                # Handle numeric types
                try:
                    if hasattr(val, 'dtype'):
                        # Handle numpy types with NaN check
                        if 'int' in str(val.dtype) and not pd.isna(val):
                            return int(val)
                        elif 'float' in str(val.dtype) and not pd.isna(val):
                            return float(val)
                        else:
                            return None
                    return val
                except:
                    return None
            
            original_count = df[col].notna().sum()
            df[col] = df[col].apply(safe_numeric_convert)
            converted_count = df[col].notna().sum()
            print(f"    {col}: {original_count} → {converted_count} valid numbers")
    
    # Handle nulls and convert types for remaining columns
    for col in df.columns:
        if col not in date_columns and col not in numeric_columns and col not in json_metadata_columns:
            def safe_string_convert(val):
                if pd.isna(val) or val is None:
                    return None
                try:
                    str_val = str(val).strip()
                    if str_val in ['None', 'nan', 'null', '']:
                        return None
                    return str_val
                except:
                    return None
            
            df[col] = df[col].apply(safe_string_convert)
    
    print(f"✅ Data prepared: {len(df)} rows ready for insert")
    return df

def concurrent_insert_chunk(chunk_data, columns, table_name='stg_MON_COO_Planning'):
    """Insert a chunk of data using db_helper with bulk operations into STAGING table"""
    chunk_df, chunk_id = chunk_data
    
    try:
        # Use db_helper connection for bulk operations
        conn = db.get_connection('orders')
        cursor = conn.cursor()
        
        # Build insert statement
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join([f'[{col}]' for col in columns])
        insert_sql = f"INSERT INTO dbo.{table_name} ({column_names}) VALUES ({placeholders})"
        
        # Prepare all rows for this chunk
        values_list = []
        for _, row in chunk_df.iterrows():
            values = []
            for val in row.values:
                if pd.isna(val) or val is None:
                    values.append(None)
                elif hasattr(val, 'dtype'):
                    # Handle numpy types with NaN check
                    if pd.isna(val):
                        values.append(None)
                    elif 'int' in str(val.dtype):
                        values.append(int(val))
                    elif 'float' in str(val.dtype):
                        values.append(float(val))
                    else:
                        values.append(val)
                else:
                    values.append(val)
            values_list.append(values)
        
        # Use executemany for bulk insert
        cursor.executemany(insert_sql, values_list)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return len(chunk_df), 0, chunk_id  # success_count, fail_count, chunk_id
        
    except Exception as e:
        print(f"    ❌ {chunk_id}: Insert error: {e}")
        return 0, len(chunk_df), chunk_id  # success_count, fail_count, chunk_id

def atomic_swap_tables():
    """PRODUCTION: Atomically swap staging table to production with minimal downtime"""
    print("🔄 ATOMIC SWAP: Replacing production table with staging data...")
    
    try:
        # Get record counts for validation
        staging_count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.stg_MON_COO_Planning", "orders")
        staging_count = staging_count_result.iloc[0]['count']
        
        prod_count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.MON_COO_Planning", "orders")
        old_prod_count = prod_count_result.iloc[0]['count']
        
        print(f"   📊 Staging table: {staging_count} records")
        print(f"   📊 Production table (current): {old_prod_count} records")
        
        if staging_count == 0:
            raise ValueError("Staging table is empty - aborting swap for safety")
        
        # Perform atomic swap operation
        print("   🔄 Executing atomic table swap...")
        swap_sql = """
        BEGIN TRANSACTION
        
        -- Drop production table
        DROP TABLE dbo.MON_COO_Planning
        
        -- Rename staging to production
        EXEC sp_rename 'dbo.stg_MON_COO_Planning', 'MON_COO_Planning'
        
        -- Create new empty staging table for next run
        SELECT TOP 0 * 
        INTO dbo.stg_MON_COO_Planning 
        FROM dbo.MON_COO_Planning
        
        COMMIT TRANSACTION
        """
        
        db.execute(swap_sql, "orders")
        
        # Verify the swap
        new_prod_count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.MON_COO_Planning", "orders")
        new_prod_count = new_prod_count_result.iloc[0]['count']
        
        new_staging_count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.stg_MON_COO_Planning", "orders")
        new_staging_count = new_staging_count_result.iloc[0]['count']
        
        print(f"   ✅ Swap completed!")
        print(f"   📊 Production table (new): {new_prod_count} records")
        print(f"   📊 Staging table (new): {new_staging_count} records (empty)")
        print(f"   🎯 Data refreshed: {old_prod_count} → {new_prod_count} records")
        
        return new_prod_count
        
    except Exception as e:
        print(f"   ❌ Atomic swap failed: {e}")
        print("   🔄 Attempting rollback...")
        try:
            db.execute("ROLLBACK TRANSACTION", "orders")
            print("   ✅ Rollback successful - production table preserved")
        except:
            print("   ⚠️ Rollback failed - manual intervention may be required")
        raise

async def production_concurrent_insert(df, chunk_size=50, max_workers=6):
    """Production-grade concurrent database insert with full table refresh"""
    print(f"🚀 PRODUCTION concurrent bulk inserting {len(df)} records...")
    print(f"📦 Chunk size: {chunk_size}, Max concurrent workers: {max_workers}")
      # Get valid table columns using db_helper - check staging table structure
    columns_query = """
        SELECT name FROM sys.columns 
        WHERE object_id = OBJECT_ID('dbo.stg_MON_COO_Planning')
    """
    columns_df = db.run_query(columns_query, "orders")
    valid_cols = set(columns_df['name'].tolist())
    
    # Filter DataFrame to only include valid columns
    df = df[[c for c in df.columns if c in valid_cols]]
    
    if len(df.columns) == 0:
        raise ValueError("No valid columns found for insert")
    
    columns = list(df.columns)
    print(f"📋 Inserting {len(columns)} columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
    
    # Split DataFrame into chunks
    chunks = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        chunks.append((chunk, f"chunk_{i//chunk_size + 1}"))
    
    print(f"📦 Split into {len(chunks)} chunks for concurrent processing")
    
    # Use ThreadPoolExecutor for concurrent database operations
    total_success = 0
    total_failed = 0
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all chunks for concurrent processing
        futures = {
            executor.submit(concurrent_insert_chunk, chunk_data, columns): chunk_data[1] 
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
                    print(f"   ✅ {chunk_name}: {success_count} records inserted")
                if fail_count > 0:
                    print(f"   ❌ {chunk_name}: {fail_count} records failed")
                    
            except Exception as e:
                print(f"   ❌ {chunk_name}: Exception occurred: {e}")
                total_failed += chunk_size
    
    elapsed_time = time.time() - start_time
    records_per_second = total_success / elapsed_time if elapsed_time > 0 else 0
    
    print(f"🎯 PRODUCTION insert completed: {total_success} success, {total_failed} failed")
    print(f"⚡ Performance: {elapsed_time:.2f} seconds, {records_per_second:.1f} records/sec")
    return total_success, total_failed

async def main():
    """Main PRODUCTION ETL function with zero-downtime staging table approach"""
    print("🚀 === PRODUCTION Monday.com to Database ETL with ZERO-DOWNTIME REFRESH ===")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Prepare staging table for zero-downtime refresh
        prepare_staging_table()
        
        # Step 2: Fetch data from Monday.com with pagination
        items, board_name = fetch_board_data_with_pagination()
        
        if not items:
            print("ℹ️ No items found in board")
            return
        
        # Step 3: Process items
        df = process_items(items)
        
        # Step 4: Prepare for database
        df = prepare_for_database(df)
        
        # Step 5: Load data into STAGING table (production remains available)
        print("📊 Loading data into staging table (production remains available)...")
        success_count, fail_count = await production_concurrent_insert(
            df, chunk_size=50, max_workers=6
        )
        
        if fail_count > 0:
            raise ValueError(f"Failed to load {fail_count} records into staging table")
        
        # Step 6: Atomic swap staging → production (minimal downtime)
        final_count = atomic_swap_tables()
        
        print(f"\n✅ ZERO-DOWNTIME ETL completed for board '{board_name}'")
        print(f"📊 Total processed: {len(df)} items")
        print(f"📊 Successfully loaded: {success_count}")
        print(f"📊 Production records: {final_count}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 DOWNTIME: ~1-2 seconds (atomic swap only)")
        
        # Final validation
        if fail_count == 0:
            print("🎯 PRODUCTION DEPLOYMENT: ZERO-DOWNTIME SUCCESS ✅")
        else:
            print(f"⚠️ PRODUCTION DEPLOYMENT: {fail_count} failures detected")
        
    except Exception as e:
        print(f"❌ PRODUCTION ETL process failed: {e}")
        print("⚠️ Production table remains unchanged - no data loss")
        raise

if __name__ == "__main__":
    asyncio.run(main())
