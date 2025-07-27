#!/usr/bin/env python3
"""
Create O/S Label - Manual creation test
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
    print("🧪 Create O/S Label Test...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday API client with config PATH, not config object
    monday_client = MondayAPIClient(config_path)
    
    # Test create_labels_if_missing for O/S specifically
    column_id = "dropdown_mkrak7qp"
    label_value = "O/S"
    
    print(f"🎯 Testing create_labels_if_missing for column {column_id} with value '{label_value}'")
    
    try:
        # This should create the label if it doesn't exist
        result = monday_client.create_labels_if_missing(column_id, [label_value], board_id=config.subitems_board_id)
        print(f"✅ Label creation result: {result}")
        
        # Test the dropdown formatting
        dropdown_value = {"labels": [label_value]}
        print(f"🎯 Dropdown format test: {dropdown_value}")
        
    except Exception as e:
        print(f"❌ Error creating O/S label: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
