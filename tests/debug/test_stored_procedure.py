#!/usr/bin/env python3
"""
Test Stored Procedure sp_get_matching_columns
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    """Test the stored procedure directly"""
    try:
        logger.info("🧪 Testing sp_get_matching_columns stored procedure...")
        
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Test stored procedure directly
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Execute stored procedure
            logger.info("🔧 Executing: EXEC sp_get_matching_columns 'swp_ORDER_LIST_SYNC', 'FACT_ORDER_LIST'")
            cursor.execute("EXEC sp_get_matching_columns 'swp_ORDER_LIST_SYNC', 'FACT_ORDER_LIST'")
            
            # Fetch results
            columns = cursor.fetchall()
            logger.info(f"📊 Found {len(columns)} matching columns")
            
            # Show first 10 results
            for i, (column_name, table1_ord, table2_ord) in enumerate(columns[:10]):
                logger.info(f"   {i+1}. {column_name} (T1:{table1_ord}, T2:{table2_ord})")
            
            # Check for transformation columns
            column_names = [col[0] for col in columns]
            transformation_columns = ['group_name', 'group_id', 'item_name']
            
            logger.info("🔍 Checking for transformation columns in stored procedure results:")
            for col in transformation_columns:
                is_present = col in column_names
                logger.info(f"   {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
            
            cursor.close()
        
        return len(columns) > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"🏁 Stored procedure test: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
