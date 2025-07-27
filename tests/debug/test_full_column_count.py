"""
Test Full Column Count Matching
===============================

Test that INSERT column count matches SELECT expression count with the SOURCE_CUSTOMER_NAME fix.
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

def test_full_column_count():
    """Test that column counts match between INSERT and SELECT"""
    
    logger = logger_helper.get_logger(__name__)
    tester = create_sql_tester('orders')
    
    print("🧪 TESTING FULL COLUMN COUNT MATCHING")
    print("=" * 50)
    
    try:
        # Import transformer
        sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))
        from order_list_transform import OrderListTransformer
        
        transformer = OrderListTransformer()
        test_table = "xACTIVELY_BLACK_ORDER_LIST_RAW"
        
        print(f"🔍 Testing: {test_table}")
        
        # Generate SQL
        insert_sql = transformer.generate_direct_insert_sql(test_table)
        
        # Parse INSERT columns precisely - look for the full column list
        insert_part = insert_sql.split('INSERT INTO')[1].split('SELECT')[0]
        
        # Find the column list in parentheses - it may span multiple lines
        paren_start = insert_part.find('(')
        paren_end = insert_part.rfind(')')
        
        if paren_start != -1 and paren_end != -1:
            column_section = insert_part[paren_start+1:paren_end]
            # Clean up whitespace and split by comma
            column_section = ' '.join(column_section.split())  # Normalize whitespace
            insert_columns = [col.strip().replace('[', '').replace(']', '') for col in column_section.split(',') if col.strip()]
        else:
            print("❌ Could not find INSERT column list in parentheses")
            return {'success': False}
        
        # Parse SELECT expressions more carefully - CASE statements contain commas!
        select_part = insert_sql.split('SELECT')[1].split('FROM')[0]
        
        # Smart parsing: count expressions by looking for 'AS [column_name]' patterns
        # Each expression ends with 'AS [column_name]'
        import re
        as_pattern = r'AS \[[^\]]+\]'
        select_expressions_count = len(re.findall(as_pattern, select_part))
        
        # Alternative method: count expressions by line breaks + AS patterns
        lines = select_part.split('\n')
        expression_lines = [line.strip() for line in lines if 'AS [' in line and line.strip()]
        
        print(f"\n📊 COLUMN COUNT ANALYSIS:")
        print(f"   INSERT columns: {len(insert_columns)}")
        print(f"   SELECT expressions: {select_expressions_count}")
        print(f"   Match: {'✅ YES' if len(insert_columns) == select_expressions_count else '❌ NO'}")
        
        # Check for key columns
        key_columns = ['AAG ORDER NUMBER', 'CUSTOMER NAME', 'SOURCE_CUSTOMER_NAME', '_SOURCE_TABLE']
        
        print(f"\n🔍 KEY COLUMN VERIFICATION:")
        for col in key_columns:
            in_insert = col in insert_columns
            in_select = col in insert_sql
            print(f"   {col}: INSERT {'✅' if in_insert else '❌'} | SELECT {'✅' if in_select else '❌'}")
        
        # Check staging table column count
        staging_query = """
        SELECT COUNT(*) as column_count FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'swp_ORDER_LIST'
        """
        
        staging_result = tester.test_query("Staging Column Count", staging_query)
        if staging_result['success']:
            staging_count = staging_result['data_sample'][0]['column_count']
            print(f"\n📋 STAGING TABLE INFO:")
            print(f"   Staging table columns: {staging_count}")
            print(f"   INSERT targeting: {len(insert_columns)} columns")
            print(f"   Coverage: {(len(insert_columns) / staging_count * 100):.1f}%")
        
        # Show first few expressions for verification
        print(f"\n🔍 SELECT EXPRESSION ANALYSIS:")
        print(f"   AS patterns found: {select_expressions_count}")
        print(f"   Expression lines: {len(expression_lines)}")
        print(f"   First few lines with AS:")
        for i, line in enumerate(expression_lines[:5]):
            print(f"   {i+1}: {line[:80]}...")
        
        return {
            'success': True,
            'insert_count': len(insert_columns),
            'select_count': select_expressions_count,
            'counts_match': len(insert_columns) == select_expressions_count,
            'has_source_customer_name': 'SOURCE_CUSTOMER_NAME' in insert_columns
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Column count test failed")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    try:
        results = test_full_column_count()
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Test success: {results.get('success', False)}")
        print(f"   Column counts match: {results.get('counts_match', False)}")
        print(f"   INSERT count: {results.get('insert_count', 0)}")
        print(f"   SELECT count: {results.get('select_count', 0)}")
        print(f"   Has SOURCE_CUSTOMER_NAME: {results.get('has_source_customer_name', False)}")
        
        if results.get('counts_match'):
            print("\n✅ COLUMN COUNT MATCHING - READY FOR PIPELINE TEST!")
        else:
            print("\n❌ COLUMN COUNT MISMATCH - NEEDS MORE FIXES")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
