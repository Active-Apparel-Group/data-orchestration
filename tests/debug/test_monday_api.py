"""
Debug script to test actual Monday.com API call with real data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from customer_master_schedule.order_mapping import (
    load_mapping_config, 
    load_customer_mapping, 
    transform_order_data,
    get_monday_column_values_dict
)
from customer_master_schedule.order_sync import monday_api_call, BOARD_ID
import pandas as pd
import json
import requests

def test_monday_api_call():
    """Test actual Monday.com API call with debug logging"""
    
    print("=" * 60)
    print("DEBUG: Monday.com API Call Testing")
    print("=" * 60)
    
    # Load configurations
    print("\n1. Loading configurations...")
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    # Create sample order data
    print("\n2. Creating sample order data...")
    sample_order = pd.Series({
        'AAG ORDER NUMBER': 'DEBUG-TEST-001',
        'CUSTOMER NAME': 'MACK WELDON',
        'CUSTOMER STYLE': 'TEST-STYLE',
        'CUSTOMER COLOUR DESCRIPTION': 'DEBUG COLOR',
        'STYLE DESCRIPTION': 'DEBUG STYLE DESCRIPTION',
        'CUSTOMER SEASON': 'SPRING SUMMER 2026',
        'ORDER DATE PO RECEIVED': '2025-06-16',
        'PO NUMBER': 'DEBUG-PO-001',
        'CUSTOMER PRICE': '25.00',
        'CATEGORY': 'MENS',
        'ORDER TYPE': 'ACTIVE',
        'EX FACTORY DATE': '2025-09-26'
    })
    
    # Transform and get column values
    print("\n3. Transforming and generating column values...")
    transformed = transform_order_data(sample_order, mapping_config, customer_lookup)
    column_values = get_monday_column_values_dict(transformed)
    
    print(f"Column values to send: {len(column_values)} fields")
    
    # Create a test group first
    print("\n4. Creating test group...")
    group_name = "DEBUG TEST GROUP"
    
    group_query = f"""
    mutation {{
        create_group(
            board_id: {BOARD_ID},
            group_name: "{group_name}"
        ) {{
            id
        }}
    }}
    """
    
    try:
        group_result = monday_api_call(group_query)
        group_id = group_result['data']['create_group']['id']
        print(f"✅ Test group created: {group_id}")
    except Exception as e:
        print(f"❌ Group creation failed: {e}")
        # Try to get existing groups and use the first one
        groups_query = f"""
        query {{
            boards(ids: [{BOARD_ID}]) {{
                groups {{
                    id
                    title
                }}
            }}
        }}
        """
        groups_result = monday_api_call(groups_query)
        groups = groups_result['data']['boards'][0]['groups']
        if groups:
            group_id = groups[0]['id']
            print(f"✅ Using existing group: {group_id}")
        else:
            print("❌ No groups available")
            return
    
    # Create the test item with detailed API response
    print("\n5. Creating test item with full API response...")
    item_name = "DEBUG TEST ITEM"
    
    # Sanitize item name
    sanitized_name = item_name.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
    
    # Convert column values to JSON string properly
    column_values_json = json.dumps(column_values)
    
    # Build the mutation
    mutation = f"""
    mutation {{
        create_item(
            board_id: {BOARD_ID},
            group_id: "{group_id}",
            item_name: "{sanitized_name}",
            column_values: {json.dumps(column_values_json)},
            create_labels_if_missing: true
        ) {{
            id
            name
            column_values {{
                id
                text
                value
            }}
        }}
    }}
    """
    
    print("GraphQL Mutation:")
    print("-" * 40)
    print(mutation)
    print("-" * 40)
    
    try:
        print("\n6. Making API call...")
        result = monday_api_call(mutation)
        
        print("✅ API call successful!")
        print(f"Item ID: {result['data']['create_item']['id']}")
        print(f"Item Name: {result['data']['create_item']['name']}")
          # Analyze which columns were actually set
        print("\n7. Analyzing set columns...")
        column_values_returned = result['data']['create_item'].get('column_values', [])
        
        print(f"Monday.com returned {len(column_values_returned)} column values:")
        
        set_columns = 0
        empty_columns = 0
        
        for col in column_values_returned:
            col_id = col.get('id', '')
            col_text = col.get('text', '') or ''
            col_value = col.get('value')
            
            if col_text and col_text.strip():
                set_columns += 1
                if set_columns <= 15:  # Show first 15 set columns
                    print(f"✅ {col_id}: '{col_text}'")
            else:
                empty_columns += 1
                if empty_columns <= 10:  # Show first 10 empty columns
                    print(f"❌ {col_id}: EMPTY")
        
        print(f"\nSummary: {set_columns} columns set, {empty_columns} columns empty")
        
        # Check if our key columns were set
        print("\n8. Checking key columns...")
        key_columns = {
            'dropdown_mkr542p2': 'CUSTOMER',
            'dropdown_mkr5tgaa': 'STYLE',
            'dropdown_mkr5677f': 'COLOR',
            'text_mkr5ej2x': 'PO NUMBER'
        }
        
        for col in column_values_returned:
            col_id = col.get('id', '')
            if col_id in key_columns:
                col_text = col.get('text', '') or ''
                expected_field = key_columns[col_id]
                if col_text and col_text.strip():
                    print(f"✅ {expected_field} ({col_id}): '{col_text}'")
                else:
                    print(f"❌ {expected_field} ({col_id}): NOT SET")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        
        # If it's a JSON error, let's inspect the payload more carefully
        if "parsing error" in str(e).lower():
            print("\n🔍 GraphQL parsing error detected. Inspecting payload...")
            print(f"Column values JSON length: {len(column_values_json)}")
            print(f"Mutation length: {len(mutation)}")
            
            # Check for problematic characters
            problematic_chars = ['\n', '\r', '\t', '"', "'"]
            for char in problematic_chars:
                if char in column_values_json:
                    print(f"⚠️  Found problematic character in JSON: {repr(char)}")

if __name__ == "__main__":
    test_monday_api_call()
