#!/usr/bin/env python3
"""
Simple Column Check - Identify Available Columns
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    """Check available columns in target table"""
    logger.info("🔍 CHECKING AVAILABLE COLUMNS...")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get all columns
        table_name = config.target_table.split('.')[-1] if '.' in config.target_table else config.target_table
        cursor.execute(f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY COLUMN_NAME
        """)
        
        all_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"Total columns in {table_name}: {len(all_columns)}")
        
        # Check for season-related columns
        season_columns = [col for col in all_columns if 'SEASON' in col.upper()]
        logger.info(f"Season columns: {season_columns}")
        
        # Check for customer-related columns
        customer_columns = [col for col in all_columns if 'CUSTOMER' in col.upper()]
        logger.info(f"Customer columns: {customer_columns}")
        
        # Check transformation columns from config
        logger.info("\n📋 CHECKING TOML CONFIGURATION COLUMNS:")
        logger.info(f"Group transformation primary: {config.config_dict.get('database', {}).get('group_name_transformation', {}).get('primary_columns', [])}")
        logger.info(f"Group transformation fallback: {config.config_dict.get('database', {}).get('group_name_transformation', {}).get('fallback_columns', [])}")
        logger.info(f"Item transformation columns: {config.config_dict.get('database', {}).get('item_name_transformation', {}).get('columns', [])}")
        
        cursor.close()

if __name__ == "__main__":
    main()
