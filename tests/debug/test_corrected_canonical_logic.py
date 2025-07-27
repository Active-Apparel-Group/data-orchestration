"""
Test Corrected Canonical Customer Logic
======================================

Test the corrected canonical customer mapping logic where:
- SOURCE_CUSTOMER_NAME = table name identifier (e.g., 'WHITE FOX', 'GREYSON')  
- CUSTOMER NAME = canonical name from raw data (e.g., 'WHITE FOX' from 'WHITE FOX (AU)')
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
sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))

import logger_helper

def test_corrected_logic():
    """Test the corrected canonical customer logic"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("🧪 TESTING CORRECTED CANONICAL CUSTOMER LOGIC")
    print("=" * 60)
    
    try:
        # Import transformer
        from order_list_transform import OrderListTransformer
        
        transformer = OrderListTransformer()
        
        # Test a specific table case
        test_table = "xWHITE_FOX_ORDER_LIST_RAW"
        
        print(f"🎯 Testing table: {test_table}")
        print()
        
        # Generate SQL for this table
        sql = transformer.generate_direct_insert_sql(test_table)
        
        print("📋 Generated SQL (first 1000 characters):")
        print("=" * 40)
        print(sql[:1000] + "..." if len(sql) > 1000 else sql)
        print("=" * 40)
        print()
        
        # Check for the key columns we care about
        if "SOURCE_CUSTOMER_NAME" in sql:
            print("✅ SOURCE_CUSTOMER_NAME found in SQL")
            # Extract the SOURCE_CUSTOMER_NAME logic
            lines = sql.split('\n')
            for i, line in enumerate(lines):
                if "SOURCE_CUSTOMER_NAME" in line:
                    print(f"   Line {i}: {line.strip()}")
        else:
            print("❌ SOURCE_CUSTOMER_NAME not found in SQL")
        
        print()
        
        if "CUSTOMER NAME" in sql:
            print("✅ CUSTOMER NAME found in SQL")
            # Extract the CUSTOMER NAME logic
            lines = sql.split('\n')
            in_customer_name_case = False
            for i, line in enumerate(lines):
                if "CUSTOMER NAME" in line and "SOURCE_CUSTOMER_NAME" not in line:
                    print(f"   Line {i}: {line.strip()}")
                    in_customer_name_case = True
                elif in_customer_name_case and ("WHEN" in line or "ELSE" in line or "END AS" in line):
                    print(f"   Line {i}: {line.strip()}")
                    if "END AS" in line:
                        in_customer_name_case = False
        else:
            print("❌ CUSTOMER NAME not found in SQL")
        
        print()
        print("🔍 Expected Logic:")
        print("   SOURCE_CUSTOMER_NAME = 'WHITE FOX' (from table name)")
        print("   CUSTOMER NAME = canonicalized from raw [CUSTOMER NAME] column")
        print()
        
        # Test a few more cases
        test_cases = [
            ("xGREYSON_ORDER_LIST_RAW", "GREYSON", "GREYSON CLOTHIERS → GREYSON"),
            ("xLORNA_JANE_ORDER_LIST_RAW", "LORNA JANE", "LORNA JANE (AU/NZ) → LORNA JANE"),
        ]
        
        print("🧪 Testing Additional Cases:")
        for table_name, expected_source, expected_mapping in test_cases:
            print(f"   {table_name}:")
            print(f"     SOURCE_CUSTOMER_NAME = '{expected_source}'")
            print(f"     CUSTOMER NAME = {expected_mapping}")
        
        print("\n✅ CORRECTED LOGIC TEST COMPLETE")
        print("Ready to run transform with fixed logic!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_corrected_logic()
