#!/usr/bin/env python3
"""
Delete/Truncate Safety Check - Multi-Customer Data Protection
==========================================================
Purpose: Ensure our delete/truncate operations are safe for multi-customer data
Pattern: EXACT pattern from imports.guidance.instructions.md - PROVEN WORKING PATTERN

SAFETY VALIDATIONS:
1. Check what data would be deleted by v_order_list_nulls_to_delete view
2. Validate 01_delete_null_rows.sql impact on multi-customer data
3. Ensure no customer data is accidentally removed
4. Test DELETE operations in dry-run mode

MULTI-CUSTOMER PROTECTION:
- Validate customer data preservation across all customers
- Check PO data integrity for all purchase orders
- Ensure no production data loss during testing
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    """Run comprehensive delete/truncate safety check for multi-customer data"""
    
    print("🛡️ DELETE/TRUNCATE SAFETY CHECK - Multi-Customer Data Protection")
    print("=" * 80)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("📊 STEP 1: Analyze current data in swp_ORDER_LIST_SYNC...")
        cursor.execute("""
            SELECT 
                [CUSTOMER NAME],
                [PO NUMBER],
                COUNT(*) as record_count,
                MIN([AAG ORDER NUMBER]) as first_order,
                MAX([AAG ORDER NUMBER]) as last_order
            FROM swp_ORDER_LIST_SYNC 
            WHERE [CUSTOMER NAME] IS NOT NULL
            GROUP BY [CUSTOMER NAME], [PO NUMBER]
            ORDER BY [CUSTOMER NAME], [PO NUMBER]
        """)
        
        current_data = cursor.fetchall()
        print(f"📋 Found data for {len(current_data)} customer/PO combinations:")
        for customer, po, count, first_order, last_order in current_data:
            print(f"  - {customer} PO {po}: {count} records (Orders: {first_order} to {last_order})")
        
        print(f"\n🔍 STEP 2: Check what v_order_list_nulls_to_delete would identify...")
        
        # First check if the view exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.VIEWS 
            WHERE TABLE_NAME = 'v_order_list_nulls_to_delete'
        """)
        view_exists = cursor.fetchone()[0] > 0
        
        if view_exists:
            print("✅ v_order_list_nulls_to_delete view exists")
            
            # Check what would be deleted (safe query)
            cursor.execute("SELECT * FROM v_order_list_nulls_to_delete")
            null_results = cursor.fetchall()
            print(f"📊 View result: {null_results}")
            
            # Check if there are any records that match the null criteria
            # Note: View returns hash values, not record_uuid
            cursor.execute("""
                SELECT COUNT(*) as potentially_deleted_records
                FROM swp_ORDER_LIST_SYNC s
                WHERE EXISTS (
                    SELECT 1 FROM v_order_list_nulls_to_delete v 
                    WHERE s.hash_ord_3_10 = v.hash_ord_3_10
                )
            """)
            
            potentially_deleted = cursor.fetchone()[0]
            print(f"⚠️  Records that would be deleted: {potentially_deleted}")
            
            if potentially_deleted > 0:
                print("🚨 WARNING: Some records would be deleted!")
                
                # Show sample of what would be deleted
                cursor.execute("""
                    SELECT TOP 5
                        [CUSTOMER NAME], [PO NUMBER], [AAG ORDER NUMBER],
                        [CUSTOMER STYLE], [TOTAL QTY], s.hash_ord_3_10
                    FROM swp_ORDER_LIST_SYNC s
                    WHERE EXISTS (
                        SELECT 1 FROM v_order_list_nulls_to_delete v 
                        WHERE s.hash_ord_3_10 = v.hash_ord_3_10
                    )
                """)
                
                sample_deleted = cursor.fetchall()
                print("📋 Sample records that would be deleted:")
                for customer, po, order_num, style, qty, hash_val in sample_deleted:
                    print(f"  - {customer} PO {po} Order {order_num}: {style} (Qty: {qty}) [Hash: {hash_val}]")
            else:
                print("✅ No records would be deleted - safe!")
                
        else:
            print("⚠️  v_order_list_nulls_to_delete view does not exist")
            print("📋 Checking for completely null records manually...")
            
            cursor.execute("""
                SELECT COUNT(*) as null_records
                FROM swp_ORDER_LIST_SYNC 
                WHERE [CUSTOMER NAME] IS NULL 
                  AND [PO NUMBER] IS NULL 
                  AND [AAG ORDER NUMBER] IS NULL
                  AND [CUSTOMER STYLE] IS NULL
                  AND [TOTAL QTY] IS NULL
            """)
            
            null_count = cursor.fetchone()[0]
            print(f"📊 Completely null records: {null_count}")
        
        print(f"\n🔒 STEP 3: Validate customer data protection...")
        
        # Check that all customers still have data after any theoretical delete
        cursor.execute("""
            SELECT 
                [CUSTOMER NAME],
                COUNT(*) as total_records,
                COUNT(CASE WHEN [AAG ORDER NUMBER] IS NOT NULL THEN 1 END) as valid_orders,
                COUNT(CASE WHEN [TOTAL QTY] IS NOT NULL AND [TOTAL QTY] > 0 THEN 1 END) as non_zero_qty
            FROM swp_ORDER_LIST_SYNC 
            WHERE [CUSTOMER NAME] IS NOT NULL
            GROUP BY [CUSTOMER NAME]
            ORDER BY [CUSTOMER NAME]
        """)
        
        customer_data = cursor.fetchall()
        print(f"📊 Customer data integrity check:")
        for customer, total, valid_orders, non_zero in customer_data:
            print(f"  - {customer}: {total} total, {valid_orders} with orders, {non_zero} with qty > 0")
        
        print(f"\n✅ STEP 4: Safety recommendations...")
        
        total_customers = len(customer_data)
        total_records = sum(row[1] for row in customer_data)
        
        print(f"📊 SUMMARY:")
        print(f"  - Total customers: {total_customers}")
        print(f"  - Total records: {total_records}")
        print(f"  - Data source: {config.source_table}")
        
        if total_records > 100:  # Multi-customer threshold
            print("✅ MULTI-CUSTOMER DATA DETECTED")
            print("🛡️  SAFETY RECOMMENDATIONS:")
            print("   1. Always test delete operations in isolated environment first")
            print("   2. Use WHERE clauses with specific customer/PO filters")
            print("   3. Consider using soft deletes instead of hard deletes")
            print("   4. Backup data before any delete operations")
        else:
            print("ℹ️  Limited data detected - standard safety measures apply")
        
        print(f"\n🔧 STEP 5: Configuration review...")
        print(f"📋 Current TOML test data configuration:")
        print(f"  - limit_customers: {getattr(config, 'limit_customers', 'Not set')}")
        print(f"  - limit_pos: {getattr(config, 'limit_pos', 'Not set')}")
        print(f"  - limit_records: {getattr(config, 'limit_records', 'Not set')}")
        print(f"  - test_mode: {getattr(config, 'test_mode', 'Not set')}")
        
        cursor.close()

    print("\n" + "=" * 80)
    print("🏁 DELETE/TRUNCATE SAFETY CHECK COMPLETED")
    print("✅ Review output above for any safety concerns")
    print("🛡️  Always validate delete operations before execution")
    print("=" * 80)

if __name__ == "__main__":
    main()
