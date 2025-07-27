#!/usr/bin/env python3
"""
Diagnostic: Group Name Population Analysis
Investigate why all records are going into the same group
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
    print("🔍 Group Name Population Diagnostic...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Test 1: Check if group_name column exists in FACT_ORDER_LIST
        print("\n📋 Test 1: Checking FACT_ORDER_LIST schema for group_name column...")
        try:
            cursor.execute("""
                SELECT TOP 0 group_name 
                FROM FACT_ORDER_LIST
            """)
            print("✅ group_name column EXISTS in FACT_ORDER_LIST")
        except Exception as e:
            print(f"❌ group_name column MISSING from FACT_ORDER_LIST: {str(e)}")
        
        # Test 2: Check current customer distribution
        print("\n📊 Test 2: Current customer distribution in FACT_ORDER_LIST...")
        cursor.execute("""
            SELECT 
                [CUSTOMER NAME],
                COUNT(*) as record_count,
                MAX([AAG ORDER NUMBER]) as sample_order
            FROM FACT_ORDER_LIST
            WHERE sync_state = 'PENDING'
            GROUP BY [CUSTOMER NAME]
            ORDER BY record_count DESC
        """)
        
        customers = cursor.fetchall()
        print(f"Found {len(customers)} unique customers:")
        for customer in customers:
            print(f"  - {customer[0]}: {customer[1]} records (sample: {customer[2]})")
        
        # Test 3: Check if group_name field has any values
        print("\n🔍 Test 3: Checking for group_name values...")
        try:
            cursor.execute("""
                SELECT TOP 10
                    [AAG ORDER NUMBER],
                    [CUSTOMER NAME],
                    group_name,
                    sync_state
                FROM FACT_ORDER_LIST
                ORDER BY created_at DESC
            """)
            
            headers = cursor.fetchall()
            print("Recent headers with group_name values:")
            for header in headers:
                group_status = "✅ HAS GROUP" if header[2] else "❌ NO GROUP"
                print(f"  - Order: {header[0]} | Customer: {header[1]} | Group: {header[2]} | {group_status}")
                
        except Exception as e:
            print(f"❌ Cannot query group_name field: {str(e)}")
        
        # Test 4: Check Enhanced Merge Orchestrator output table schema
        print("\n🔧 Test 4: Enhanced Merge Orchestrator output verification...")
        try:
            # Check if there are any raw input tables with different schemas
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE '%ORDER_LIST%RAW%' 
                   OR TABLE_NAME LIKE '%HEADER%RAW%'
                ORDER BY TABLE_NAME
            """)
            
            raw_tables = cursor.fetchall()
            if raw_tables:
                print("Raw input tables found:")
                for table in raw_tables:
                    print(f"  - {table[0]}")
                    
                    # Check if raw table has group_name
                    try:
                        cursor.execute(f"SELECT TOP 0 group_name FROM [{table[0]}]")
                        print(f"    ✅ {table[0]} has group_name column")
                    except:
                        print(f"    ❌ {table[0]} missing group_name column")
            else:
                print("No raw input tables found")
                
        except Exception as e:
            print(f"Error checking raw tables: {str(e)}")
        
        cursor.close()

if __name__ == "__main__":
    main()
