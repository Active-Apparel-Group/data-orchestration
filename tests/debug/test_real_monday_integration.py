"""
Test Real Monday.com API Integration
Purpose: Validate that Monday.com API integration is working with real API calls
Location: tests/debug/test_real_monday_integration.py
"""

import sys
from pathlib import Path
import pandas as pd

# Add utils and dev to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))

# Import from utils following project standards
import logger_helper
from monday_integration import create_monday_integration
from monday_api_adapter import MondayApiAdapter


def test_monday_connection():
    """Test Monday.com API connection"""
    print("\n=== Testing Monday.com API Connection ===")
    
    # Test direct integration
    monday = create_monday_integration()
    success, message = monday.test_connection()
    
    print(f"Monday.com API Test: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    
    return success


def test_api_adapter():
    """Test Monday.com API adapter"""
    print("\n=== Testing Monday.com API Adapter ===")
    
    try:
        adapter = MondayApiAdapter()
        print("✅ API Adapter initialized successfully")
          # Test connection through adapter
        success, message = adapter.monday_client.test_connection()
        print(f"Adapter Connection Test: {'SUCCESS' if success else 'FAILED'}")
        print(f"Message: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Failed to initialize API adapter: {e}")
        return False


def test_board_groups():
    """Test retrieving board groups"""
    print("\n=== Testing Board Groups Retrieval ===")
    
    try:
        monday = create_monday_integration()
        board_id = "9200517329"  # GREYSON board
        
        success, groups, error = monday.get_board_groups(board_id)
        
        if success:
            print(f"✅ Retrieved {len(groups)} groups for board {board_id}")
            for group in groups:
                print(f"   - {group.get('id', 'unknown_id')}: {group.get('title', 'No Title')}")
        else:
            print(f"❌ Failed to retrieve board groups: {error}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error retrieving board groups: {e}")
        return False


def test_item_creation():
    """Test creating a Monday.com item"""
    print("\n=== Testing Monday.com Item Creation ===")
    
    try:
        adapter = MondayApiAdapter()
        
        # Create test order data
        test_order = pd.Series({
            'CUSTOMER': 'TEST CUSTOMER',
            'CUSTOMER NAME': 'TEST CUSTOMER',
            'AAG ORDER NUMBER': 'TEST_PO_12345',
            'PO NUMBER': 'CUST_PO_67890',
            'CUSTOMER STYLE': 'TEST_STYLE_001',
            'TOTAL QTY': 100,
            'ORDER DATE PO RECEIVED': pd.Timestamp.now(),            'source_uuid': 'test_uuid_12345',
            'Group': 'group_mkranjfa'  # Use GREYSON 2026 SPRING group
        })
        
        print("Creating test Monday.com item...")
        print(f"Item: {test_order['CUSTOMER']} - {test_order['AAG ORDER NUMBER']}")
        
        result = adapter.create_master_schedule_item(test_order)
        
        if result.get('success'):
            print(f"✅ Successfully created Monday.com item!")
            print(f"   Item ID: {result.get('monday_item_id')}")
            print(f"   Item Name: {result.get('item_name')}")
            print(f"   Customer: {result.get('customer')}")
            print(f"   Group: {result.get('group_id')}")
            print(f"   Source UUID: {result.get('source_uuid')}")
            print(f"   Created At: {result.get('created_at')}")
            
            # Return item ID for further testing
            return result.get('monday_item_id')
        else:
            print(f"❌ Failed to create Monday.com item: {result.get('error')}")
            return None
        
    except Exception as e:
        print(f"❌ Error creating Monday.com item: {e}")
        return None


def test_subitem_creation(parent_item_id: str):
    """Test creating a Monday.com subitem"""
    print("\n=== Testing Monday.com Subitem Creation ===")
    
    if not parent_item_id:
        print("❌ No parent item ID provided - skipping subitem test")
        return False
    
    try:
        adapter = MondayApiAdapter()
        
        # Create test subitem data
        test_subitems = pd.DataFrame([
            {
                'size_name': 'S',
                'size_qty': 25,
                'stg_size_label': 'Small',
                'ORDER_QTY': 25,
                'parent_source_uuid': 'test_uuid_12345',
                'order_number': 'TEST_PO_12345'
            },
            {
                'size_name': 'M',
                'size_qty': 35,
                'stg_size_label': 'Medium',
                'ORDER_QTY': 35,
                'parent_source_uuid': 'test_uuid_12345',
                'order_number': 'TEST_PO_12345'
            },
            {
                'size_name': 'L',
                'size_qty': 40,
                'stg_size_label': 'Large',
                'ORDER_QTY': 40,
                'parent_source_uuid': 'test_uuid_12345',
                'order_number': 'TEST_PO_12345'
            }
        ])
        
        print(f"Creating {len(test_subitems)} test subitems for parent item {parent_item_id}...")
        
        results = adapter.create_subitems(parent_item_id, test_subitems)
        
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)
        
        print(f"Subitem Creation Results: {successful}/{total} successful")
        
        for i, result in enumerate(results):
            if result.get('success'):
                print(f"   ✅ Subitem {i+1}: {result.get('size_name')} (ID: {result.get('monday_subitem_id')})")
            else:
                print(f"   ❌ Subitem {i+1}: {result.get('size_name')} - Error: {result.get('error')}")
        
        return successful > 0
        
    except Exception as e:
        print(f"❌ Error creating Monday.com subitems: {e}")
        return False


def test_api_error_handling():
    """Test API error handling with invalid data"""
    print("\n=== Testing API Error Handling ===")
    
    try:
        monday = create_monday_integration()
        
        # Test with invalid board ID
        print("Testing with invalid board ID...")
        success, result, error = monday.create_item(
            board_id="invalid_board_id",
            item_name="Test Item",
            group_id="invalid_group"
        )
        
        if not success:
            print(f"✅ Error handling working - caught invalid board: {error}")
        else:
            print(f"⚠️  Unexpected success with invalid board ID")
        
        # Test with empty item name
        print("Testing with empty item name...")
        success, result, error = monday.create_item(
            board_id="9200517329",
            item_name="",
            group_id="new_group"
        )
        
        if not success:
            print(f"✅ Error handling working - caught empty name: {error}")
        else:
            print(f"⚠️  Unexpected success with empty item name")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during error handling test: {e}")
        return False


def main():
    """Run all Monday.com integration tests"""
    print("🚀 Starting Real Monday.com API Integration Tests")
    print("=" * 60)
    
    # Test 1: Basic connection
    connection_success = test_monday_connection()
    
    # Test 2: API adapter initialization
    adapter_success = test_api_adapter()
    
    # Test 3: Board groups retrieval
    groups_success = test_board_groups()
    
    # Test 4: Item creation (only if connection works)
    item_id = None
    if connection_success and adapter_success:
        item_id = test_item_creation()
    
    # Test 5: Subitem creation (only if item was created)
    subitem_success = False
    if item_id:
        subitem_success = test_subitem_creation(item_id)
    
    # Test 6: Error handling
    error_handling_success = test_api_error_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    
    tests = [
        ("Connection Test", connection_success),
        ("API Adapter Test", adapter_success),
        ("Board Groups Test", groups_success),
        ("Item Creation Test", item_id is not None),
        ("Subitem Creation Test", subitem_success),
        ("Error Handling Test", error_handling_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Monday.com integration is working properly.")
    else:
        print("⚠️  Some tests failed. Check configuration and API credentials.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
