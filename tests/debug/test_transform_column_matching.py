"""
Test Transform Column Matching 
==============================

Test the actual OrderListTransformer column matching logic to identify
where the column mismatch occurs.
"""

import sys
from pathlib import Path

# Add project paths
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

def test_transform_column_matching():
    """Test the actual transform column matching logic"""
    
    logger = logger_helper.get_logger(__name__)
    tester = create_sql_tester('orders')
    
    print("🔍 TESTING TRANSFORM COLUMN MATCHING")
    print("=" * 60)
    
    # Import the actual transformer
    sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))
    from order_list_transform import OrderListTransformer
    
    # Initialize transformer
    transformer = OrderListTransformer()
    
    # Test with a specific table
    test_table = "xACTIVELY_BLACK_ORDER_LIST_RAW"
    
    print(f"\n🧪 TESTING SQL GENERATION FOR: {test_table}")
    print("-" * 50)
    
    try:
        # Generate the SQL using the actual transformer method
        insert_sql = transformer.generate_direct_insert_sql(test_table)
        
        print("✅ SQL GENERATION SUCCESS")
        print("\n📄 GENERATED SQL (first 500 chars):")
        print("-" * 30)
        print(insert_sql[:500] + "..." if len(insert_sql) > 500 else insert_sql)
        
        # Let's also test the column analysis
        print(f"\n📊 COLUMN ANALYSIS FOR {test_table}:")
        print("-" * 30)
        
        # Get raw table columns
        raw_columns_query = f"""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{test_table}'
        ORDER BY ORDINAL_POSITION
        """
        
        raw_result = tester.test_query(
            "Raw Table Columns",
            raw_columns_query
        )
        
        if raw_result['success']:
            raw_columns = [row['COLUMN_NAME'] for row in raw_result['data_sample']]
            print(f"✅ Raw table columns ({len(raw_columns)}): {raw_columns[:10]}...")
        
        # Get staging table columns  
        staging_columns_query = """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'swp_ORDER_LIST'
        ORDER BY ORDINAL_POSITION
        """
        
        staging_result = tester.test_query(
            "Staging Table Columns",
            staging_columns_query
        )
        
        if staging_result['success']:
            staging_columns = [row['COLUMN_NAME'] for row in staging_result['data_sample']]
            print(f"✅ Staging table columns ({len(staging_columns)}): {staging_columns[:10]}...")
        
        # Analyze the generated SQL
        print(f"\n🔍 SQL ANALYSIS:")
        print("-" * 20)
        
        # Count columns in INSERT part
        insert_part = insert_sql.split('INSERT INTO')[1].split('SELECT')[0]
        if '(' in insert_part and ')' in insert_part:
            column_section = insert_part.split('(')[1].split(')')[0]
            insert_columns = [col.strip().replace('[', '').replace(']', '') for col in column_section.split(',')]
            print(f"📝 INSERT column count: {len(insert_columns)}")
            print(f"   First 5: {insert_columns[:5]}")
        
        # Count columns in SELECT part  
        select_part = insert_sql.split('SELECT')[1].split('FROM')[0]
        # This is more complex due to CASE statements, but let's get a rough count
        select_lines = [line.strip() for line in select_part.split('\n') if line.strip()]
        print(f"📝 SELECT expression count: {len(select_lines)}")
        print(f"   First 3 expressions: {select_lines[:3]}")
        
        return {
            'sql_generation_success': True,
            'generated_sql': insert_sql,
            'raw_column_count': len(raw_columns) if raw_result['success'] else 0,
            'staging_column_count': len(staging_columns) if staging_result['success'] else 0
        }
        
    except Exception as e:
        print(f"❌ SQL GENERATION FAILED: {e}")
        logger.exception("Transform SQL generation failed")
        return {
            'sql_generation_success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        results = test_transform_column_matching()
        
        print(f"\n✅ Test completed")
        print(f"   SQL generation: {'SUCCESS' if results.get('sql_generation_success') else 'FAILED'}")
        if 'raw_column_count' in results:
            print(f"   Raw columns: {results['raw_column_count']}")
            print(f"   Staging columns: {results['staging_column_count']}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
