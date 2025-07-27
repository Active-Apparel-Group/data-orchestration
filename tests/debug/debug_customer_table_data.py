"""
Debug script to check customer table data and test consolidation logic
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
import pandas as pd

def check_customer_table_data():
    """Check which customer tables have data"""
    print("=" * 80)
    print("CUSTOMER TABLE DATA ANALYSIS")
    print("=" * 80)
    
    # Get all customer tables
    query = """
    SELECT 
        TABLE_NAME,
        CASE
            WHEN TABLE_NAME LIKE 'x%ORDER_LIST%'
            THEN REPLACE(
                SUBSTRING(TABLE_NAME, 2, CHARINDEX('_ORDER_LIST', TABLE_NAME) - 2),
                '_', ' ')
            ELSE 'UNKNOWN'
        END as CUSTOMER_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo'
    AND TABLE_NAME LIKE 'x%ORDER_LIST%'
    ORDER BY TABLE_NAME
    """
    
    with db.get_connection('orders') as conn:
        tables_df = pd.read_sql(query, conn)
    
    print(f"Found {len(tables_df)} customer tables")
    
    tables_with_data = []
    
    for _, row in tables_df.iterrows():
        table_name = row['TABLE_NAME']
        customer_name = row['CUSTOMER_NAME']
        
        # Check row count
        try:
            count_query = f"SELECT COUNT(*) as row_count FROM dbo.[{table_name}]"
            with db.get_connection('orders') as conn:
                count_result = pd.read_sql(count_query, conn)
                row_count = count_result['row_count'].iloc[0]
            
            if row_count > 0:
                tables_with_data.append({
                    'table_name': table_name,
                    'customer_name': customer_name,
                    'row_count': row_count
                })
                print(f"✓ {table_name} ({customer_name}): {row_count:,} rows")
            else:
                print(f"  {table_name} ({customer_name}): 0 rows (empty)")
                
        except Exception as e:
            print(f"✗ {table_name} ({customer_name}): ERROR - {e}")
    
    print(f"\nSUMMARY:")
    print(f"Total tables: {len(tables_df)}")
    print(f"Tables with data: {len(tables_with_data)}")
    print(f"Empty tables: {len(tables_df) - len(tables_with_data)}")
    
    if tables_with_data:
        print(f"\nTables with data:")
        for table in tables_with_data:
            print(f"  - {table['table_name']}: {table['row_count']:,} rows")
    else:
        print(f"\nNo customer tables have data currently.")
        print(f"This means the orchestrator hasn't run yet or no files were processed.")
    
    return tables_with_data

def check_orders_unified_data():
    """Check ORDERS_UNIFIED for reference"""
    print("\n" + "=" * 80)
    print("ORDERS_UNIFIED REFERENCE CHECK")
    print("=" * 80)
    
    try:
        query = "SELECT COUNT(*) as row_count FROM dbo.ORDERS_UNIFIED"
        with db.get_connection('orders') as conn:
            result = pd.read_sql(query, conn)
            row_count = result['row_count'].iloc[0]
        
        print(f"ORDERS_UNIFIED contains: {row_count:,} rows")
        
        if row_count > 0:
            # Get sample data structure
            sample_query = "SELECT TOP 1 * FROM dbo.ORDERS_UNIFIED"
            with db.get_connection('orders') as conn:
                sample = pd.read_sql(sample_query, conn)
            
            print(f"Columns in ORDERS_UNIFIED: {len(sample.columns)}")
            print("Sample columns:")
            for i, col in enumerate(sample.columns[:10]):
                print(f"  {i+1}. {col}")
            if len(sample.columns) > 10:
                print(f"  ... and {len(sample.columns) - 10} more columns")
        
    except Exception as e:
        print(f"Error checking ORDERS_UNIFIED: {e}")

def check_order_list_existence():
    """Check if ORDER_LIST table exists"""
    print("\n" + "=" * 80)
    print("ORDER_LIST TABLE CHECK")
    print("=" * 80)
    
    try:
        query = """
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'ORDER_LIST' AND TABLE_SCHEMA = 'dbo'
        """
        
        with db.get_connection('orders') as conn:
            result = pd.read_sql(query, conn)
            exists = result['table_count'].iloc[0] > 0
        
        if exists:
            # Get row count
            count_query = "SELECT COUNT(*) as row_count FROM dbo.ORDER_LIST"
            with db.get_connection('orders') as conn:
                count_result = pd.read_sql(count_query, conn)
                row_count = count_result['row_count'].iloc[0]
            
            print(f"✓ ORDER_LIST table exists with {row_count:,} rows")
        else:
            print("✗ ORDER_LIST table does not exist")
            print("  The consolidation script will create it based on ORDERS_UNIFIED schema")
            
    except Exception as e:
        print(f"Error checking ORDER_LIST: {e}")

def main():
    """Main analysis function"""
    print("Starting customer table data analysis...")
    
    # Check customer tables
    tables_with_data = check_customer_table_data()
    
    # Check ORDERS_UNIFIED
    check_orders_unified_data()
    
    # Check ORDER_LIST
    check_order_list_existence()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    if not tables_with_data:
        print("\nRECOMMENDATION:")
        print("1. Run the XLSX orchestrator first to populate customer tables")
        print("2. Then run the ORDER_LIST consolidator")
        print("\nExample workflow:")
        print("  python notebooks/complete_xlsx_to_sql_orchestrator_with_comparison.py")
        print("  python notebooks/order_list_consolidator.py")
    else:
        print(f"\nREADY TO CONSOLIDATE:")
        print(f"Found {len(tables_with_data)} customer tables with data")
        print(f"Ready to run ORDER_LIST consolidation")

if __name__ == "__main__":
    main()
