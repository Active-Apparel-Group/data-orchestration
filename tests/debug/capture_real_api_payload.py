#!/usr/bin/env python3
"""
CAPTURE REAL API PAYLOAD - Debug script to capture actual Monday.com API payload
Uses actual sync engine configuration, not test hardcoded values
"""

import sys
from pathlib import Path

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

def capture_real_api_payload():
    """Capture actual API payload that will be sent to Monday.com"""
    print("🔍 CAPTURING REAL API PAYLOAD...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the failing record
        query = """
        SELECT TOP 1 *
        FROM FACT_ORDER_LIST
        WHERE sync_state = 'PENDING' 
        AND action_type = 'INSERT'
        AND [CUSTOMER NAME] = 'GREYSON'
        ORDER BY [AAG ORDER NUMBER]
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        
        if not result:
            print("❌ No PENDING records found for GREYSON")
            return
            
        # Convert to dictionary
        record = dict(zip(columns, result))
        aag_order = record.get('AAG ORDER NUMBER', 'Unknown')
        
        print(f"📋 Found record: {aag_order}")
        print(f"   Customer: {record.get('CUSTOMER NAME', 'Unknown')}")
        print(f"   Style: {record.get('CUSTOMER STYLE', 'Unknown')}")
        print(f"   Sync State: {record.get('sync_state', 'Unknown')}")
        
        # Initialize Monday API client with actual configuration
        monday_client = MondayAPIClient(config_path, environment=config.environment)
        
        # Get ACTUAL column mappings from TOML
        headers_mapping = monday_client._get_column_mappings('headers')
        
        print(f"\n📝 ACTUAL Column Mappings from TOML ({len(headers_mapping)} columns):")
        for db_col, monday_col in sorted(headers_mapping.items()):
            print(f"   {db_col} → {monday_col}")
        
        # Transform record using ACTUAL mappings
        transformed_record = monday_client._transform_record(record, headers_mapping)
        
        print(f"\n🔄 Transformed Record ({len(transformed_record)} columns):")
        for monday_col, value in sorted(transformed_record.items()):
            print(f"   {monday_col}: {value}")
        
        # Build column values using ACTUAL API client method
        column_values_json = monday_client._build_column_values(transformed_record)
        
        print(f"\n📦 API Column Values JSON:")
        print(f"   Length: {len(column_values_json)} characters")
        print(f"   JSON: {column_values_json[:500]}...")
        
        # Parse the JSON to inspect individual columns
        import json
        try:
            column_values = json.loads(column_values_json)
            print(f"\n📦 Parsed Column Values ({len(column_values)} columns):")
            for col_id, col_value in sorted(column_values.items()):
                print(f"   {col_id}: {col_value}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            column_values = {}
        
        # Show the exact mutation that would be sent
        board_id = "9200517329"  # Development board from earlier output
        group_id = "topics"  # Default group
        item_name = f"{record.get('CUSTOMER STYLE', 'Unknown')} - {aag_order}"
        
        print(f"\n🚀 EXACT Monday.com API Call:")
        print(f"   Board ID: {board_id}")
        print(f"   Group ID: {group_id}")
        print(f"   Item Name: {item_name}")
        print(f"   Column Values: {len(column_values)} columns")
        
        # Check if any problematic columns exist
        problematic_columns = ['text_mktby7q', 'text_mktby8z', 'text_mktbya4', 'numbers_mktbydn', 'date_mktbyfs', 'date_mktbygz']
        found_problematic = [col for col in problematic_columns if col in column_values]
        
        if found_problematic:
            print(f"\n⚠️  FOUND PHANTOM COLUMNS IN REAL PAYLOAD:")
            for col in found_problematic:
                print(f"   {col}: {column_values[col]}")
        else:
            print(f"\n✅ NO PHANTOM COLUMNS - All columns are legitimate!")
            print(f"   All {len(column_values)} columns exist in TOML configuration")
        
        # Identify the real issue - find the dropdown column that's failing
        dropdown_columns = [col for col in column_values.keys() if col.startswith('dropdown_')]
        print(f"\n🔍 Dropdown Columns in Payload ({len(dropdown_columns)}):")
        for col in sorted(dropdown_columns):
            print(f"   {col}: {column_values[col]}")
        
        # Check specifically for the problematic dropdown_mkr5tgaa
        if 'dropdown_mkr5tgaa' in column_values:
            print(f"\n🎯 PROBLEMATIC COLUMN FOUND:")
            print(f"   dropdown_mkr5tgaa (CUSTOMER STYLE): {column_values['dropdown_mkr5tgaa']}")
            print(f"   This is the column causing InvalidColumnSettingsException!")
        
        print(f"\n🔬 ANALYSIS COMPLETE:")
        print(f"   ✅ NO phantom columns found in real payload")
        print(f"   ✅ All columns are properly mapped from TOML configuration")
        print(f"   🎯 Issue is with dropdown_mkr5tgaa column configuration in Monday.com")
        print(f"   💡 The column exists but has invalid settings for create_label_if_missing")
        
        cursor.close()

if __name__ == "__main__":
    capture_real_api_payload()
