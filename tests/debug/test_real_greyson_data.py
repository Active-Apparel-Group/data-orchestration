"""
Test Real GREYSON Data Processing
Purpose: Validate that real GREYSON data creates proper Monday.com items with all columns populated
Location: tests/debug/test_real_greyson_data.py
"""

import sys
from pathlib import Path
import pandas as pd
import json

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
import db_helper as db
from monday_api_adapter import MondayApiAdapter


def get_real_greyson_data():
    """Get real GREYSON data from database"""
    print("\n=== Fetching Real GREYSON Data ===")
    
    sql = """
    SELECT TOP 1
        [AAG ORDER NUMBER],
        [CUSTOMER NAME],
        [CUSTOMER STYLE], 
        [TOTAL QTY],
        [EX FACTORY DATE],
        [ORDER DATE PO RECEIVED],
        [PO NUMBER]
    FROM [dbo].[ORDERS_UNIFIED]
    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
    AND [AAG ORDER NUMBER] = 'GRE-00505'
    ORDER BY [ORDER DATE PO RECEIVED] DESC
    """
    
    try:
        with db.get_connection('dms') as conn:
            df = pd.read_sql(sql, conn)
            
        if len(df) > 0:
            print(f"✅ Found {len(df)} GREYSON record(s)")
            for col in df.columns:
                print(f"   {col}: {df.iloc[0][col]}")
            return df.iloc[0]
        else:
            print("❌ No GREYSON data found")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


def test_column_mapping(order_data):
    """Test how order data gets mapped to Monday.com columns"""
    print("\n=== Testing Column Mapping ===")
    
    try:
        adapter = MondayApiAdapter()
        
        # Test the column transformation
        column_values = adapter._transform_to_monday_columns(order_data)
        
        print("Column Mapping Result:")
        print(json.dumps(column_values, indent=2, default=str))
        
        return column_values
        
    except Exception as e:
        print(f"❌ Column mapping error: {e}")
        return {}


def test_board_groups():
    """Test getting board groups to see available seasons"""
    print("\n=== Available Board Groups (Seasons) ===")
    
    try:
        adapter = MondayApiAdapter()
        success, groups, error = adapter.monday_client.get_board_groups("9200517329")
        
        if success:
            print(f"Available groups for items:")
            for group in groups:
                print(f"   - {group.get('id')}: {group.get('title')}")
            
            # Look for GREYSON-specific groups
            greyson_groups = [g for g in groups if 'GREYSON' in g.get('title', '').upper()]
            print(f"\nGREYSON-specific groups:")
            for group in greyson_groups:
                print(f"   - {group.get('id')}: {group.get('title')}")
                
            return greyson_groups
        else:
            print(f"❌ Failed to get board groups: {error}")
            return []
            
    except Exception as e:
        print(f"❌ Board groups error: {e}")
        return []


def create_real_monday_item(order_data, greyson_groups):
    """Create a Monday.com item with real GREYSON data"""
    print("\n=== Creating Real Monday.com Item ===")
    
    try:
        adapter = MondayApiAdapter()
        
        # Add proper group for GREYSON data
        if greyson_groups:
            # Use the first GREYSON group found
            order_data['Group'] = greyson_groups[0]['id']
            print(f"Using GREYSON group: {greyson_groups[0]['title']} ({greyson_groups[0]['id']})")
        else:
            print("⚠️  No GREYSON groups found, using default")
        
        # Add UUID for tracking
        order_data['source_uuid'] = f"real_greyson_{order_data.get('AAG ORDER NUMBER', 'unknown')}"
        
        print(f"Creating item for:")
        print(f"   Customer: {order_data.get('CUSTOMER NAME')}")
        print(f"   AAG Order: {order_data.get('AAG ORDER NUMBER')}")
        print(f"   Style: {order_data.get('CUSTOMER STYLE')}")
        print(f"   Quantity: {order_data.get('TOTAL QTY')}")
        print(f"   Group: {order_data.get('Group')}")
        
        result = adapter.create_master_schedule_item(order_data)
        
        if result.get('success'):
            print(f"✅ Successfully created Monday.com item!")
            print(f"   Item ID: {result.get('monday_item_id')}")
            print(f"   Item Name: {result.get('item_name')}")
            print(f"   Customer: {result.get('customer')}")
            
            return result.get('monday_item_id')
        else:
            print(f"❌ Failed to create item: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ Item creation error: {e}")
        return None


def check_monday_board_manually():
    """Instructions for manual Monday.com board check"""
    print("\n=== Manual Monday.com Board Check Required ===")
    print("🔍 Please check the Monday.com board manually:")
    print("   1. Go to Monday.com board 9200517329")
    print("   2. Find the items we just created")
    print("   3. Check if these columns are populated:")
    print("      - Customer Name")
    print("      - Style")
    print("      - Quantity") 
    print("      - PO Number")
    print("      - Delivery Date")
    print("   4. Check if items are in correct seasonal group")
    print("   5. Check if subitems have size names and quantities")


def main():
    """Run comprehensive real data test"""
    print("🚀 Testing Real GREYSON Data Pipeline")
    print("=" * 60)
    
    # Step 1: Get real GREYSON data
    order_data = get_real_greyson_data()
    if not order_data:
        print("💥 Cannot continue without real data")
        return False
    
    # Step 2: Test column mapping
    column_values = test_column_mapping(order_data)
    
    # Step 3: Get available board groups
    greyson_groups = test_board_groups()
    
    # Step 4: Create real Monday.com item
    item_id = create_real_monday_item(order_data, greyson_groups)
    
    # Step 5: Manual check instructions
    check_monday_board_manually()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Real Data Test Summary")
    print("=" * 60)
    
    print(f"Real Data Retrieved: {'✅ YES' if order_data is not None else '❌ NO'}")
    print(f"Column Mapping: {'✅ SUCCESS' if column_values else '❌ FAILED'}")
    print(f"Board Groups: {'✅ SUCCESS' if greyson_groups else '❌ FAILED'}")
    print(f"Item Created: {'✅ SUCCESS' if item_id else '❌ FAILED'}")
    
    if item_id:
        print(f"\n🎯 Created Item ID: {item_id}")
        print("   👆 Check this item in Monday.com to validate column data!")
    
    success = all([order_data is not None, column_values, item_id])
    
    if success:
        print("\n✅ Test completed - Manual verification required")
    else:
        print("\n❌ Test failed - Check errors above")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
