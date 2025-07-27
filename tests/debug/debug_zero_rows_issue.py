"""
Debug: Zero Rows Issue Investigation
Purpose: Understand why the server-side ETL processed 0 rows
Date: July 10, 2025
"""

import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

logger = logger_helper.get_logger(__name__)

def investigate_zero_rows():
    """Investigate why server-side ETL processed 0 rows"""
    print("🔍 INVESTIGATING ZERO ROWS ISSUE")
    print("=" * 60)
    
    # Step 1: Check if RAW tables have any data at all
    print("\n1️⃣ CHECKING RAW TABLE DATA COUNTS")
    print("-" * 40)
    
    raw_tables_query = """
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
        ORDER BY TABLE_NAME
    """
    
    raw_tables = db.run_query(raw_tables_query, "orders")
    print(f"Found {len(raw_tables)} RAW tables")
    
    total_raw_rows = 0
    tables_with_data = []
    
    for idx, row in raw_tables.iterrows():
        table_name = row['TABLE_NAME']
        customer = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
        
        try:
            # Count total rows in this table
            count_query = f"SELECT COUNT(*) as row_count FROM [dbo].[{table_name}]"
            count_result = db.run_query(count_query, "orders")
            row_count = count_result.iloc[0]['row_count'] if not count_result.empty else 0
            
            total_raw_rows += row_count
            
            if row_count > 0:
                tables_with_data.append((customer, row_count))
                print(f"  ✅ {customer}: {row_count:,} rows")
            else:
                print(f"  ❌ {customer}: 0 rows")
                
        except Exception as e:
            print(f"  ❌ {customer}: ERROR - {e}")
    
    print(f"\nSUMMARY:")
    print(f"  Total RAW rows across all tables: {total_raw_rows:,}")
    print(f"  Tables with data: {len(tables_with_data)}")
    
    if total_raw_rows == 0:
        print("❌ ISSUE FOUND: All RAW tables are empty!")
        return
    
    # Step 2: Check for [AAG ORDER NUMBER] column existence
    print("\n2️⃣ CHECKING [AAG ORDER NUMBER] COLUMN")
    print("-" * 40)
    
    missing_aag_column = []
    for customer, row_count in tables_with_data[:5]:  # Check first 5 tables with data
        table_name = f"x{customer}_ORDER_LIST_RAW"
        
        try:
            # Check if [AAG ORDER NUMBER] column exists
            column_query = f"""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
                AND COLUMN_NAME = 'AAG ORDER NUMBER'
            """
            column_result = db.run_query(column_query, "orders")
            
            if column_result.empty:
                missing_aag_column.append(customer)
                print(f"  ❌ {customer}: Missing [AAG ORDER NUMBER] column")
                
                # Show actual columns
                all_columns_query = f"""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
                    ORDER BY ORDINAL_POSITION
                """
                columns = db.run_query(all_columns_query, "orders")
                column_list = columns['COLUMN_NAME'].tolist()[:10]  # First 10 columns
                print(f"     Actual columns (first 10): {column_list}")
            else:
                print(f"  ✅ {customer}: Has [AAG ORDER NUMBER] column")
                
        except Exception as e:
            print(f"  ❌ {customer}: ERROR checking columns - {e}")
    
    # Step 3: Check data with WHERE clause filter
    print("\n3️⃣ CHECKING WHERE CLAUSE FILTER")
    print("-" * 40)
    
    for customer, row_count in tables_with_data[:3]:  # Check first 3 tables
        table_name = f"x{customer}_ORDER_LIST_RAW"
        
        try:
            # Check rows with our WHERE clause
            filtered_query = f"""
                SELECT COUNT(*) as filtered_count
                FROM [dbo].[{table_name}]
                WHERE [AAG ORDER NUMBER] IS NOT NULL 
                AND LTRIM(RTRIM([AAG ORDER NUMBER])) != ''
            """
            filtered_result = db.run_query(filtered_query, "orders")
            filtered_count = filtered_result.iloc[0]['filtered_count'] if not filtered_result.empty else 0
            
            print(f"  {customer}:")
            print(f"    Total rows: {row_count:,}")
            print(f"    After WHERE filter: {filtered_count:,}")
            print(f"    Filtered out: {row_count - filtered_count:,} ({((row_count - filtered_count) / row_count * 100) if row_count > 0 else 0:.1f}%)")
            
            # Sample some [AAG ORDER NUMBER] values
            if row_count > 0:
                sample_query = f"""
                    SELECT TOP 5 [AAG ORDER NUMBER]
                    FROM [dbo].[{table_name}]
                """
                samples = db.run_query(sample_query, "orders")
                if not samples.empty:
                    sample_values = samples['AAG ORDER NUMBER'].tolist()
                    print(f"    Sample values: {sample_values}")
                
        except Exception as e:
            print(f"  ❌ {customer}: ERROR checking filter - {e}")
    
    # Step 4: Check staging table
    print("\n4️⃣ CHECKING STAGING TABLE")
    print("-" * 40)
    
    try:
        staging_count_query = "SELECT COUNT(*) as staging_count FROM [dbo].[swp_ORDER_LIST]"
        staging_result = db.run_query(staging_count_query, "orders")
        staging_count = staging_result.iloc[0]['staging_count'] if not staging_result.empty else 0
        
        print(f"  swp_ORDER_LIST rows: {staging_count:,}")
        
        if staging_count == 0:
            print("  ❌ Staging table is empty - this confirms the 0 rows issue")
        else:
            print(f"  ✅ Staging table has data: {staging_count:,} rows")
            
    except Exception as e:
        print(f"  ❌ Error checking staging table: {e}")

if __name__ == "__main__":
    investigate_zero_rows()
