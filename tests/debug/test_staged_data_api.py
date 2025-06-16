"""
Debug script to test Monday.com API call using actual staged data from MON_CustMasterSchedule
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from customer_master_schedule.order_sync import get_db_connection, get_monday_column_values_for_staged_order, monday_api_call, BOARD_ID
import pandas as pd
import json

def test_with_staged_data():
    """Test Monday.com API call using actual staged data"""
    
    print("=" * 60)
    print("DEBUG: Monday.com API Call with Staged Data")
    print("=" * 60)
    
    # Get actual staged data from MON_CustMasterSchedule
    print("\n1. Fetching staged data from MON_CustMasterSchedule...")
    
    conn = get_db_connection()
    try:        # Get pending records using the proper query from the working script
        query = """
        SELECT TOP 10 *
        FROM [dbo].[MON_CustMasterSchedule]
        WHERE [Item ID] IS NOT NULL 
            AND ISNUMERIC([Item ID]) = 1 
            AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
            AND TRY_CAST([Item ID] AS BIGINT) < 10000
        ORDER BY TRY_CAST([Item ID] AS BIGINT) ASC
        """
        
        df = pd.read_sql(query, conn)
        
        if df.empty:
            print("❌ No staged records found. Run the order sync first to stage some data.")
            return
        
        print(f"✅ Found {len(df)} staged records to test")
        
        # Show the first record details
        first_record = df.iloc[0]
        print(f"\nTesting with record:")
        print(f"  Item ID: {first_record.get('Item ID', 'N/A')}")
        print(f"  AAG ORDER NUMBER: {first_record.get('AAG ORDER NUMBER', 'N/A')}")
        print(f"  CUSTOMER: {first_record.get('CUSTOMER', 'N/A')}")
        print(f"  STYLE: {first_record.get('STYLE', 'N/A')}")
        print(f"  COLOR: {first_record.get('COLOR', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error fetching staged data: {e}")
        return
    finally:
        conn.close()
    
    # Test the column values generation using real staged data
    print("\n2. Generating column values for staged data...")
    
    for idx, order_row in df.iterrows():
        print(f"\n--- Testing Record {idx + 1}: {order_row.get('AAG ORDER NUMBER', 'Unknown')} ---")
        
        try:            # Get column values using the new staged data method
            column_values = get_monday_column_values_for_staged_order(order_row)
            
            print(f"Generated {len(column_values)} column values")
            
            # Show key columns
            key_columns = {
                'dropdown_mkr542p2': 'CUSTOMER',
                'dropdown_mkr5tgaa': 'STYLE',
                'dropdown_mkr5677f': 'COLOR',
                'text_mkr5ej2x': 'PO NUMBER',
                'text_mkr5wya6': 'AAG ORDER NUMBER'
            }
            
            print("Key column values:")
            for col_id, field_name in key_columns.items():
                value = column_values.get(col_id, 'NOT FOUND')
                print(f"  {field_name}: {value}")
            
            # Test actual API call for the first record only
            if idx == 0:
                print(f"\n3. Testing actual Monday.com API call...")
                
                # Create item name and group name using the same logic as main script
                from customer_master_schedule.order_sync import create_item_name, create_group_name, ensure_group_exists
                
                item_name = create_item_name(order_row)
                group_name = create_group_name(order_row)
                
                print(f"Item name: '{item_name}'")
                print(f"Group name: '{group_name}'")
                
                # Ensure group exists
                try:
                    group_id = ensure_group_exists(group_name)
                    print(f"✅ Group ID: {group_id}")
                except Exception as e:
                    print(f"❌ Group creation failed: {e}")
                    continue
                
                # Create the API mutation
                sanitized_name = item_name.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
                column_values_json = json.dumps(column_values)
                
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
                
                print(f"\n4. Making API call...")
                print(f"Mutation length: {len(mutation)} characters")
                print(f"Column values JSON length: {len(column_values_json)} characters")
                
                try:
                    result = monday_api_call(mutation)
                    
                    print("✅ API call successful!")
                    item_id = result['data']['create_item']['id']
                    item_name_returned = result['data']['create_item']['name']
                    
                    print(f"Monday.com Item ID: {item_id}")
                    print(f"Monday.com Item Name: '{item_name_returned}'")
                    
                    # Analyze which columns were set
                    column_values_returned = result['data']['create_item'].get('column_values', [])
                    
                    print(f"\n5. Column analysis ({len(column_values_returned)} total columns):")
                    
                    set_columns = 0
                    key_results = {}
                    
                    for col in column_values_returned:
                        col_id = col.get('id', '')
                        col_text = col.get('text', '') or ''
                        
                        if col_text.strip():
                            set_columns += 1
                        
                        # Check key columns
                        if col_id in key_columns:
                            key_results[col_id] = col_text
                    
                    print(f"Total columns set: {set_columns}")
                    print(f"Key column results:")
                    for col_id, field_name in key_columns.items():
                        value = key_results.get(col_id, 'NOT SET')
                        status = "✅" if value and value != 'NOT SET' else "❌"
                        print(f"  {status} {field_name}: '{value}'")
                    
                    # Compare sent vs received values
                    print(f"\n6. Sent vs Received comparison:")
                    for col_id, field_name in key_columns.items():
                        sent_value = column_values.get(col_id, 'NOT SENT')
                        received_value = key_results.get(col_id, 'NOT RECEIVED')
                        match_status = "✅" if str(sent_value) == str(received_value) else "❌"
                        print(f"  {match_status} {field_name}:")
                        print(f"    Sent: '{sent_value}'")
                        print(f"    Received: '{received_value}'")
                    
                except Exception as e:
                    print(f"❌ API call failed: {e}")
                    
                    # If it's a validation error, show more details
                    if "dropdown label" in str(e).lower() or "columnvalueexception" in str(e).lower():
                        print(f"\n🔍 Column validation error detected")
                        print(f"This suggests dropdown values don't match Monday.com options")
                        
                        # Show the problematic column values
                        print(f"Column values being sent:")
                        for col_id, value in column_values.items():
                            if 'dropdown' in col_id:
                                print(f"  {col_id}: '{value}'")
                
                break  # Only test the first record for API call
            
        except Exception as e:
            print(f"❌ Error processing record: {e}")
            continue

if __name__ == "__main__":
    test_with_staged_data()
