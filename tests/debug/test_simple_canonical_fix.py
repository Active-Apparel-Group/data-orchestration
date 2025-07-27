#!/usr/bin/env python3
"""
Test the simple canonical fix approach
- INSERT with alias for SOURCE_CUSTOMER_NAME
- Bulk UPDATE for canonical CUSTOMER NAME
"""
import sys
from pathlib import Path

# Add project root for imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
from canonical_order_list_transformer import CanonicalOrderListTransformer

def test_canonical_transformer():
    """Test the canonical transformer with simplified approach"""
    
    # Initialize transformer
    transformer = CanonicalOrderListTransformer()
    
    # Test with a known table
    test_table = "xGREYSON_ORDER_LIST_RAW"
    
    # Get DDL columns (simplified - just key ones for testing)
    ddl_columns = [
        {'name': 'record_uuid', 'type': 'UNIQUEIDENTIFIER'},
        {'name': 'CUSTOMER NAME', 'type': 'NVARCHAR(100)'},
        {'name': 'SOURCE_CUSTOMER_NAME', 'type': 'NVARCHAR(100)'},
        {'name': 'PO NUMBER', 'type': 'NVARCHAR(255)'},
        {'name': '_SOURCE_TABLE', 'type': 'NVARCHAR(255)'}
    ]
    
    print(f"🧪 Testing canonical transformation for {test_table}")
    
    # Generate SQL
    sql = transformer.generate_canonical_transform_sql(
        table_name=test_table,
        ddl_columns=ddl_columns
    )
    
    print(f"\n📄 Generated SQL:")
    print("=" * 80)
    print(sql)
    print("=" * 80)
    
    # Check key elements
    checks = [
        ("Contains INSERT", "INSERT INTO" in sql),
        ("Contains UPDATE", "UPDATE" in sql),
        ("Contains transaction", "BEGIN TRANSACTION" in sql),
        ("Contains SOURCE_CUSTOMER_NAME alias", "[CUSTOMER NAME] AS [SOURCE_CUSTOMER_NAME]" in sql),
        ("Contains canonical update", "SET [CUSTOMER NAME] =" in sql),
        ("Contains source table filter", "_SOURCE_TABLE" in sql)
    ]
    
    print(f"\n✅ Validation Results:")
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}: {result}")
    
    all_passed = all(result for _, result in checks)
    print(f"\n🎯 Overall Result: {'✅ PASS' if all_passed else '❌ FAIL'}")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Testing Simple Canonical Fix Approach")
    print("-" * 50)
    
    success = test_canonical_transformer()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("💡 Approach: INSERT with alias + bulk UPDATE for canonical mapping")
    else:
        print("\n❌ Test failed - check the generated SQL")
    
    exit(0 if success else 1)
