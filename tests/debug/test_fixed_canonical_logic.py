"""
Test Fixed Canonical Customer Logic
===================================

Test the corrected canonical customer mapping logic.
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

def test_fixed_logic():
    """Test the fixed canonical customer logic"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("🧪 TESTING FIXED CANONICAL CUSTOMER LOGIC")
    print("=" * 50)
    
    try:
        # Import transformer
        sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))
        from order_list_transform import OrderListTransformer
        
        transformer = OrderListTransformer()
        
        # Test cases that should be fixed
        test_cases = [
            "xWHITE_FOX_ORDER_LIST_RAW",
            "xNASC_WHITE_FOX_ORDER_LIST_RAW", 
            "xGREYSON_ORDER_LIST_RAW",
            "xJOHNNIE_O_ORDER_LIST_RAW"
        ]
        
        for table_name in test_cases:
            print(f"\n🔍 Testing: {table_name}")
            
            # Generate SQL
            insert_sql = transformer.generate_direct_insert_sql(table_name)
            
            # Extract customer name transformations
            lines = insert_sql.split('\n')
            customer_name_line = None
            source_customer_name_line = None
            
            for line in lines:
                if " AS [CUSTOMER NAME]" in line:
                    customer_name_line = line.strip()
                elif " AS [SOURCE_CUSTOMER_NAME]" in line:
                    source_customer_name_line = line.strip()
            
            print(f"   CUSTOMER NAME: {customer_name_line}")
            print(f"   SOURCE_CUSTOMER_NAME: {source_customer_name_line}")
            
            # Validate the logic
            if customer_name_line and source_customer_name_line:
                # Should see canonical in CUSTOMER NAME, original in SOURCE_CUSTOMER_NAME
                if "WHITE FOX" in customer_name_line and "WHITE_FOX" not in customer_name_line:
                    print("   ✅ CUSTOMER NAME has canonical format (no underscores)")
                elif "GREYSON" in customer_name_line and "CLOTHIERS" not in customer_name_line:
                    print("   ✅ CUSTOMER NAME has canonical format")
                else:
                    print("   ⚠️  Check CUSTOMER NAME format")
                
                if "WHITE FOX" in source_customer_name_line or "GREYSON" in source_customer_name_line:
                    print("   ✅ SOURCE_CUSTOMER_NAME has original format")
                else:
                    print("   ⚠️  Check SOURCE_CUSTOMER_NAME format")
            
        return {'success': True}
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Fixed logic test failed")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    test_fixed_logic()
