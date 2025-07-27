#!/usr/bin/env python3
"""
Debug Size Label Creation - Test O/S vs OS handling
=================================================
Verify that TOML configuration 'create_labels_if_missing = true' is respected
for size dropdown (dropdown_mkrak7qp) in development environment
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

def main():
    print("🔍 DEBUGGING SIZE LABEL CREATION (O/S vs OS)")
    print("=" * 60)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    print("\n1. CHECKING TOML CONFIGURATION")
    print("-" * 40)
    
    # Initialize Monday API client to check configuration
    monday_client = MondayAPIClient(config_path)
    
    # Check the exact TOML setting for size dropdown
    toml_config = monday_client.toml_config
    size_dropdown_setting = (toml_config.get('monday', {})
                            .get('development', {})
                            .get('lines', {})
                            .get('create_labels_if_missing', {})
                            .get('dropdown_mkrak7qp'))
    
    print(f"🔍 TOML Setting for dropdown_mkrak7qp (size_code): {size_dropdown_setting}")
    print(f"   Expected: true (to auto-create 'O/S' labels)")
    print(f"   Actual: {size_dropdown_setting}")
    
    if size_dropdown_setting is True:
        print("   ✅ Configuration is CORRECT - should create 'O/S' labels")
    else:
        print("   ❌ Configuration is WRONG - will NOT create 'O/S' labels")
    
    print("\n2. TESTING API CLIENT LOGIC")
    print("-" * 40)
    
    # Test the API client's label creation logic
    test_records = [
        {'size_code': 'O/S', 'qty': 10},
        {'size_code': 'OS', 'qty': 5},
        {'size_code': 'XS', 'qty': 3}
    ]
    
    should_create_labels = monday_client._determine_create_labels_for_records(test_records, 'lines')
    print(f"🔍 API Client _determine_create_labels_for_records: {should_create_labels}")
    
    # Test specific column check
    for record in test_records:
        size_value = record['size_code']
        column_should_create = monday_client._should_create_labels_for_column('dropdown_mkrak7qp', 'lines')
        print(f"   Size '{size_value}': create_labels_if_missing = {column_should_create}")
    
    print("\n3. DATABASE SIZE DATA ANALYSIS")
    print("-" * 40)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Query actual size data
        query = f"""
        SELECT DISTINCT 
            size_code,
            sync_state,
            sync_error_message,
            COUNT(*) as frequency
        FROM {config.lines_table}
        WHERE size_code IS NOT NULL
          AND (size_code LIKE '%O%' OR size_code IN ('OS', 'O/S'))
        GROUP BY size_code, sync_state, sync_error_message
        ORDER BY frequency DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("🔍 Current Size Data in Database:")
        for row in results:
            size_code, sync_state, error_msg, frequency = row
            status = "❌ ERROR" if error_msg else ("✅ SYNCED" if sync_state == 'SYNCED' else "⚠️ PENDING")
            print(f"   '{size_code}': {sync_state} {status} (freq: {frequency})")
            if error_msg:
                print(f"      Error: {error_msg[:100]}...")
        
        cursor.close()
    
    print("\n4. RECOMMENDATIONS")
    print("-" * 40)
    
    if size_dropdown_setting is True:
        print("✅ TOML Configuration is correct")
        print("💡 If 'O/S' labels are still failing:")
        print("   1. Check Monday.com board permissions")
        print("   2. Verify API client is using correct environment (development)")
        print("   3. Check if 'O/S' vs 'OS' causes Monday.com validation issues")
        print("   4. Ensure API requests include create_labels_if_missing=true parameter")
    else:
        print("❌ TOML Configuration needs to be fixed")
        print("💡 Set dropdown_mkrak7qp = true in [monday.development.lines.create_labels_if_missing]")

if __name__ == "__main__":
    main()
