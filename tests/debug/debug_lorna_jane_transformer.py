"""
Debug Transformer Logic for LORNA JANE
======================================

Investigate why CUSTOMER NAME is blank for LORNA JANE records
when canonical mapping is working correctly.
"""

import sys
from pathlib import Path
import pandas as pd

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

import db_helper as db
import logger_helper
from canonical_customer_manager import canonicalize_customer

def debug_lorna_jane_transformer():
    """Debug the transformer logic for LORNA JANE specifically"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("\n" + "="*80)
    print("🔍 DEBUGGING LORNA JANE TRANSFORMER LOGIC")
    print("="*80)
    
    # Check raw LORNA JANE table
    print("📊 Step 1: Check raw LORNA JANE table data")
    print("-" * 50)
    
    raw_table_query = """
        SELECT 
            [CUSTOMER NAME],
            COUNT(*) as record_count
        FROM [dbo].[xLORNA_JANE_ORDER_LIST_RAW]
        WHERE [CUSTOMER NAME] IS NOT NULL
        GROUP BY [CUSTOMER NAME]
        ORDER BY COUNT(*) DESC
    """
    
    try:
        raw_df = db.run_query(raw_table_query, 'orders')
        
        if not raw_df.empty:
            print("Raw LORNA JANE customer names:")
            for _, row in raw_df.iterrows():
                customer_name = row['CUSTOMER NAME']
                count = row['record_count']
                canonical = canonicalize_customer(customer_name, 'master_order_list')
                print(f"   '{customer_name}' → '{canonical}' ({count:,} records)")
        
        # Test the transformer logic simulation
        print("\n📊 Step 2: Simulate transformer logic")
        print("-" * 50)
        
        # Simulate what happens in generate_direct_insert_sql
        table_name = "xLORNA_JANE_ORDER_LIST_RAW"
        
        # Extract customer from table name (this is what transformer does)
        raw_customer = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
        original_customer = raw_customer.replace('_', ' ')
        
        print(f"Table name: {table_name}")
        print(f"Raw customer: {raw_customer}")
        print(f"Original customer: {original_customer}")
        
        # Test canonical mapping for extracted customer name
        canonical_customer = canonicalize_customer(original_customer, 'master_order_list')
        print(f"Canonical mapping: '{original_customer}' → '{canonical_customer}'")
        
        # Check if this matches what we expect
        if canonical_customer:
            print(f"✅ Canonical mapping successful: {canonical_customer}")
        else:
            print(f"❌ Canonical mapping failed - returns empty/null")
        
        # Test actual customer names from raw table
        print("\n📊 Step 3: Test canonical mapping for actual raw customer names")
        print("-" * 50)
        
        for _, row in raw_df.iterrows():
            actual_customer = row['CUSTOMER NAME']
            canonical = canonicalize_customer(actual_customer, 'master_order_list')
            print(f"   Raw: '{actual_customer}' → Canonical: '{canonical}'")
        
        # Check what's in the final ORDER_LIST
        print("\n📊 Step 4: Check ORDER_LIST results for LORNA JANE")
        print("-" * 50)
        
        order_list_query = """
            SELECT 
                [AAG ORDER NUMBER],
                [CUSTOMER NAME],
                [SOURCE_CUSTOMER_NAME],
                [_SOURCE_TABLE]
            FROM [dbo].[ORDER_LIST]
            WHERE [_SOURCE_TABLE] = 'xLORNA_JANE_ORDER_LIST_RAW'
            AND ([CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = '')
            ORDER BY [AAG ORDER NUMBER]
        """
        
        order_df = db.run_query(order_list_query, 'orders')
        
        if not order_df.empty:
            print(f"Found {len(order_df)} blank CUSTOMER NAME records:")
            print(order_df.head(5).to_string(index=False))
            
            # Check if SOURCE_CUSTOMER_NAME gives us clues
            unique_sources = order_df['SOURCE_CUSTOMER_NAME'].unique()
            print(f"\nUnique SOURCE_CUSTOMER_NAME values: {list(unique_sources)}")
        else:
            print("No blank CUSTOMER NAME records found in ORDER_LIST")
        
        # Check transformer code logic
        print("\n📊 Step 5: Analyze transformer logic issue")
        print("-" * 50)
        
        print("🔍 POTENTIAL ISSUES:")
        print("1. Table name extraction: LORNA_JANE → 'LORNA JANE'")
        print("2. Canonical mapping: 'LORNA JANE' should map to 'LORNA JANE'")
        print("3. But raw table has 'LORNA JANE (AU)' and 'LORNA JANE (NZ)'")
        print()
        print("💡 HYPOTHESIS:")
        print("The transformer extracts 'LORNA JANE' from table name,")
        print("but the raw table contains 'LORNA JANE (AU)' and 'LORNA JANE (NZ)'.")
        print("The canonical mapping for 'LORNA JANE' might be failing.")
        
        # Test the exact string used in transformer
        test_canonical = canonicalize_customer('LORNA JANE', 'master_order_list')
        print(f"\nTest: canonicalize_customer('LORNA JANE', 'master_order_list') = '{test_canonical}'")
        
        if not test_canonical or test_canonical.strip() == '':
            print("❌ FOUND THE BUG: 'LORNA JANE' (without region) has no canonical mapping!")
            print("   The transformer extracts 'LORNA JANE' but YAML only has regional variants.")
        else:
            print("✅ 'LORNA JANE' maps correctly")
            print("   Issue must be elsewhere in the transformer logic")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_lorna_jane_transformer()
