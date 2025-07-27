"""
Debug Canonical Customer Mapping for Table Name Extraction
==========================================================

Test if all table names can be properly mapped to canonical customers.
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

import db_helper as db
from canonical_customer_manager import canonicalize_customer

def test_table_name_canonical_mapping():
    """Test canonical mapping for all table names"""
    
    print("🧪 TESTING TABLE NAME → CANONICAL CUSTOMER MAPPING")
    print("=" * 60)
    
    # Get all RAW tables
    raw_tables_query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
        ORDER BY TABLE_NAME
    """
    
    raw_tables_df = db.run_query(raw_tables_query, 'orders')
    
    print(f"Testing {len(raw_tables_df)} table names...")
    print()
    
    failed_mappings = []
    
    for idx, row in raw_tables_df.iterrows():
        table_name = row['TABLE_NAME']
        
        # Simulate transformer logic exactly
        raw_customer = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
        original_customer = raw_customer.replace('_', ' ')
        
        # Test canonical mapping
        try:
            canonical_customer = canonicalize_customer(original_customer, 'master_order_list')
            
            if canonical_customer and canonical_customer.strip():
                print(f"✅ {table_name}")
                print(f"   {original_customer} → {canonical_customer}")
            else:
                print(f"❌ {table_name}")
                print(f"   {original_customer} → EMPTY/NULL")
                failed_mappings.append({
                    'table_name': table_name,
                    'extracted_name': original_customer,
                    'canonical_result': canonical_customer
                })
        except Exception as e:
            print(f"❌ {table_name}")
            print(f"   {original_customer} → ERROR: {e}")
            failed_mappings.append({
                'table_name': table_name,
                'extracted_name': original_customer,
                'error': str(e)
            })
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total tables: {len(raw_tables_df)}")
    print(f"Failed mappings: {len(failed_mappings)}")
    print(f"Success rate: {((len(raw_tables_df) - len(failed_mappings)) / len(raw_tables_df) * 100):.1f}%")
    
    if failed_mappings:
        print("\n🚨 FAILED MAPPINGS:")
        for failure in failed_mappings:
            table = failure['table_name']
            name = failure['extracted_name']
            if 'error' in failure:
                print(f"   {table}: '{name}' → ERROR: {failure['error']}")
            else:
                result = failure.get('canonical_result', 'UNKNOWN')
                print(f"   {table}: '{name}' → '{result}'")

if __name__ == "__main__":
    test_table_name_canonical_mapping()
