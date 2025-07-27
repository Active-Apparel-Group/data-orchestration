#!/usr/bin/env python3
"""
DEBUG: Test 01_delete_null_rows.sql - Prove it does NOT delete GREYSON data
========================================================================

This test validates that 01_delete_null_rows.sql works correctly and does NOT delete 
our GREYSON PO 4755 test data (69 records).

Purpose: Prove the deletion step is not the root cause of the Enhanced Merge Orchestrator issue.
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🧪 DEBUG: Testing 01_delete_null_rows.sql with GREYSON data...")
    print("=" * 70)
    
    # Database connection
    with db.get_connection("orders") as connection:
        cursor = connection.cursor()
        
        # STEP 1: Count records in swp_ORDER_LIST_SYNC (should be 69 from transform_order_list.py)
        print(f"\n📊 STEP 1: Count records in swp_ORDER_LIST_SYNC")
        cursor.execute("SELECT COUNT(*) FROM [swp_ORDER_LIST_SYNC]")
        initial_count = cursor.fetchone()[0]
        print(f"   ✅ Initial record count: {initial_count}")
        
        # Verify it's GREYSON data
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT [CUSTOMER NAME]) as unique_customers,
                COUNT(DISTINCT [PO NUMBER]) as unique_pos
            FROM [swp_ORDER_LIST_SYNC]
            WHERE [CUSTOMER NAME] LIKE 'GREYSON%'
        """)
        greyson_data = cursor.fetchone()
        print(f"   📋 GREYSON data: {greyson_data[0]} records, {greyson_data[1]} customers, {greyson_data[2]} POs")
        
        # STEP 2: Run 01_delete_null_rows.sql (the exact same script)
        print(f"\n🗑️ STEP 2: Execute 01_delete_null_rows.sql")
        
        # Read the SQL file
        sql_file_path = repo_root / "sql" / "operations" / "order_list_transform" / "01_delete_null_rows.sql"
        with open(sql_file_path, "r", encoding="utf-8") as f:
            delete_sql = f.read().strip()
        
        print(f"   📄 SQL: {delete_sql}")
        
        # Execute the deletion
        try:
            cursor.execute(delete_sql)
            connection.commit()
            print(f"   ✅ Delete operation executed successfully")
        except Exception as e:
            print(f"   ❌ Delete operation failed: {e}")
            return
        
        # STEP 3: Count records after deletion
        print(f"\n📊 STEP 3: Count records after deletion")
        cursor.execute("SELECT COUNT(*) FROM [swp_ORDER_LIST_SYNC]")
        final_count = cursor.fetchone()[0]
        
        deleted_count = initial_count - final_count
        
        print(f"   📋 Results:")
        print(f"      Initial count: {initial_count}")
        print(f"      Final count: {final_count}")
        print(f"      Deleted count: {deleted_count}")
        
        # STEP 4: Verify GREYSON data still exists
        print(f"\n🔍 STEP 4: Verify GREYSON data preservation")
        cursor.execute("""
            SELECT 
                COUNT(*) as remaining_greyson,
                COUNT(DISTINCT [CUSTOMER STYLE]) as unique_styles,
                COUNT(DISTINCT [PO NUMBER]) as unique_pos
            FROM [swp_ORDER_LIST_SYNC]
            WHERE [CUSTOMER NAME] LIKE 'GREYSON%'
        """)
        greyson_remaining = cursor.fetchone()
        print(f"   📊 GREYSON remaining: {greyson_remaining[0]} records, {greyson_remaining[1]} styles, {greyson_remaining[2]} POs")
        
        # STEP 5: Analysis and conclusions
        print(f"\n🎯 ANALYSIS:")
        if deleted_count == 0:
            print(f"   ✅ PERFECT: 01_delete_null_rows.sql deleted {deleted_count} records")
            print(f"   ✅ GREYSON data preserved: {greyson_remaining[0]} records intact")
            print(f"   ✅ CONCLUSION: Delete script is NOT the problem!")
        else:
            print(f"   ⚠️ WARNING: Delete script removed {deleted_count} records")
            if greyson_remaining[0] == greyson_data[0]:
                print(f"   ✅ GREYSON data preserved: All {greyson_remaining[0]} records intact")
                print(f"   ℹ️ CONCLUSION: Delete script removed other records but preserved GREYSON data")
            else:
                print(f"   ❌ GREYSON data affected: {greyson_data[0] - greyson_remaining[0]} GREYSON records deleted")
                print(f"   🚨 CONCLUSION: Delete script IS affecting GREYSON data")
        
        # STEP 6: Show what would be deleted (if anything)
        print(f"\n🔍 STEP 6: Analyze deletion criteria")
        cursor.execute("""
            SELECT record_uuid, [CUSTOMER NAME], [CUSTOMER STYLE], [PO NUMBER], [TOTAL QTY]
            FROM [swp_ORDER_LIST_SYNC]
            WHERE record_uuid IN (
                SELECT record_uuid FROM [v_order_list_nulls_to_delete]
            )
        """)
        would_delete = cursor.fetchall()
        
        if would_delete:
            print(f"   ⚠️ Records that WOULD be deleted by view:")
            for record in would_delete[:5]:  # Show first 5
                print(f"      • {record[1]} | {record[2]} | {record[3]} | QTY: {record[4]}")
            if len(would_delete) > 5:
                print(f"      ... and {len(would_delete) - 5} more records")
        else:
            print(f"   ✅ No records match deletion criteria - GREYSON data is safe!")
        
        cursor.close()
    
    print(f"\n" + "=" * 70)
    print(f"🏁 01_DELETE_NULL_ROWS.SQL VALIDATION COMPLETE")
    print(f"=" * 70)

if __name__ == "__main__":
    main()
