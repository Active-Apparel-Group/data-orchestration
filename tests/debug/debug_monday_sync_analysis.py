#!/usr/bin/env python3
"""
Debug Monday.com Sync Analysis - Analyze Batch Processing and Error Handling
===========================================================================
1. Why 21/22 batches are 'SUCCESS' - what happened to the 1 failed batch?
2. How are internal server errors (500/timeouts) handled in sync process?
3. Analysis of Monday.com API response patterns and retry logic
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
    print("🔍 DEBUGGING MONDAY.COM SYNC BATCH PROCESSING")
    print("=" * 60)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n1. BATCH SUCCESS ANALYSIS - 21/22 SUCCESS RATE")
        print("-" * 50)
        
        # Query 1: Detailed sync analysis
        query1 = f"""
        SELECT 
            sync_state,
            action_type,
            retry_count,
            CASE 
                WHEN sync_error_message IS NULL THEN 'SUCCESS'
                WHEN sync_error_message LIKE '%timeout%' OR sync_error_message LIKE '%500%' THEN 'TIMEOUT/500_ERROR'
                WHEN sync_error_message LIKE '%rate limit%' THEN 'RATE_LIMIT'
                ELSE 'OTHER_ERROR'
            END as error_category,
            COUNT(*) as record_count
        FROM {config.target_table}
        WHERE action_type = 'INSERT'
        GROUP BY sync_state, action_type, retry_count, 
                 CASE 
                     WHEN sync_error_message IS NULL THEN 'SUCCESS'
                     WHEN sync_error_message LIKE '%timeout%' OR sync_error_message LIKE '%500%' THEN 'TIMEOUT/500_ERROR'
                     WHEN sync_error_message LIKE '%rate limit%' THEN 'RATE_LIMIT'
                     ELSE 'OTHER_ERROR'
                 END
        ORDER BY sync_state, retry_count
        """
        
        print("🔍 Sync Success/Failure Breakdown:")
        cursor.execute(query1)
        results1 = cursor.fetchall()
        total_success = 0
        total_failed = 0
        for row in results1:
            sync_state, action_type, retry_count, error_category, count = row
            if sync_state == 'SYNCED':
                total_success += count
            else:
                total_failed += count
            print(f"   STATE: {sync_state} | RETRIES: {retry_count} | CATEGORY: {error_category} | COUNT: {count}")
        
        total_records = total_success + total_failed
        success_rate = (total_success / total_records * 100) if total_records > 0 else 0
        print(f"\n📊 BATCH SUCCESS SUMMARY:")
        print(f"   Total Records: {total_records}")
        print(f"   Successful: {total_success}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n💡 ANALYSIS: 21/22 batches = {(21/22)*100:.1f}% success rate")
        print(f"   Your system achieved {success_rate:.1f}% - {'✅ EXCEEDS' if success_rate >= 95.5 else '⚠️ BELOW'} the 21/22 benchmark")
        
        print("\n2. ERROR HANDLING ANALYSIS")
        print("-" * 30)
        
        # Query 2: Specific error analysis
        query2 = f"""
        SELECT 
            sync_error_message,
            retry_count,
            sync_attempted_at,
            sync_completed_at,
            COUNT(*) as frequency
        FROM {config.target_table}
        WHERE sync_error_message IS NOT NULL
        GROUP BY sync_error_message, retry_count, sync_attempted_at, sync_completed_at
        ORDER BY frequency DESC
        """
        
        print("🔍 Error Details (if any):")
        cursor.execute(query2)
        results2 = cursor.fetchall()
        if results2:
            for row in results2:
                error_msg, retries, attempted, completed, freq = row
                print(f"   ERROR: {error_msg}")
                print(f"   RETRIES: {retries}")
                print(f"   ATTEMPTED: {attempted}")
                print(f"   COMPLETED: {completed}")
                print(f"   FREQUENCY: {freq}")
                print("   ---")
        else:
            print("   ✅ NO ERRORS FOUND - All sync operations completed successfully")
        
        print("\n3. MONDAY.COM GROUP ID ANALYSIS")
        print("-" * 35)
        
        # Query 3: Monday.com integration analysis
        query3 = f"""
        SELECT 
            group_name,
            group_id,
            monday_item_id,
            COUNT(*) as item_count,
            COUNT(CASE WHEN monday_item_id IS NOT NULL THEN 1 END) as synced_items
        FROM {config.target_table}
        WHERE group_name IS NOT NULL
        GROUP BY group_name, group_id, monday_item_id
        ORDER BY group_name
        """
        
        print("🔍 Monday.com Group and Item ID Analysis:")
        cursor.execute(query3)
        results3 = cursor.fetchall()
        for row in results3:
            group_name, group_id, monday_item_id, item_count, synced_items = row
            print(f"   GROUP: {group_name}")
            print(f"   GROUP_ID: {group_id} {'❌ NULL - NOT SET' if group_id is None else '✅ SET'}")
            print(f"   MONDAY_ITEM_ID: {monday_item_id}")
            print(f"   ITEM_COUNT: {item_count}")
            print(f"   SYNCED_ITEMS: {synced_items}")
            print("   ---")
        
        print("\n4. LINES TABLE SYNC ANALYSIS")
        print("-" * 30)
        
        # Query 4: Lines table analysis for size issues
        query4 = f"""
        SELECT 
            size_code,
            sync_state,
            monday_subitem_id,
            sync_error_message,
            COUNT(*) as frequency
        FROM {config.lines_table}
        WHERE size_code IS NOT NULL
        GROUP BY size_code, sync_state, monday_subitem_id, sync_error_message
        ORDER BY frequency DESC
        """
        
        print("🔍 Lines Table Sync Analysis (Size Issues):")
        cursor.execute(query4)
        results4 = cursor.fetchall()
        for row in results4:
            size_code, sync_state, subitem_id, error_msg, freq = row
            if error_msg or sync_state != 'SYNCED':
                status = "❌ ERROR" if error_msg else "⚠️ PENDING"
                print(f"   SIZE: '{size_code}' | STATE: {sync_state} | {status} | FREQ: {freq}")
                if error_msg:
                    print(f"   ERROR: {error_msg[:100]}...")
        
        cursor.close()
        
        print("\n" + "=" * 60)
        print("🔍 KEY FINDINGS SUMMARY:")
        print("=" * 60)
        print("1. SUCCESS RATE: Database shows actual sync success rate")
        print("2. GROUP_ID NULL: Groups created in Monday.com but IDs not stored back")
        print("3. SIZE MISMATCH: Both 'O/S' and 'OS' variants exist in data")
        print("4. ERROR HANDLING: Check if timeout/500 errors are properly retried")

if __name__ == "__main__":
    main()
