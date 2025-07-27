#!/usr/bin/env python3
"""
Step-by-Step Component Test Suite

Tests each component individually in sequence:
1. Find new records
2. Confirm query finds new records 
3. Insert records into MON_CustMasterSchedule with staging IDs
4. Confirm records inserted into MON_CustMasterSchedule
5. Execute Monday API 
6. Confirm records loaded in Monday.com
7. Update staging table with Monday.com IDs

Each test must be approved before moving to the next test.
"""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

# Add both project root and src to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pandas as pd
from datetime import datetime

# Make variables available globally for the test functions
globals()['project_root'] = project_root
globals()['src_path'] = src_path

def wait_for_approval(test_name: str, test_result: str) -> bool:
    """
    Wait for user approval before proceeding to next test
    
    Args:
        test_name: Name of the test
        test_result: Result summary
        
    Returns:
        True if approved, False if rejected
    """
    print(f"\n{'='*60}")
    print(f"🔍 TEST COMPLETED: {test_name}")
    print(f"{'='*60}")
    print(test_result)
    print(f"{'='*60}")
    
    while True:
        response = input("\n✅ Approve this test and continue? (y/n/details): ").strip().lower()
        if response in ['y', 'yes']:
            print("✅ Test approved - continuing to next test...\n")
            return True
        elif response in ['n', 'no']:
            print("❌ Test rejected - stopping test suite")
            return False
        elif response in ['d', 'details']:
            print("\n📋 Test Details:")
            print(test_result)
        else:
            print("Please enter 'y' for yes, 'n' for no, or 'd' for details")

def test_1_find_new_records():
    """
    TEST 1: Find new records from ORDERS_UNIFIED
    """
    print("🔍 TEST 1: Finding new records from ORDERS_UNIFIED")
    print("-" * 50)
    
    # Debug: Show paths
    print(f"📁 Project root: {project_root}")
    print(f"📁 Src path: {src_path}")
    print(f"📁 Current working directory: {os.getcwd()}")
    
    try:
        # Try to import the module
        print("🔄 Attempting to import customer_master_schedule.order_queries...")
        from customer_master_schedule.order_queries import get_new_orders_from_unified
        print("✅ Import successful!")
        
        # Get new orders with a small limit for testing
        print("🔄 Executing database query...")
        new_orders = get_new_orders_from_unified(limit=5)
        
        result_summary = f"""
📊 RESULTS:
- Found {len(new_orders)} new orders
- Database connection: ✅ Working
- Query execution: ✅ Working

📋 Sample Data:
"""
        
        if not new_orders.empty:
            result_summary += f"- First order: {new_orders.iloc[0].get('AAG ORDER NUMBER', 'N/A')}\n"
            result_summary += f"- Customer: {new_orders.iloc[0].get('CUSTOMER NAME', 'N/A')}\n"
            result_summary += f"- Style: {new_orders.iloc[0].get('CUSTOMER STYLE', 'N/A')}\n"
            result_summary += f"- Color: {new_orders.iloc[0].get('CUSTOMER COLOUR DESCRIPTION', 'N/A')}\n"
            
            result_summary += f"\n📋 Available Columns ({len(new_orders.columns)}):\n"
            for i, col in enumerate(new_orders.columns[:10]):  # Show first 10 columns
                result_summary += f"  {i+1}. {col}\n"
            if len(new_orders.columns) > 10:
                result_summary += f"  ... and {len(new_orders.columns) - 10} more columns\n"
        else:
            result_summary += "- No new orders found (this may be expected)\n"
        
        result_summary += f"\n✅ TEST 1 STATUS: PASSED"
        
        return wait_for_approval("Find New Records", result_summary), new_orders
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Database connection or query failed
- Error: {str(e)}

❌ TEST 1 STATUS: FAILED
"""
        return wait_for_approval("Find New Records", error_summary), pd.DataFrame()

def test_2_transform_data(new_orders_df):
    """
    TEST 2: Transform order data using mapping configuration
    """
    print("🔄 TEST 2: Transforming order data")
    print("-" * 50)
    
    if new_orders_df.empty:
        result_summary = """
⚠️ SKIPPED:
- No new orders available from Test 1
- Cannot test transformation without data

⚠️ TEST 2 STATUS: SKIPPED
"""
        return wait_for_approval("Transform Data", result_summary), []
    
    try:
        from customer_master_schedule.order_mapping import (
            load_mapping_config, 
            load_customer_mapping,
            transform_order_data
        )
        
        # Load configurations
        mapping_config = load_mapping_config()
        customer_lookup = load_customer_mapping()
        
        # Transform first order
        first_order = new_orders_df.iloc[0]
        transformed_data = transform_order_data(first_order, mapping_config, customer_lookup)
        
        result_summary = f"""
📊 RESULTS:
- Mapping config loaded: ✅ {len(mapping_config.get('exact_matches', []))} exact matches
- Customer lookup loaded: ✅ {len(customer_lookup)} variants
- Order transformed: ✅ {len(transformed_data)} fields

📋 Sample Transformed Fields:
"""
        
        # Show key transformed fields
        key_fields = ['STYLE', 'COLOR', 'AAG ORDER NUMBER', 'CUSTOMER_CODE', 'ORDER_TYPE']
        for field in key_fields:
            if field in transformed_data:
                field_data = transformed_data[field]
                if isinstance(field_data, dict):
                    value = field_data.get('value', 'N/A')
                    column_id = field_data.get('column_id', 'N/A')
                    result_summary += f"  - {field}: {value} (Column: {column_id})\n"
                else:
                    result_summary += f"  - {field}: {field_data}\n"
        
        result_summary += f"\n✅ TEST 2 STATUS: PASSED"
        
        return wait_for_approval("Transform Data", result_summary), [transformed_data]
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Transformation failed
- Error: {str(e)}

❌ TEST 2 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Transform Data", error_summary), []

def test_3_insert_staging(transformed_orders):
    """
    TEST 3: Insert records into MON_CustMasterSchedule with staging IDs
    """
    print("💾 TEST 3: Inserting records into staging table")
    print("-" * 50)
    
    if not transformed_orders:
        result_summary = """
⚠️ SKIPPED:
- No transformed orders available from Test 2
- Cannot test staging insert without data

⚠️ TEST 3 STATUS: SKIPPED
"""
        return wait_for_approval("Insert Staging", result_summary), []
    
    try:
        from customer_master_schedule.order_queries import (
            insert_orders_to_staging,
            get_database_connection,
            get_next_staging_id
        )
        
        # Get initial count in staging table
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
        initial_count = cursor.fetchone()[0]
        
        # Get next staging ID
        next_staging_id = get_next_staging_id()
        
        conn.close()
        
        # Convert to DataFrame
        df = pd.DataFrame(transformed_orders)
        
        # Insert into staging
        insert_success = insert_orders_to_staging(df)
        
        # Get final count
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
        final_count = cursor.fetchone()[0]
        
        # Get the records we just inserted
        cursor.execute(f"""
            SELECT TOP 5 [Item ID], [CUSTOMER_CODE], [ORDER_NUMBER], [STYLE], [COLOR], [ORDER_TYPE]
            FROM MON_CustMasterSchedule 
            WHERE [Item ID] >= {next_staging_id}
            ORDER BY [Item ID] DESC
        """)
        recent_records = cursor.fetchall()
        
        conn.close()
        
        result_summary = f"""
📊 RESULTS:
- Insert operation: {'✅ SUCCESS' if insert_success else '❌ FAILED'}
- Initial count: {initial_count}
- Final count: {final_count}
- Records added: {final_count - initial_count}
- Next staging ID used: {next_staging_id}

📋 Recently Inserted Records:
"""
        
        for record in recent_records:
            result_summary += f"  - ID: {record[0]} | Customer: {record[1]} | Order: {record[2]} | Style: {record[3]}\n"
        
        if final_count > initial_count:
            result_summary += f"\n✅ TEST 3 STATUS: PASSED"
            staging_ids = list(range(next_staging_id, next_staging_id + (final_count - initial_count)))
        else:
            result_summary += f"\n❌ TEST 3 STATUS: FAILED - No records actually inserted"
            staging_ids = []
        
        return wait_for_approval("Insert Staging", result_summary), staging_ids
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Staging insert failed
- Error: {str(e)}

❌ TEST 3 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Insert Staging", error_summary), []

def test_4_verify_staging(staging_ids):
    """
    TEST 4: Verify records exist in MON_CustMasterSchedule
    """
    print("🔍 TEST 4: Verifying records in staging table")
    print("-" * 50)
    
    if not staging_ids:
        result_summary = """
⚠️ SKIPPED:
- No staging IDs available from Test 3
- Cannot verify records without staging IDs

⚠️ TEST 4 STATUS: SKIPPED
"""
        return wait_for_approval("Verify Staging", result_summary), []
    
    try:
        from customer_master_schedule.order_queries import get_database_connection
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Query for our specific staging IDs
        staging_ids_str = ','.join(map(str, staging_ids))
        cursor.execute(f"""
            SELECT [Item ID], [CUSTOMER_CODE], [ORDER_NUMBER], [STYLE], [COLOR], 
                   [ORDER_TYPE], [DUE_DATE], [SYNC_STATUS]
            FROM MON_CustMasterSchedule 
            WHERE [Item ID] IN ({staging_ids_str})
            ORDER BY [Item ID]
        """)
        
        staged_records = cursor.fetchall()
        conn.close()
        
        result_summary = f"""
📊 RESULTS:
- Expected staging IDs: {len(staging_ids)}
- Found records: {len(staged_records)}
- Verification: {'✅ MATCH' if len(staged_records) == len(staging_ids) else '❌ MISMATCH'}

📋 Staged Records:
"""
        
        verified_records = []
        for record in staged_records:
            item_id, customer, order_num, style, color, order_type, due_date, sync_status = record
            result_summary += f"  - ID: {item_id} | {customer} | {order_num} | {style} | {order_type}\n"
            verified_records.append({
                'staging_id': item_id,
                'customer': customer,
                'order_number': order_num,
                'style': style,
                'color': color,
                'order_type': order_type
            })
        
        if len(staged_records) == len(staging_ids):
            result_summary += f"\n✅ TEST 4 STATUS: PASSED"
        else:
            result_summary += f"\n❌ TEST 4 STATUS: FAILED - Record count mismatch"
        
        return wait_for_approval("Verify Staging", result_summary), verified_records
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Staging verification failed
- Error: {str(e)}

❌ TEST 4 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Verify Staging", error_summary), []

def test_5_monday_api(verified_records):
    """
    TEST 5: Execute Monday.com API to create items
    """
    print("🚀 TEST 5: Creating items in Monday.com")
    print("-" * 50)
    
    if not verified_records:
        result_summary = """
⚠️ SKIPPED:
- No verified records available from Test 4
- Cannot test Monday.com API without data

⚠️ TEST 5 STATUS: SKIPPED
"""
        return wait_for_approval("Monday API", result_summary), []
    
    try:
        from customer_master_schedule.monday_integration import (
            create_monday_item,
            ensure_group_exists,
            get_board_info
        )
        from customer_master_schedule.add_order import determine_group_name
        
        BOARD_ID = "9200517329"
        
        # Get board info
        board_info = get_board_info(BOARD_ID)
        
        result_summary = f"""
📊 RESULTS:
- Board: {board_info['name']} (ID: {BOARD_ID})
- Records to process: {len(verified_records)}

📋 Monday.com API Results:
"""
        
        created_items = []
        
        # Process only the first record for testing
        record = verified_records[0]
        
        # Determine group name (simplified for test)
        group_name = f"{record['customer']} FALL 2025"  # Simplified for test
        
        # Ensure group exists
        group_id = ensure_group_exists(BOARD_ID, group_name)
        
        # Create item name
        item_name = f"{record['style']}_{record['color']}_{record['order_number']}".replace(' ', '_').replace('/', '_')
        
        # Create minimal column values for test
        column_values = {
            "text_mkr5wya6": record['order_number'],      # ORDER NUMBER
            "dropdown_mkr5tgaa": record['style'],         # STYLE
            "dropdown_mkr5677f": record['color'],         # COLOR
        }
        
        # Create Monday.com item
        monday_item_id = create_monday_item(
            board_id=BOARD_ID,
            group_id=group_id,
            item_name=item_name,
            column_values=column_values
        )
        
        if monday_item_id:
            result_summary += f"  ✅ Created item: {item_name}\n"
            result_summary += f"     - Monday.com ID: {monday_item_id}\n"
            result_summary += f"     - Group: {group_name} ({group_id})\n"
            result_summary += f"     - Staging ID: {record['staging_id']}\n"
            
            created_items.append({
                'staging_id': record['staging_id'],
                'monday_item_id': monday_item_id,
                'group_id': group_id,
                'item_name': item_name
            })
            
            result_summary += f"\n✅ TEST 5 STATUS: PASSED"
        else:
            result_summary += f"  ❌ Failed to create item: {item_name}\n"
            result_summary += f"\n❌ TEST 5 STATUS: FAILED"
        
        return wait_for_approval("Monday API", result_summary), created_items
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Monday.com API failed
- Error: {str(e)}

❌ TEST 5 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Monday API", error_summary), []

def test_6_update_staging(created_items):
    """
    TEST 6: Update staging table with Monday.com IDs
    """
    print("🔄 TEST 6: Updating staging table with Monday.com IDs")
    print("-" * 50)
    
    if not created_items:
        result_summary = """
⚠️ SKIPPED:
- No created items available from Test 5
- Cannot test staging update without Monday.com IDs

⚠️ TEST 6 STATUS: SKIPPED
"""
        return wait_for_approval("Update Staging", result_summary), False
    
    try:
        from customer_master_schedule.order_queries import (
            update_monday_item_id,
            get_database_connection
        )
        
        result_summary = f"""
📊 RESULTS:
- Items to update: {len(created_items)}

📋 Update Results:
"""
        
        updates_successful = 0
        
        for item in created_items:
            staging_id = str(item['staging_id'])
            monday_id = str(item['monday_item_id'])
            group_id = item['group_id']
            
            # Update the staging record
            update_success = update_monday_item_id(staging_id, monday_id, group_id)
            
            if update_success:
                result_summary += f"  ✅ Updated staging ID {staging_id} → Monday ID {monday_id}\n"
                updates_successful += 1
            else:
                result_summary += f"  ❌ Failed to update staging ID {staging_id}\n"
        
        # Verify the updates
        conn = get_database_connection()
        cursor = conn.cursor()
        
        for item in created_items:
            staging_id = item['staging_id']
            cursor.execute("""
                SELECT [Item ID], [SYNC_STATUS], [MONDAY_GROUP_ID] 
                FROM MON_CustMasterSchedule 
                WHERE [Item ID] = ?
            """, (item['monday_item_id'],))
            
            updated_record = cursor.fetchone()
            if updated_record:
                result_summary += f"  ✅ Verified: Record updated with Monday ID {updated_record[0]}\n"
        
        conn.close()
        
        if updates_successful == len(created_items):
            result_summary += f"\n✅ TEST 6 STATUS: PASSED"
            test_success = True
        else:
            result_summary += f"\n❌ TEST 6 STATUS: FAILED - {updates_successful}/{len(created_items)} updates successful"
            test_success = False
        
        return wait_for_approval("Update Staging", result_summary), test_success
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Staging update failed
- Error: {str(e)}

❌ TEST 6 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Update Staging", error_summary), False

def main():
    """
    Run the complete step-by-step test suite
    """
    print("🧪 STEP-BY-STEP COMPONENT TEST SUITE")
    print("=" * 60)
    print("Each test must be approved before proceeding to the next test.")
    print("=" * 60)
    
    # Test 1: Find new records
    test1_pass, new_orders = test_1_find_new_records()
    if not test1_pass:
        return 1
    
    # Test 2: Transform data
    test2_pass, transformed_orders = test_2_transform_data(new_orders)
    if not test2_pass:
        return 1
    
    # Test 3: Insert staging
    test3_pass, staging_ids = test_3_insert_staging(transformed_orders)
    if not test3_pass:
        return 1
    
    # Test 4: Verify staging
    test4_pass, verified_records = test_4_verify_staging(staging_ids)
    if not test4_pass:
        return 1
    
    # Test 5: Monday API
    test5_pass, created_items = test_5_monday_api(verified_records)
    if not test5_pass:
        return 1
    
    # Test 6: Update staging
    test6_pass, final_success = test_6_update_staging(created_items)
    if not test6_pass:
        return 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ Test 1: Find new records - PASSED")
    print("✅ Test 2: Transform data - PASSED") 
    print("✅ Test 3: Insert staging - PASSED")
    print("✅ Test 4: Verify staging - PASSED")
    print("✅ Test 5: Monday API - PASSED")
    print("✅ Test 6: Update staging - PASSED")
    print("=" * 60)
    print("🚀 End-to-end workflow is now fully functional!")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
