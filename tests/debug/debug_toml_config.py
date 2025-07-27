#!/usr/bin/env python3
"""
Debug TOML configuration parsing for create_labels_if_missing
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

def main():
    print("🔍 Debug TOML Configuration Parsing...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Monday API Client
        monday_client = MondayAPIClient(config_path)
        
        print(f"🎯 Environment: {monday_client._get_environment()}")
        
        # Test the _get_dropdown_config method directly
        print("\n📋 Testing _get_dropdown_config for 'lines':")
        dropdown_config, default = monday_client._get_dropdown_config('lines')
        print(f"   Default: {default}")
        print(f"   Config: {dropdown_config}")
        
        # Check specific column
        target_column = "dropdown_mkrak7qp"
        if target_column in dropdown_config:
            print(f"✅ Found {target_column}: {dropdown_config[target_column]}")
        else:
            print(f"❌ {target_column} not found in config")
        
        # Test with our actual record
        test_record = {
            'dropdown_mkrak7qp': 'O/S',
            'numeric_mkra7j8e': 2,
            'name': 'Size O/S'
        }
        
        print(f"\n🧪 Testing _determine_create_labels_for_records with: {test_record}")
        result = monday_client._determine_create_labels_for_records([test_record], 'lines')
        print(f"   Result: {result}")
        
        # Let's also check the TOML config directly
        print(f"\n📄 Direct TOML access:")
        toml_path = ['monday', 'development', 'lines', 'create_labels_if_missing']
        config_section = monday_client.toml_config
        for i, key in enumerate(toml_path):
            print(f"   Step {i+1}: {key}")
            if key in config_section:
                config_section = config_section.get(key, {})
                print(f"     ✅ Found: {type(config_section).__name__}")
                if isinstance(config_section, dict):
                    print(f"     Content: {config_section}")
            else:
                print(f"     ❌ Key '{key}' not found! Available: {list(config_section.keys()) if isinstance(config_section, dict) else 'Not a dict'}")
                break
        
        cursor.close()

if __name__ == "__main__":
    main()
