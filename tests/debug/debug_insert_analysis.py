"""
Debug: Server-Side INSERT Analysis
Purpose: Check why INSERT statements are returning 0 rows
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
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
from transform_generator_order_lists import load_yaml
from precision_transformer import create_precision_transformer

logger = logger_helper.get_logger(__name__)

def analyze_insert_issue():
    """Analyze why server-side INSERT statements return 0 rows"""
    print("🔍 ANALYZING SERVER-SIDE INSERT ISSUE")
    print("=" * 60)
    
    # Test with one customer that has data
    test_customer = "GREYSON"
    table_name = f"x{test_customer}_ORDER_LIST_RAW"
    
    print(f"Testing with: {test_customer}")
    print(f"Table: {table_name}")
    
    # Step 1: Verify table has data
    print(f"\n1️⃣ VERIFYING RAW TABLE DATA")
    print("-" * 40)
    
    count_query = f"SELECT COUNT(*) as total_rows FROM [dbo].[{table_name}]"
    total_result = db.run_query(count_query, "orders")
    total_rows = total_result.iloc[0]['total_rows'] if not total_result.empty else 0
    print(f"  Total rows in {table_name}: {total_rows:,}")
    
    if total_rows == 0:
        print("  ❌ No data to work with!")
        return
    
    # Step 2: Check WHERE clause filtering
    print(f"\n2️⃣ CHECKING WHERE CLAUSE FILTERING")
    print("-" * 40)
    
    where_query = f"""
        SELECT COUNT(*) as filtered_rows
        FROM [dbo].[{table_name}]
        WHERE [AAG ORDER NUMBER] IS NOT NULL 
        AND LTRIM(RTRIM([AAG ORDER NUMBER])) != ''
    """
    filtered_result = db.run_query(where_query, "orders")
    filtered_rows = filtered_result.iloc[0]['filtered_rows'] if not filtered_result.empty else 0
    print(f"  Rows after WHERE filter: {filtered_rows:,}")
    print(f"  Filtered out: {total_rows - filtered_rows:,} ({((total_rows - filtered_rows) / total_rows * 100) if total_rows > 0 else 0:.1f}%)")
    
    if filtered_rows == 0:
        print("  ❌ WHERE clause filters out ALL data!")
        
        # Sample the [AAG ORDER NUMBER] values
        sample_query = f"""
            SELECT TOP 10 
                [AAG ORDER NUMBER],
                CASE 
                    WHEN [AAG ORDER NUMBER] IS NULL THEN 'NULL'
                    WHEN LTRIM(RTRIM([AAG ORDER NUMBER])) = '' THEN 'EMPTY'
                    ELSE 'VALID'
                END as status
            FROM [dbo].[{table_name}]
        """
        samples = db.run_query(sample_query, "orders")
        print(f"  Sample [AAG ORDER NUMBER] values:")
        for _, row in samples.iterrows():
            print(f"    '{row['AAG ORDER NUMBER']}' -> {row['status']}")
        return
    
    # Step 3: Load YAML and check column mapping
    print(f"\n3️⃣ CHECKING YAML COLUMN MAPPING")
    print("-" * 40)
    
    yaml_path = repo_root / "pipelines" / "utils" / "order_list_schema.yml"
    metadata = load_yaml(yaml_path)
    print(f"  YAML columns defined: {len(metadata['columns'])}")
    
    # Get actual table columns
    columns_query = f"""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
    """
    columns_result = db.run_query(columns_query, "orders")
    table_columns = set(columns_result['COLUMN_NAME'].tolist())
    print(f"  Actual table columns: {len(table_columns)}")
    
    # Check mapping success
    mapped_columns = 0
    for col in metadata["columns"]:
        canonical_name = col["name"]
        candidates = [canonical_name] + col.get("aliases", [])
        
        matched = any(candidate in table_columns for candidate in candidates)
        if matched:
            mapped_columns += 1
    
    print(f"  Successfully mapped: {mapped_columns}/{len(metadata['columns'])} ({(mapped_columns/len(metadata['columns'])*100):.1f}%)")
    
    # Step 4: Check staging table structure
    print(f"\n4️⃣ CHECKING STAGING TABLE")
    print("-" * 40)
    
    staging_table = "swp_ORDER_LIST"
    try:
        staging_columns_query = f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{staging_table}'
            ORDER BY ORDINAL_POSITION
        """
        staging_columns_result = db.run_query(staging_columns_query, "orders")
        staging_columns = staging_columns_result['COLUMN_NAME'].tolist()
        print(f"  Staging table columns: {len(staging_columns)}")
        print(f"  First 10 columns: {staging_columns[:10]}")
        
        # Check if staging table exists and is empty
        staging_count_query = f"SELECT COUNT(*) as staging_rows FROM [dbo].[{staging_table}]"
        staging_count_result = db.run_query(staging_count_query, "orders")
        staging_rows = staging_count_result.iloc[0]['staging_rows'] if not staging_count_result.empty else 0
        print(f"  Current staging rows: {staging_rows:,}")
        
    except Exception as e:
        print(f"  ❌ Error checking staging table: {e}")
    
    # Step 5: Test a simplified INSERT
    print(f"\n5️⃣ TESTING SIMPLIFIED INSERT")
    print("-" * 40)
    
    try:
        # Try a very simple INSERT with just a few columns
        simple_insert = f"""
            INSERT INTO [{staging_table}] ([AAG ORDER NUMBER], [CUSTOMER NAME])
            SELECT 
                [AAG ORDER NUMBER],
                '{test_customer}' as [CUSTOMER NAME]
            FROM [dbo].[{table_name}]
            WHERE [AAG ORDER NUMBER] IS NOT NULL 
            AND LTRIM(RTRIM([AAG ORDER NUMBER])) != ''
        """
        
        print(f"  Executing simplified INSERT...")
        result = db.execute(simple_insert, "orders")
        rows_affected = result.rowcount if hasattr(result, 'rowcount') else 0
        print(f"  ✅ Simplified INSERT: {rows_affected} rows")
        
        if rows_affected > 0:
            print(f"  ✅ SUCCESS! The issue is with the complex column mapping")
        else:
            print(f"  ❌ Still 0 rows - issue is with basic WHERE clause or data")
            
    except Exception as e:
        print(f"  ❌ Error with simplified INSERT: {e}")
    
    # Step 6: Check precision transformer issues
    print(f"\n6️⃣ CHECKING PRECISION TRANSFORMER")
    print("-" * 40)
    
    try:
        precision_transformer = create_precision_transformer()
        print(f"  Precision transformer loaded: {len(precision_transformer.schema_types)} columns")
        
        # Check if any transforms are causing issues
        sample_transforms = list(precision_transformer.schema_types.items())[:5]
        print(f"  Sample transforms:")
        for col_name, schema_type in sample_transforms:
            transform = precision_transformer.get_precision_transform(col_name)
            print(f"    {col_name} ({schema_type}): {transform is not None}")
            
    except Exception as e:
        print(f"  ❌ Error with precision transformer: {e}")

if __name__ == "__main__":
    analyze_insert_issue()
