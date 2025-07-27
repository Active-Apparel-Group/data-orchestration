"""
Quick Test: Universal Monday.com Update Script
Purpose: Validate the universal update script functionality
Author: CTO / Head Data Engineer
Date: 2025-06-30

Tests:
1. Script initialization
2. Configuration loading
3. GraphQL template loading
4. Board metadata loading
5. Dry run validation
"""

import sys
import os
from pathlib import Path
import json

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "scripts"))

import logger_helper

def test_universal_update_script():
    """Test the universal Monday.com update script"""
    logger = logger_helper.get_logger(__name__)
    
    print("=== UNIVERSAL MONDAY UPDATE SCRIPT TEST ===")
    print()
    
    # Test 1: Import and initialize
    print("1. Testing script import and initialization...")
    try:
        from universal_monday_update import UniversalMondayUpdater
        updater = UniversalMondayUpdater()
        print("   SUCCESS: Script imported and initialized")
    except Exception as e:
        print(f"   ERROR: Failed to import/initialize: {e}")
        return False
    
    # Test 2: Test GraphQL template loading
    print("\n2. Testing GraphQL template loading...")
    try:
        update_item_query = updater.load_graphql_template("update_item")
        update_subitem_query = updater.load_graphql_template("update_subitem")
        print("   SUCCESS: GraphQL templates loaded")
        print(f"   - update_item template: {len(update_item_query)} characters")
        print(f"   - update_subitem template: {len(update_subitem_query)} characters")
    except Exception as e:
        print(f"   ERROR: Failed to load GraphQL templates: {e}")
        return False
    
    # Test 3: Test board metadata loading
    print("\n3. Testing board metadata loading...")
    try:
        metadata = updater.load_board_metadata(8709134353)
        print("   SUCCESS: Board metadata loaded")
        print(f"   - Board name: {metadata.get('name', 'Unknown')}")
        print(f"   - Columns count: {len(metadata.get('columns', []))}")
    except Exception as e:
        print(f"   ERROR: Failed to load board metadata: {e}")
        return False
    
    # Test 4: Test TOML configuration loading
    print("\n4. Testing TOML configuration loading...")
    try:
        config_path = repo_root / "configs" / "updates" / "customer_master_schedule_items.toml"
        updater_with_config = UniversalMondayUpdater(str(config_path))
        print("   SUCCESS: TOML configuration loaded")
        print(f"   - Board ID: {updater_with_config.update_config.get('metadata', {}).get('board_id', 'Unknown')}")
        print(f"   - Update type: {updater_with_config.update_config.get('metadata', {}).get('update_type', 'Unknown')}")
    except Exception as e:
        print(f"   ERROR: Failed to load TOML configuration: {e}")
        return False
    
    # Test 5: Test dry run item update
    print("\n5. Testing dry run item update...")
    try:
        result = updater.update_item(
            board_id=8709134353,
            item_id=123456,  # Fake ID for testing
            column_updates={"status": "Testing", "quantity": "100"},
            dry_run=True
        )
        
        if result['success'] and result['dry_run']:
            print("   SUCCESS: Dry run item update")
            print(f"   - Result: {result['message']}")
        else:
            print(f"   ERROR: Dry run failed: {result}")
            return False
    except Exception as e:
        print(f"   ERROR: Dry run item update failed: {e}")
        return False
    
    # Test 6: Test dry run subitem update  
    print("\n6. Testing dry run subitem update...")
    try:
        result = updater.update_subitem(
            board_id=8709134353,
            item_id=123456,  # Fake ID for testing
            subitem_id=789012,  # Fake ID for testing
            column_updates={"size": "XL", "quantity": "25"},
            dry_run=True
        )
        
        if result['success'] and result['dry_run']:
            print("   SUCCESS: Dry run subitem update")
            print(f"   - Result: {result['message']}")
        else:
            print(f"   ERROR: Dry run failed: {result}")
            return False
    except Exception as e:
        print(f"   ERROR: Dry run subitem update failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print()
    print("The Universal Monday.com Update Script is ready for deployment!")
    print()
    print("Next steps:")
    print("1. Run 'OPUS: Universal Monday Update (Dry Run)' VS Code task")
    print("2. Test with actual Monday.com IDs from staging data")
    print("3. Execute live updates when validated")
    
    return True

if __name__ == "__main__":
    success = test_universal_update_script()
    sys.exit(0 if success else 1)
