"""
Debug INSERT Column Generation
==============================

Debug why INSERT is only getting 12 columns instead of all DDL columns.
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

def debug_insert_generation():
    """Debug INSERT column generation"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("🐛 DEBUGGING INSERT COLUMN GENERATION")
    print("=" * 50)
    
    try:
        # Import transformer
        sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))
        from order_list_transform import OrderListTransformer
        
        transformer = OrderListTransformer()
        test_table = "xACTIVELY_BLACK_ORDER_LIST_RAW"
        
        print(f"🔍 Debugging: {test_table}")
        
        # Check DDL columns directly
        print(f"\n📋 DDL COLUMNS INFO:")
        print(f"   DDL column count: {len(transformer.ddl_columns)}")
        print(f"   Sample DDL columns: {list(transformer.ddl_columns.keys())[:10]}")
        
        # Check schema columns
        print(f"\n📋 SCHEMA INFO:")
        print(f"   Schema columns count: {len(transformer.schema_columns)}")
        print(f"   Sample schema columns: {list(transformer.schema_columns.keys())[:10]}")
        
        # Generate SQL and debug parsing
        insert_sql = transformer.generate_direct_insert_sql(test_table)
        
        # Find the INSERT section more carefully
        print(f"\n🔍 SQL STRUCTURE ANALYSIS:")
        
        # Look for the INSERT INTO pattern
        lines = insert_sql.split('\n')
        insert_line_found = False
        columns_section = ""
        
        for i, line in enumerate(lines):
            if 'INSERT INTO' in line:
                print(f"   INSERT found at line {i}: {line.strip()}")
                insert_line_found = True
                
                # Look for the column list (should be in parentheses after table name)
                for j in range(i, min(i + 10, len(lines))):
                    if '(' in lines[j] and ')' in lines[j]:
                        columns_section = lines[j]
                        print(f"   Columns line {j}: {lines[j].strip()}")
                        break
                break
        
        if not insert_line_found:
            print("   ❌ No INSERT INTO found!")
            return
        
        # Debug the exact parsing
        if columns_section:
            # Extract just the column part
            if '(' in columns_section and ')' in columns_section:
                start_paren = columns_section.find('(')
                end_paren = columns_section.rfind(')')
                column_text = columns_section[start_paren+1:end_paren]
                
                columns = [col.strip().replace('[', '').replace(']', '') for col in column_text.split(',')]
                print(f"\n📊 PARSED INSERT COLUMNS:")
                print(f"   Count: {len(columns)}")
                print(f"   First 10: {columns[:10]}")
                print(f"   Last 5: {columns[-5:]}")
                
                # Check if SOURCE_CUSTOMER_NAME is there
                if 'SOURCE_CUSTOMER_NAME' in columns:
                    pos = columns.index('SOURCE_CUSTOMER_NAME')
                    print(f"   SOURCE_CUSTOMER_NAME found at position {pos}")
                else:
                    print(f"   ❌ SOURCE_CUSTOMER_NAME not found in INSERT columns")
            else:
                print("   ❌ Could not find column parentheses")
        else:
            print("   ❌ Could not find columns section")
        
        # Show the first 500 chars of SQL for debugging
        print(f"\n🔍 FIRST 500 CHARS OF SQL:")
        print(insert_sql[:500])
        print("...")
        
        return {'success': True}
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        logger.exception("INSERT debug failed")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    debug_insert_generation()
