#!/usr/bin/env python3
"""
Setup GREYSON PO 4755 data for Enhanced Merge Orchestrator testing
=================================================================
Purpose: Set up swp_ORDER_LIST_SYNC with GREYSON data before running E2E tests
Pattern: EXACT pattern from imports.guidance.instructions.md - PROVEN WORKING PATTERN
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    """Setup GREYSON PO 4755 data in swp_ORDER_LIST_SYNC for testing"""
    try:
        logger.info("🧪 Setting up GREYSON PO 4755 data for Enhanced Merge Orchestrator testing...")
        
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Database connection using config.db_key
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Step 1: Check current state
            logger.info("📊 Checking current table states...")
            
            # Check ORDER_LIST for GREYSON data
            cursor.execute("""
                SELECT COUNT(*) FROM ORDER_LIST 
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
            """)
            order_list_count = cursor.fetchone()[0]
            logger.info(f"   ORDER_LIST GREYSON records: {order_list_count}")
            
            # Check swp_ORDER_LIST_SYNC current state
            cursor.execute(f"SELECT COUNT(*) FROM {config.source_table}")
            source_count = cursor.fetchone()[0]
            logger.info(f"   {config.source_table} total records: {source_count}")
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM {config.source_table}
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
            """)
            source_greyson_count = cursor.fetchone()[0]
            logger.info(f"   {config.source_table} GREYSON records: {source_greyson_count}")
            
            # Step 2: Setup data if needed
            if order_list_count > 0 and source_greyson_count == 0:
                logger.info("🔧 Setting up GREYSON data in swp_ORDER_LIST_SYNC...")
                
                # Insert GREYSON data into swp_ORDER_LIST_SYNC
                setup_query = f"""
                INSERT INTO {config.source_table}
                SELECT * FROM ORDER_LIST
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
                """
                
                cursor.execute(setup_query)
                connection.commit()
                
                # Verify setup
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {config.source_table}
                    WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
                """)
                final_count = cursor.fetchone()[0]
                logger.info(f"   ✅ GREYSON data setup complete: {final_count} records inserted")
                
            elif source_greyson_count > 0:
                logger.info(f"   ✅ GREYSON data already exists: {source_greyson_count} records")
                
            else:
                logger.warning("   ⚠️ No GREYSON data found in ORDER_LIST source table")
            
            # Step 3: Reset group_id for testing
            logger.info("🔧 Resetting group_id for testing...")
            cursor.execute(f"""
                UPDATE {config.source_table} 
                SET group_id = NULL 
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
            """)
            connection.commit()
            logger.info("   ✅ group_id reset complete")
            
            # Step 4: Final validation
            logger.info("✅ Final validation...")
            cursor.execute(f"""
                SELECT 
                    [CUSTOMER NAME],
                    [PO NUMBER],
                    COUNT(*) as record_count
                FROM {config.source_table}
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755'
                GROUP BY [CUSTOMER NAME], [PO NUMBER]
            """)
            
            results = cursor.fetchall()
            for row in results:
                logger.info(f"   Customer: {row[0]}, PO: {row[1]}, Records: {row[2]}")
            
            cursor.close()
        
        logger.info("🎯 GREYSON data setup complete! Ready for Enhanced Merge Orchestrator testing.")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    logger.info(f"🏁 GREYSON data setup completed with exit code: {exit_code}")
    sys.exit(exit_code)
