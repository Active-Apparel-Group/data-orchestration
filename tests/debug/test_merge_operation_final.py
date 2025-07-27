#!/usr/bin/env python3
"""
FINAL DIAGNOSTIC: Test Actual Merge Operation
Test the merge from swp_ORDER_LIST_SYNC to FACT_ORDER_LIST with group_name
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
    print("🔬 Final Diagnostic: Merge Operation Test...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Test 1: Check if both tables have group_name column
        print("\n📋 Test 1: Schema comparison between source and target...")
        
        try:
            # Check swp_ORDER_LIST_SYNC schema
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'swp_ORDER_LIST_SYNC' 
                AND COLUMN_NAME = 'group_name'
            """)
            source_schema = cursor.fetchall()
            
            # Check FACT_ORDER_LIST schema  
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'FACT_ORDER_LIST' 
                AND COLUMN_NAME = 'group_name'
            """)
            target_schema = cursor.fetchall()
            
            print(f"Source (swp_ORDER_LIST_SYNC) group_name: {source_schema}")
            print(f"Target (FACT_ORDER_LIST) group_name: {target_schema}")
            
            if source_schema and target_schema:
                print("✅ Both tables have group_name column")
            else:
                print("❌ Schema mismatch detected")
                
        except Exception as e:
            print(f"Error checking schemas: {str(e)}")
        
        # Test 2: Compare recent records between tables
        print("\n🔍 Test 2: Comparing recent records between source and target...")
        
        try:
            # Get recent record from source
            cursor.execute("""
                SELECT TOP 1
                    [AAG ORDER NUMBER],
                    [CUSTOMER NAME],
                    group_name,
                    sync_state,
                    'SOURCE' as table_origin
                FROM swp_ORDER_LIST_SYNC
                WHERE sync_state = 'NEW' AND group_name IS NOT NULL
                ORDER BY created_at DESC
            """)
            source_record = cursor.fetchone()
            
            if source_record:
                # Check if same record exists in target
                cursor.execute("""
                    SELECT TOP 1
                        [AAG ORDER NUMBER],
                        [CUSTOMER NAME], 
                        group_name,
                        sync_state,
                        'TARGET' as table_origin
                    FROM FACT_ORDER_LIST
                    WHERE [AAG ORDER NUMBER] = ?
                """, (source_record[0],))
                target_record = cursor.fetchone()
                
                print("Source record:")
                print(f"  Order: {source_record[0]} | Customer: {source_record[1]} | Group: {source_record[2]} | State: {source_record[3]}")
                
                if target_record:
                    print("Target record:")
                    print(f"  Order: {target_record[0]} | Customer: {target_record[1]} | Group: {target_record[2]} | State: {target_record[3]}")
                    
                    if source_record[2] == target_record[2]:
                        print("✅ Group names match between source and target")
                    else:
                        print("❌ Group name mismatch!")
                        print(f"    Source group_name: '{source_record[2]}'")
                        print(f"    Target group_name: '{target_record[2]}'")
                else:
                    print("❌ Record not found in target table - merge may not have occurred")
            else:
                print("❌ No NEW records found in source table")
                
        except Exception as e:
            print(f"Error comparing records: {str(e)}")
        
        # Test 3: Check business_columns configuration
        print("\n⚙️ Test 3: Business columns configuration...")
        try:
            business_columns = config.get_business_columns(use_dynamic_detection=False)
            print(f"Configured business_columns: {len(business_columns)} columns")
            
            if 'group_name' in business_columns:
                print("✅ group_name IS included in business_columns")
            else:
                print("❌ group_name NOT included in business_columns")
                print(f"Business columns: {business_columns}")
                
        except Exception as e:
            print(f"Error checking business_columns: {str(e)}")
        
        cursor.close()

if __name__ == "__main__":
    main()
