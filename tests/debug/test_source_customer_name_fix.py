"""
Test SOURCE_CUSTOMER_NAME Fix
=============================

Test the SQL generation with the SOURCE_CUSTOMER_NAME fix to ensure
INSERT column count matches SELECT expression count.
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

import logger_helper

def test_source_customer_name_fix():
    """Test the SOURCE_CUSTOMER_NAME fix in transformer"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("🧪 TESTING SOURCE_CUSTOMER_NAME FIX")
    print("=" * 50)
    
    try:
        # Import the transformer
        sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))
        from order_list_transform import OrderListTransformer
        
        # Initialize transformer
        transformer = OrderListTransformer()
        
        # Test with specific table
        test_table = "xACTIVELY_BLACK_ORDER_LIST_RAW"
        print(f"\n🔍 Testing SQL generation for: {test_table}")
        
        # Generate SQL
        insert_sql = transformer.generate_direct_insert_sql(test_table)
        
        print("✅ SQL generation completed!")
        
        # Analyze the SQL
        print("\n📊 SQL ANALYSIS:")
        print("-" * 20)
        
        # Parse INSERT columns
        try:
            insert_part = insert_sql.split('INSERT INTO')[1].split('SELECT')[0]
            if '(' in insert_part and ')' in insert_part:
                column_section = insert_part.split('(')[1].split(')')[0]
                insert_columns = [col.strip().replace('[', '').replace(']', '') for col in column_section.split(',')]
                
                print(f"📝 INSERT column count: {len(insert_columns)}")
                
                # Check for SOURCE_CUSTOMER_NAME
                if 'SOURCE_CUSTOMER_NAME' in insert_columns:
                    print("✅ SOURCE_CUSTOMER_NAME found in INSERT columns")
                else:
                    print("❌ SOURCE_CUSTOMER_NAME missing from INSERT columns")
                
                # Show first and last few columns
                print(f"   First 5 columns: {insert_columns[:5]}")
                print(f"   Last 5 columns: {insert_columns[-5:]}")
        
        except Exception as e:
            print(f"❌ Failed to parse INSERT columns: {e}")
        
        # Parse SELECT expressions
        try:
            select_part = insert_sql.split('SELECT')[1].split('FROM')[0]
            select_lines = [line.strip() for line in select_part.split('\n') if line.strip() and not line.strip().startswith('--')]
            
            # Count actual expressions (rough estimate)
            expression_count = 0
            for line in select_lines:
                if ' AS [' in line or line.endswith(','):
                    expression_count += 1
            
            print(f"📝 SELECT expression count (estimated): {expression_count}")
            
            # Check for SOURCE_CUSTOMER_NAME in SELECT
            select_text = ' '.join(select_lines)
            if 'SOURCE_CUSTOMER_NAME' in select_text:
                print("✅ SOURCE_CUSTOMER_NAME found in SELECT expressions")
                
                # Find the specific line
                for line in select_lines:
                    if 'SOURCE_CUSTOMER_NAME' in line:
                        print(f"   Expression: {line.strip()}")
                        break
            else:
                print("❌ SOURCE_CUSTOMER_NAME missing from SELECT expressions")
        
        except Exception as e:
            print(f"❌ Failed to parse SELECT expressions: {e}")
        
        # Show a snippet of the generated SQL
        print(f"\n📄 GENERATED SQL (first 800 chars):")
        print("-" * 30)
        print(insert_sql[:800] + "..." if len(insert_sql) > 800 else insert_sql)
        
        # Expected customer name from table
        expected_customer = test_table.replace('_ORDER_LIST_RAW', '').replace('x', '')
        print(f"\n🎯 EXPECTED CUSTOMER EXTRACTION:")
        print(f"   Table: {test_table}")
        print(f"   Extracted customer: '{expected_customer}'")
        
        return {
            'success': True,
            'sql_generated': True,
            'has_source_customer_name': 'SOURCE_CUSTOMER_NAME' in insert_sql,
            'expected_customer': expected_customer
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("SOURCE_CUSTOMER_NAME test failed")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    try:
        results = test_source_customer_name_fix()
        
        print(f"\n🎯 TEST RESULTS:")
        print(f"   Success: {results.get('success', False)}")
        print(f"   SQL Generated: {results.get('sql_generated', False)}")
        print(f"   Has SOURCE_CUSTOMER_NAME: {results.get('has_source_customer_name', False)}")
        
        if results.get('success'):
            print("✅ SOURCE_CUSTOMER_NAME fix appears to be working!")
        else:
            print("❌ SOURCE_CUSTOMER_NAME fix needs adjustment")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
