#!/usr/bin/env python3
"""
Test Enhanced Merge Orchestrator - GREYSON PO 4755 ONLY
=======================================================
Purpose: Isolated test with only GREYSON PO 4755 data (69 records)
Location: tests/debug/test_enhanced_merge_greyson_only.py
Created: 2025-07-28

FOCUSED TEST APPROACH:
1. Clean all test tables
2. Create test data: GREYSON PO 4755 only (69 records)
3. Run Enhanced Merge Orchestrator on isolated data
4. Validate results with known data set
"""

import sys
from pathlib import Path

# EXACT working import pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.merge_orchestrator import EnhancedMergeOrchestrator

logger = logger.get_logger(__name__)

def main():
    print("🧪 ENHANCED MERGE ORCHESTRATOR - GREYSON PO 4755 ISOLATED TEST")
    print("===============================================================")
    print("Purpose: Test with isolated GREYSON data only (69 records)")
    print("Expected: All phases should pass with known test data")
    print("===============================================================")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        try:
            # Step 1: Clean test environment
            logger.info("🧹 Step 1: Cleaning test environment...")
            cleanup_queries = [
                "TRUNCATE TABLE ORDER_LIST_LINES",
                "DELETE FROM FACT_ORDER_LIST", 
                "DROP TABLE IF EXISTS swp_ORDER_LIST_SYNC"
            ]
            
            for query in cleanup_queries:
                try:
                    cursor.execute(query)
                    logger.info(f"   ✅ Executed: {query}")
                except Exception as e:
                    logger.info(f"   ⚠️  Skipped (expected): {query} - {e}")
            
            connection.commit()
            
            # Step 2: Create isolated test data - GREYSON PO 4755 only
            logger.info("📊 Step 2: Creating isolated test data (GREYSON PO 4755)...")
            create_test_data_query = """
            SELECT * INTO swp_ORDER_LIST_SYNC FROM ORDER_LIST
            WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
            """
            
            cursor.execute(create_test_data_query)
            test_records = cursor.rowcount
            logger.info(f"   ✅ Created test table: {test_records} records")
            
            # Add required columns for sync processing
            logger.info("🔧 Step 2b: Adding sync columns...")
            sync_columns = [
                "ALTER TABLE swp_ORDER_LIST_SYNC ADD sync_state VARCHAR(20) DEFAULT 'PENDING'",
                "ALTER TABLE swp_ORDER_LIST_SYNC ADD updated_at DATETIME2 DEFAULT GETUTCDATE()",
                "ALTER TABLE swp_ORDER_LIST_SYNC ADD group_name VARCHAR(100)",
                "ALTER TABLE swp_ORDER_LIST_SYNC ADD item_name VARCHAR(200)",
                "ALTER TABLE swp_ORDER_LIST_SYNC ADD group_id VARCHAR(50)",
                "UPDATE swp_ORDER_LIST_SYNC SET group_id = NULL, sync_state = 'PENDING'"
            ]
            
            for query in sync_columns:
                try:
                    cursor.execute(query)
                    logger.info(f"   ✅ Added: {query.split()[3] if 'ADD' in query else 'Updated sync_state'}")
                except Exception as e:
                    logger.info(f"   ⚠️  Column exists: {e}")
            
            connection.commit()
            
            # Step 3: Validate test data
            cursor.execute("SELECT COUNT(*) FROM swp_ORDER_LIST_SYNC")
            source_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM swp_ORDER_LIST_SYNC WHERE [CUSTOMER NAME] LIKE 'GREYSON%'")
            greyson_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Test data validation:")
            logger.info(f"   Total records: {source_count}")
            logger.info(f"   GREYSON records: {greyson_count}")
            logger.info(f"   Expected: 69 records")
            
            if source_count != 69:
                logger.warning(f"⚠️  Expected 69 records, got {source_count}")
            
            # Step 4: Initialize Enhanced Merge Orchestrator
            logger.info("🚀 Step 4: Running Enhanced Merge Orchestrator...")
            orchestrator = EnhancedMergeOrchestrator(config)
            
            # Execute the enhanced merge sequence 
            result = orchestrator.execute_enhanced_merge_sequence(dry_run=False)
            
            # Step 5: Results validation
            logger.info("📊 Step 5: Validating results...")
            
            cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST")
            target_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES")
            lines_count = cursor.fetchone()[0]
            
            logger.info(f"📈 Final results:")
            logger.info(f"   Source records processed: {source_count}")
            logger.info(f"   Target records created: {target_count}")
            logger.info(f"   Line records created: {lines_count}")
            
            # Overall result
            if result.get('success', False):
                logger.info("✅ ENHANCED MERGE ORCHESTRATOR - GREYSON TEST: PASSED")
                print("\n🎉 SUCCESS: Enhanced Merge Orchestrator working with isolated test data!")
            else:
                logger.error("❌ ENHANCED MERGE ORCHESTRATOR - GREYSON TEST: FAILED")
                logger.error(f"Error: {result.get('error', 'Unknown error')}")
                print("\n❌ FAILED: Check logs for details")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            print(f"\n❌ FAILED: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    main()
