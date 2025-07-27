#!/usr/bin/env python3
"""
Quick Color Column Diagnostic Test
==================================
Purpose: Simply check what color columns exist in the database
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🎨 SIMPLE COLOR COLUMN CHECK")
    print("=" * 50)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    print(f"📋 Source table: {config.source_table}")
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print(f"\n🔍 Checking color-related columns...")
        
        # Check for color-related columns
        color_query = f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{config.source_table}'
        AND (COLUMN_NAME LIKE '%COLOR%' OR COLUMN_NAME LIKE '%COLOUR%')
        ORDER BY COLUMN_NAME
        """
        
        try:
            cursor.execute(color_query)
            color_columns = [row[0] for row in cursor.fetchall()]
            
            print(f"   📊 Color-related columns found:")
            for col in color_columns:
                print(f"      • {col}")
            
            if not color_columns:
                print(f"   ⚠️ No color-related columns found!")
            
            # Check specific columns mentioned in TOML config
            print(f"\n🔍 Checking TOML-configured columns:")
            specific_checks = ['CUSTOMER STYLE', 'CUSTOMER COLOUR DESCRIPTION', 'AAG ORDER NUMBER']
            
            for col in specific_checks:
                check_query = f"""
                SELECT COUNT(*) as exists_count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{config.source_table}' AND COLUMN_NAME = '{col}'
                """
                cursor.execute(check_query)
                exists = cursor.fetchone()[0] > 0
                print(f"      {'✅' if exists else '❌'} {col}")
            
            print(f"\n✅ Color column diagnostic complete!")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        cursor.close()

if __name__ == "__main__":
    main()
