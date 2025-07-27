"""
Detailed Transform Analysis
===========================

Get detailed analysis of the transform column matching issue.
"""

import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

from sql_test_helper import create_sql_tester
import logger_helper
import db_helper as db

def detailed_transform_analysis():
    """Detailed analysis of transform issue"""
    
    logger = logger_helper.get_logger(__name__)
    tester = create_sql_tester('orders')
    
    print("🔍 DETAILED TRANSFORM ANALYSIS")
    print("=" * 60)
    
    # Test table
    test_table = "xACTIVELY_BLACK_ORDER_LIST_RAW"
    
    # Get full column list
    print(f"\n📋 FULL COLUMN ANALYSIS FOR {test_table}")
    print("-" * 50)
    
    # Get ALL columns from raw table
    raw_columns_query = f"""
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{test_table}'
    ORDER BY ORDINAL_POSITION
    """
    
    raw_result = tester.test_query(
        "All Raw Table Columns",
        raw_columns_query,
        expected_min_rows=50  # Expect many columns
    )
    
    if raw_result['success']:
        print(f"✅ Raw table has {raw_result['row_count']} columns")
        # Use data_sample instead of data
        all_raw_columns = [row['COLUMN_NAME'] for row in raw_result.get('data_sample', [])]
        if len(all_raw_columns) < raw_result['row_count']:
            # Get full data using direct query
            import db_helper as db
            columns_df = db.run_query(raw_columns_query, 'orders')
            all_raw_columns = columns_df['COLUMN_NAME'].tolist()
        
        print(f"   All columns: {all_raw_columns[:20]}...")  # Show first 20
        print(f"   Last 10 columns: {all_raw_columns[-10:]}")
    else:
        print(f"❌ Failed to get raw columns: {raw_result}")
        return
    
    # Get ALL columns from staging table
    staging_columns_query = """
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'swp_ORDER_LIST'
    ORDER BY ORDINAL_POSITION
    """
    
    staging_result = tester.test_query(
        "All Staging Table Columns",
        staging_columns_query,
        expected_min_rows=400  # Expect many columns
    )
    
    if staging_result['success']:
        print(f"✅ Staging table has {staging_result['row_count']} columns")
        all_staging_columns = [row['COLUMN_NAME'] for row in staging_result['data']]
        print(f"   First 20 columns: {all_staging_columns[:20]}")
        print(f"   Last 10 columns: {all_staging_columns[-10:]}")
    else:
        print(f"❌ Failed to get staging columns: {staging_result}")
        return
    
    # Analyze overlap
    print(f"\n🔍 COLUMN OVERLAP ANALYSIS")
    print("-" * 30)
    
    raw_set = set(all_raw_columns)
    staging_set = set(all_staging_columns)
    
    overlap = raw_set.intersection(staging_set)
    raw_only = raw_set - staging_set
    staging_only = staging_set - raw_set
    
    print(f"📊 Overlap: {len(overlap)} columns")
    print(f"   Raw only: {len(raw_only)} columns")
    print(f"   Staging only: {len(staging_only)} columns")
    
    if raw_only:
        print(f"   Sample raw-only: {list(raw_only)[:10]}")
    if staging_only:
        print(f"   Sample staging-only: {list(staging_only)[:10]}")
    
    # Test the transform SQL generation
    print(f"\n🧪 TRANSFORM SQL TEST")
    print("-" * 25)
    
    try:
        sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))
        from order_list_transform import OrderListTransformer
        
        transformer = OrderListTransformer()
        insert_sql = transformer.generate_direct_insert_sql(test_table)
        
        # Parse the INSERT columns
        insert_part = insert_sql.split('INSERT INTO')[1].split('SELECT')[0]
        if '(' in insert_part and ')' in insert_part:
            column_section = insert_part.split('(')[1].split(')')[0]
            insert_columns = [col.strip().replace('[', '').replace(']', '') for col in column_section.split(',')]
            
            print(f"📝 INSERT attempts {len(insert_columns)} columns")
            print(f"   First 10: {insert_columns[:10]}")
            print(f"   Last 5: {insert_columns[-5:]}")
            
            # Check if all INSERT columns exist in staging table
            missing_in_staging = [col for col in insert_columns if col not in staging_set]
            if missing_in_staging:
                print(f"❌ {len(missing_in_staging)} INSERT columns not in staging table:")
                print(f"   Missing: {missing_in_staging[:10]}")
            else:
                print(f"✅ All INSERT columns exist in staging table")
        
        return {
            'success': True,
            'raw_columns': len(all_raw_columns),
            'staging_columns': len(all_staging_columns),
            'overlap': len(overlap),
            'sql_generated': True
        }
        
    except Exception as e:
        print(f"❌ Transform test failed: {e}")
        logger.exception("Transform analysis failed")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    try:
        results = detailed_transform_analysis()
        print(f"\n✅ Analysis complete: {results}")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
