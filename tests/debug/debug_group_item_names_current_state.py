#!/usr/bin/env python3
"""
DEBUG: Group and Item Names Current State Analysis
Purpose: Check current state of group_name and item_name transformations
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    """Analyze current group_name and item_name state in FACT_ORDER_LIST"""
    logger.info("🔍 ANALYZING GROUP_NAME AND ITEM_NAME CURRENT STATE...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check group_name values
        logger.info("📊 CHECKING GROUP_NAME VALUES:")
        cursor.execute("""
        SELECT DISTINCT 
            [CUSTOMER NAME],
            [SEASON],
            [group_name],
            COUNT(*) as record_count
        FROM [FACT_ORDER_LIST]
        WHERE [CUSTOMER NAME] = 'GREYSON'
        GROUP BY [CUSTOMER NAME], [SEASON], [group_name]
        ORDER BY [group_name], [SEASON]
        """)
        
        group_results = cursor.fetchall()
        for row in group_results:
            customer, season, group_name, count = row
            logger.info(f"  Customer: '{customer}', Season: '{season}' → group_name: '{group_name}' ({count} records)")
        
        # Check item_name values
        logger.info("📊 CHECKING ITEM_NAME VALUES:")
        cursor.execute("""
        SELECT DISTINCT 
            [CUSTOMER STYLE],
            [COLOR],
            [AAG ORDER NUMBER],
            [item_name],
            COUNT(*) as record_count
        FROM [FACT_ORDER_LIST]
        WHERE [CUSTOMER NAME] = 'GREYSON'
          AND [AAG ORDER NUMBER] IN ('POG4755', 'PO4755', 'G4755')
        GROUP BY [CUSTOMER STYLE], [COLOR], [AAG ORDER NUMBER], [item_name]
        ORDER BY [AAG ORDER NUMBER], [CUSTOMER STYLE]
        """)
        
        item_results = cursor.fetchall()
        for row in item_results:
            style, color, order_num, item_name, count = row
            logger.info(f"  Style: '{style}', Color: '{color}', Order: '{order_num}' → item_name: '{item_name}' ({count} records)")
        
        # Check if transformations are enabled
        logger.info("⚙️ CHECKING TRANSFORMATION CONFIGURATION:")
        try:
            from src.pipelines.sync_order_list.merge_orchestrator import EnhancedMergeOrchestrator
            orchestrator = EnhancedMergeOrchestrator(config)
            
            group_enabled = orchestrator._is_group_transformation_enabled()
            item_enabled = orchestrator._is_item_transformation_enabled()
            
            logger.info(f"  Group name transformation enabled: {group_enabled}")
            logger.info(f"  Item name transformation enabled: {item_enabled}")
            
        except Exception as e:
            logger.error(f"Failed to check transformation config: {e}")
        
        cursor.close()
    
    logger.info("✅ Group and item name state analysis completed")

if __name__ == "__main__":
    main()
