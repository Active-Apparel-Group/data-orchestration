#!/usr/bin/env python3
"""
Test Data Cleanup - Enhanced Merge Orchestrator
===============================================
Purpose: Reset test data for clean Enhanced Merge Orchestrator test runs
Created: 2025-07-28 (Following memory bank instructions)

This tool resets all test data related to GREYSON PO 4755 records
to ensure clean state for Enhanced Merge Orchestrator testing.
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
    """Reset all test data for clean Enhanced Merge Orchestrator test run"""
    logger.info("🧹 CLEANING UP TEST DATA FOR ENHANCED MERGE ORCHESTRATOR...")
    logger.info("=" * 80)
    
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        # Reset source table group fields
        logger.info("📋 Resetting swp_ORDER_LIST_SYNC group fields...")
        cursor.execute("UPDATE swp_ORDER_LIST_SYNC SET group_id = NULL, group_name = NULL")
        logger.info("✅ Reset swp_ORDER_LIST_SYNC group fields")
        
        # Reset target table group_id
        logger.info("📋 Resetting FACT_ORDER_LIST group_id for GREYSON PO 4755...")
        cursor.execute("""
            UPDATE FACT_ORDER_LIST 
            SET group_id = NULL 
            WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'
        """)
        affected = cursor.rowcount
        logger.info(f"✅ Reset {affected} FACT_ORDER_LIST group_id fields")
        
        # Reset sync states and Monday.com IDs
        logger.info("📋 Resetting FACT_ORDER_LIST sync states and Monday.com IDs...")
        cursor.execute("""
            UPDATE FACT_ORDER_LIST 
            SET sync_state = 'PENDING', monday_item_id = NULL 
            WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'
        """)
        affected = cursor.rowcount
        logger.info(f"✅ Reset {affected} FACT_ORDER_LIST sync states")
        
        # Reset ORDER_LIST_LINES subitem IDs
        logger.info("📋 Resetting ORDER_LIST_LINES subitem IDs...")
        cursor.execute("""
            UPDATE ORDER_LIST_LINES 
            SET monday_subitem_id = NULL 
            WHERE record_uuid IN (
                SELECT record_uuid 
                FROM FACT_ORDER_LIST 
                WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'
            )
        """)
        affected = cursor.rowcount
        logger.info(f"✅ Reset {affected} ORDER_LIST_LINES subitem IDs")
        
        # Clean up duplicate groups from MON_Boards_Groups if any
        logger.info("📋 Checking for duplicate groups in MON_Boards_Groups...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM MON_Boards_Groups 
            WHERE group_name = 'GREYSON 2025 FALL'
        """)
        group_count = cursor.fetchone()[0]
        
        if group_count > 1:
            logger.warning(f"⚠️  Found {group_count} duplicate groups, keeping only the first one")
            cursor.execute("""
                DELETE FROM MON_Boards_Groups 
                WHERE group_name = 'GREYSON 2025 FALL' 
                AND group_id NOT IN (
                    SELECT TOP 1 group_id 
                    FROM MON_Boards_Groups 
                    WHERE group_name = 'GREYSON 2025 FALL'
                )
            """)
            affected = cursor.rowcount
            logger.info(f"✅ Removed {affected} duplicate group entries")
        else:
            logger.info(f"✅ Group tracking clean: {group_count} entries found")
        
        connection.commit()
        cursor.close()
    
    logger.info("=" * 80)
    logger.info("✅ TEST DATA CLEANUP COMPLETE - READY FOR CLEAN TEST RUN!")
    logger.info("🎯 Next: Run Enhanced Merge Orchestrator with string group ID fix")

if __name__ == "__main__":
    main()
