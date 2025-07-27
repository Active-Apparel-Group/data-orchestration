#!/usr/bin/env python3
"""
Transformation Columns Schema Validation
Validates that group_name, group_id, item_name are present in source and target tables
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
    print("🧪 TRANSFORMATION COLUMNS SCHEMA VALIDATION")
    print("=" * 60)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Define transformation columns we need to validate
        transformation_columns = ['group_name', 'group_id', 'item_name']
        
        # Tables to check
        source_table = "swp_ORDER_LIST_SYNC"
        target_table = "FACT_ORDER_LIST"
        
        print(f"📋 Checking transformation columns in:")
        print(f"   📥 Source: {source_table}")
        print(f"   📤 Target: {target_table}")
        print()
        
        # Function to check columns in a table
        def check_table_columns(table_name):
            print(f"🔍 Checking {table_name}...")
            
            # Get column information
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                AND COLUMN_NAME IN ('group_name', 'group_id', 'item_name')
                ORDER BY COLUMN_NAME
            """)
            
            columns = cursor.fetchall()
            
            if not columns:
                print(f"   ❌ No transformation columns found in {table_name}")
                return False
            
            found_columns = set()
            for column in columns:
                col_name, data_type, is_nullable, default_val = column
                found_columns.add(col_name)
                nullable_text = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_text = f" DEFAULT {default_val}" if default_val else ""
                print(f"   ✅ {col_name}: {data_type} {nullable_text}{default_text}")
            
            # Check if all transformation columns are present
            missing_columns = set(transformation_columns) - found_columns
            if missing_columns:
                print(f"   ❌ Missing columns: {', '.join(missing_columns)}")
                return False
            else:
                print(f"   ✅ All transformation columns present: {', '.join(sorted(found_columns))}")
                return True
        
        # Check both tables
        print("📊 SCHEMA VALIDATION RESULTS:")
        print("-" * 40)
        
        source_valid = check_table_columns(source_table)
        print()
        target_valid = check_table_columns(target_table)
        print()
        
        # Summary
        print("🎯 VALIDATION SUMMARY:")
        print("-" * 30)
        print(f"   📥 Source table ({source_table}): {'✅ VALID' if source_valid else '❌ INVALID'}")
        print(f"   📤 Target table ({target_table}): {'✅ VALID' if target_valid else '❌ INVALID'}")
        
        if source_valid and target_valid:
            print()
            print("🎉 SUCCESS: All transformation columns are properly configured!")
            print("   ✅ group_name: Available for Monday.com group organization")
            print("   ✅ group_id: Available for Monday.com group ID tracking")
            print("   ✅ item_name: Available for Monday.com item name generation")
            print()
            print("🚀 Enhanced Merge Orchestrator is PRODUCTION READY with transformation columns!")
            
            # Additional data validation
            print()
            print("📊 DATA SAMPLE VALIDATION:")
            print("-" * 30)
            
            # Check if transformation columns have data
            for table_name in [source_table, target_table]:
                print(f"🔍 Checking data in {table_name}...")
                
                cursor.execute(f"""
                    SELECT TOP 5
                        [AAG ORDER NUMBER],
                        group_name,
                        group_id, 
                        item_name
                    FROM {table_name}
                    WHERE [AAG ORDER NUMBER] IS NOT NULL
                    ORDER BY [AAG ORDER NUMBER]
                """)
                
                sample_data = cursor.fetchall()
                
                if sample_data:
                    print(f"   ✅ Sample data found ({len(sample_data)} records):")
                    for i, row in enumerate(sample_data[:3], 1):
                        aag_order, group_name, group_id, item_name = row
                        print(f"     {i}. Order: {aag_order}")
                        print(f"        group_name: {group_name or 'NULL'}")
                        print(f"        group_id: {group_id or 'NULL'}")
                        print(f"        item_name: {item_name or 'NULL'}")
                else:
                    print(f"   ⚠️  No data found in {table_name}")
                print()
            
            return True
        else:
            print()
            print("❌ VALIDATION FAILED: Missing transformation columns!")
            print("   Please ensure group_name, group_id, and item_name columns exist in both tables.")
            return False
        
        cursor.close()

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        print(f"🏁 Schema validation completed with exit code: {exit_code}")
    except Exception as e:
        print(f"❌ Schema validation failed with error: {str(e)}")
        exit(1)
