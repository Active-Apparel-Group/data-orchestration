#!/usr/bin/env python3
"""
PRODUCTION FIX: Test Enhanced Merge Orchestrator Group Name Population
Verify that group_name transformation is working correctly
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.merge_orchestrator import EnhancedMergeOrchestrator

logger = logger.get_logger(__name__)

def main():
    print("🔧 Enhanced Merge Orchestrator Group Name Test...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Test Enhanced Merge Orchestrator
    orchestrator = EnhancedMergeOrchestrator(config)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Test 1: Check swp_ORDER_LIST_SYNC table for group_name values
        print("\n📋 Test 1: Checking swp_ORDER_LIST_SYNC for group_name population...")
        try:
            cursor.execute("""
                SELECT TOP 10
                    [AAG ORDER NUMBER],
                    [CUSTOMER NAME], 
                    [CUSTOMER SEASON],
                    [AAG SEASON],
                    group_name,
                    sync_state
                FROM swp_ORDER_LIST_SYNC
                WHERE sync_state = 'NEW'
                ORDER BY created_at DESC
            """)
            
            records = cursor.fetchall()
            if records:
                print(f"Found {len(records)} NEW records in swp_ORDER_LIST_SYNC:")
                for record in records:
                    group_status = "✅ HAS GROUP" if record[4] else "❌ NO GROUP"
                    print(f"  - Order: {record[0]} | Customer: {record[1]} | Season: {record[2]} | Group: {record[4]} | {group_status}")
            else:
                print("❌ No NEW records found in swp_ORDER_LIST_SYNC")
                
        except Exception as e:
            print(f"❌ Cannot query swp_ORDER_LIST_SYNC: {str(e)}")
        
        # Test 2: Manually test group name transformation logic
        print("\n🧪 Test 2: Manual group name transformation logic...")
        cursor.execute("""
            SELECT TOP 5
                [CUSTOMER NAME],
                [CUSTOMER SEASON],
                [AAG SEASON],
                CASE 
                    WHEN [CUSTOMER SEASON] is not null
                        THEN CONCAT([CUSTOMER NAME], ' ', [CUSTOMER SEASON])
                    WHEN [CUSTOMER SEASON] is null and [AAG SEASON] is not null
                        THEN CONCAT([CUSTOMER NAME], ' ', [AAG SEASON])
                    ELSE 'check'
                END as computed_group_name
            FROM FACT_ORDER_LIST
            ORDER BY created_at DESC
        """)
        
        records = cursor.fetchall()
        print("Group name transformation logic test:")
        for record in records:
            print(f"  - Customer: {record[0]} | Customer Season: {record[1]} | AAG Season: {record[2]} | → Group: {record[3]}")
        
        cursor.close()

if __name__ == "__main__":
    main()
