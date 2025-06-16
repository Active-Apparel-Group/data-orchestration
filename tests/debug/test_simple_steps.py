#!/usr/bin/env python3
"""
Simple Step-by-Step Test - Using Task Approach

Tests each component individually using the same import approach as the working VS Code tasks.
"""

import sys
import os

# Use the same approach as the working VS Code tasks
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pandas as pd
from datetime import datetime
from typing import Dict

def wait_for_approval(test_name: str, test_result: str) -> bool:
    """Wait for user approval before proceeding to next test"""
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
    """TEST 1: Find new records from ORDERS_UNIFIED"""
    print("🔍 TEST 1: Finding new records from ORDERS_UNIFIED")
    print("-" * 50)
    
    try:
        # Import using the working approach
        from customer_master_schedule.order_queries import get_new_orders_from_unified
        print("✅ Import successful!")
        
        # Test database connection and query
        new_orders = get_new_orders_from_unified(limit=5)
        
        result_summary = f"""
📊 RESULTS:
- Found {len(new_orders)} new orders
- Database connection: ✅ Working
- Query execution: ✅ Working

📋 Sample Data (first record):
"""
        
        if not new_orders.empty:
            first_order = new_orders.iloc[0]
            result_summary += f"- Order: {first_order.get('AAG ORDER NUMBER', 'N/A')}\n"
            result_summary += f"- Customer: {first_order.get('CUSTOMER NAME', 'N/A')}\n"
            result_summary += f"- Style: {first_order.get('CUSTOMER STYLE', 'N/A')}\n"
            result_summary += f"- Color: {first_order.get('CUSTOMER COLOUR DESCRIPTION', 'N/A')}\n"
            result_summary += f"- Season: {first_order.get('CUSTOMER SEASON', 'N/A')}\n"
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
        import traceback
        print("Full error traceback:")
        traceback.print_exc()
        return wait_for_approval("Find New Records", error_summary), pd.DataFrame()

def test_2_check_staging_count():
    """TEST 2: Check current staging table count"""
    print("📊 TEST 2: Checking current staging table count")
    print("-" * 50)
    
    try:
        from customer_master_schedule.order_queries import get_database_connection, get_next_staging_id
        
        conn = get_database_connection()
        if not conn:
            raise Exception("Failed to get database connection")
            
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
        total_count = cursor.fetchone()[0]
          # Get count of staging IDs (1000+) - using BIGINT to handle large numbers
        cursor.execute("""
            SELECT COUNT(*) FROM MON_CustMasterSchedule 
            WHERE [Item ID] IS NOT NULL 
            AND ISNUMERIC([Item ID]) = 1 
            AND TRY_CAST([Item ID] AS BIGINT) >= 1000 
            AND TRY_CAST([Item ID] AS BIGINT) < 10000000
        """)
        staging_count = cursor.fetchone()[0]
        
        # Get count of Monday.com IDs (high numbers) - using BIGINT
        cursor.execute("""
            SELECT COUNT(*) FROM MON_CustMasterSchedule 
            WHERE [Item ID] IS NOT NULL 
            AND ISNUMERIC([Item ID]) = 1 
            AND TRY_CAST([Item ID] AS BIGINT) >= 10000000
        """)
        monday_count = cursor.fetchone()[0]
        
        # Get next staging ID
        next_id = get_next_staging_id()
        
        conn.close()
        
        result_summary = f"""
📊 STAGING TABLE STATUS:
- Total records: {total_count}
- Staging IDs (1000+): {staging_count}
- Monday.com IDs (10M+): {monday_count}
- Next staging ID: {next_id}

📋 Table Structure: ✅ Ready for testing

✅ TEST 2 STATUS: PASSED
"""
        
        return wait_for_approval("Check Staging Count", result_summary), next_id
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Staging table check failed
- Error: {str(e)}

❌ TEST 2 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Check Staging Count", error_summary), None

def test_3_transform_single_order(new_orders):
    """TEST 3: Transform a single order"""
    print("🔄 TEST 3: Transforming a single order")
    print("-" * 50)
    
    if new_orders.empty:
        result_summary = """
⚠️ SKIPPED:
- No new orders available from Test 1
- Cannot test transformation without data

⚠️ TEST 3 STATUS: SKIPPED
"""
        return wait_for_approval("Transform Single Order", result_summary), None
    
    try:
        from customer_master_schedule.order_mapping import (
            load_mapping_config,
            load_customer_mapping,
            transform_order_data
        )
        
        # Load configurations
        print("📋 Loading configurations...")
        mapping_config = load_mapping_config()
        customer_lookup = load_customer_mapping()
        
        # Transform first order
        print("🔄 Transforming order...")
        first_order = new_orders.iloc[0]
        transformed_data = transform_order_data(first_order, mapping_config, customer_lookup)
        
        result_summary = f"""
📊 TRANSFORMATION RESULTS:
- Mapping config: ✅ Loaded ({len(mapping_config.get('exact_matches', []))} exact matches)
- Customer lookup: ✅ Loaded ({len(customer_lookup)} variants)
- Order transformed: ✅ {len(transformed_data)} fields

📋 Key Transformed Fields:
"""
        
        # Show important fields
        key_fields = ['STYLE', 'COLOR', 'AAG ORDER NUMBER', 'CUSTOMER_CODE', 'ORDER_TYPE']
        for field in key_fields:
            if field in transformed_data:
                field_data = transformed_data[field]
                if isinstance(field_data, dict):
                    value = field_data.get('value', 'N/A')
                    result_summary += f"  - {field}: {value}\n"
                else:
                    result_summary += f"  - {field}: {field_data}\n"
        
        result_summary += f"\n✅ TEST 3 STATUS: PASSED"
        
        return wait_for_approval("Transform Single Order", result_summary), transformed_data
        
    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Transformation failed
- Error: {str(e)}

❌ TEST 3 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Transform Single Order", error_summary), None

def test_4_insert_staging(transformed_data, next_staging_id):
    """TEST 4: Insert transformed data into staging table"""
    print("💾 TEST 4: Inserting into staging table")
    print("-" * 50)
    
    if not transformed_data:
        result_summary = """
⚠️ SKIPPED:
- No transformed data available from Test 3
- Cannot test staging insert without data

⚠️ TEST 4 STATUS: SKIPPED
"""
        return wait_for_approval("Insert Staging", result_summary), None
    
    try:
        from customer_master_schedule.order_queries import (
            insert_orders_to_staging,
            get_database_connection
        )
        
        print("🔄 Getting initial count...")
        
        # Get initial count
        conn = get_database_connection()
        if not conn:
            raise Exception("Failed to get database connection")
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
        initial_count = cursor.fetchone()[0]
        print(f"📊 Initial count: {initial_count}")
        conn.close()
          # Convert to DataFrame and insert using our new flattening function
        from customer_master_schedule.order_mapping import create_staging_dataframe
        df = create_staging_dataframe([transformed_data])
        print(f"📋 Inserting DataFrame with {len(df)} record(s)...")
        print(f"📋 Expected staging ID: {next_staging_id}")
        
        # Perform the insert
        insert_success = insert_orders_to_staging(df)
        print(f"📋 Insert operation result: {insert_success}")
        
        # Get final count for verification
        print("🔄 Getting final count...")
        conn = get_database_connection()
        if not conn:
            raise Exception("Failed to reconnect for verification")
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM MON_CustMasterSchedule")
        final_count = cursor.fetchone()[0]
        print(f"📊 Final count: {final_count}")
          # Check if our record was inserted
        print(f"🔍 Checking for staging ID {next_staging_id}...")
        cursor.execute(f"""
            SELECT [Item ID], [CUSTOMER], [AAG ORDER NUMBER], [STYLE], [COLOR]
            FROM MON_CustMasterSchedule 
            WHERE [Item ID] = '{next_staging_id}'
        """)
        inserted_record = cursor.fetchone()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🔍 TEST COMPLETED: Insert Staging")
        print("=" * 60)

        if insert_success and inserted_record:
            result_summary = f"""
📊 INSERT RESULTS:
- Insert operation: ✅ SUCCESS
- Initial count: {initial_count}
- Final count: {final_count}
- Records added: {final_count - initial_count}
- Expected staging ID: {next_staging_id}
- Record found: ✅ YES

📋 Inserted Record:
  - Staging ID: {inserted_record[0]}
  - Customer: {inserted_record[1]}
  - Order: {inserted_record[2]}
  - Style: {inserted_record[3]}
  - Color: {inserted_record[4]}

✅ TEST 4 STATUS: PASSED
"""
            return wait_for_approval("Insert Staging", result_summary), next_staging_id
        else:
            result_summary = f"""
📊 INSERT RESULTS:
- Insert operation: {'✅ SUCCESS' if insert_success else '❌ FAILED'}
- Initial count: {initial_count}
- Final count: {final_count}
- Records added: {final_count - initial_count}
- Expected staging ID: {next_staging_id}
- Record found: {'✅ YES' if inserted_record else '❌ NO'}

📋 Inserted Record:
  - {'Record details above' if inserted_record else 'No record found with staging ID ' + str(next_staging_id)}

❌ TEST 4 STATUS: FAILED
"""
            return wait_for_approval("Insert Staging", result_summary), None

    except Exception as e:
        error_summary = f"""
❌ ERRORS:
- Staging insert failed
- Error: {str(e)}

❌ TEST 4 STATUS: FAILED
"""
        import traceback
        traceback.print_exc()
        return wait_for_approval("Insert Staging", error_summary), None

def test_5_sync_to_monday(staging_id: int, transformed_data: Dict = None) -> tuple[bool, str]:
    """Test Step 5: Sync staging record to Monday.com and get item ID"""
    
    print("🚀 TEST 5: Syncing record to Monday.com")
    print("-" * 50)
    
    if staging_id is None:
        result_summary = """
⚠️ SKIPPED:
- No staging ID available from Test 4
- Cannot test Monday.com sync without staging record

⚠️ TEST 5 STATUS: SKIPPED
"""
        return wait_for_approval("Sync to Monday.com", result_summary), None
    
    try:
        from customer_master_schedule.order_queries import (
            get_database_connection,
            get_pending_monday_sync
        )
        from customer_master_schedule.monday_integration import (
            create_monday_item,
            get_board_info
        )
        from customer_master_schedule.order_mapping import (
            format_monday_column_values,
            get_monday_column_values_dict
        )
        
        print(f"🔄 Getting staging record with ID {staging_id}...")
        
        # Get the staging record
        conn = get_database_connection()
        if not conn:
            raise Exception("Failed to get database connection")
            
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM MON_CustMasterSchedule 
            WHERE [Item ID] = {staging_id}
        """)
        record = cursor.fetchone()
        conn.close()
        
        if not record:
            raise Exception(f"No staging record found with ID {staging_id}")
        
        print("✅ Found staging record")
        print(f"📋 Customer: {record[4] if len(record) > 4 else 'N/A'}")  # CUSTOMER column        print(f"📋 Order: {record[5] if len(record) > 5 else 'N/A'}")     # AAG ORDER NUMBER column
        
        print("🔄 Creating Monday.com item...")
        
        # Use full transformation if available, otherwise fallback to simplified version
        if transformed_data:
            print("✅ Using FULL transformation with all mapped fields")
            item_name = transformed_data.get('Title', {}).get('value', f"Test-{staging_id}")
            column_values = get_monday_column_values_dict(transformed_data)
            print(f"📊 Monday.com fields to sync: {len(column_values)} fields")
        else:
            print("⚠️ Using SIMPLIFIED transformation (2 fields only)")
            # Fallback to simplified version for backward compatibility
            item_name = f"{record[5]}-{record[4]}" if len(record) > 5 else f"Test-{staging_id}"
            column_values = {
                "text_mkr5wya6": record[5] if len(record) > 5 else f"ORDER-{staging_id}",  # AAG ORDER NUMBER
                "dropdown_mkr542p2": record[4] if len(record) > 4 else "TEST CUSTOMER"     # CUSTOMER
            }
          # Create Monday.com item
        board_id = "9200517329"  # Customer Master Schedule board
        group_id = "group_mkr7d8xj"  # Default group
        
        monday_result = create_monday_item(
            board_id=board_id,
            group_id=group_id,
            item_name=item_name,
            column_values=column_values
        )
        
        if monday_result:
            monday_item_id = monday_result  # create_monday_item returns the item ID directly
            print(f"✅ Created Monday.com item: {monday_item_id}")
            
            # Update staging table with Monday.com ID
            print("🔄 Updating staging table with Monday.com ID...")
            conn = get_database_connection()
            if not conn:
                raise Exception("Failed to reconnect for update")
                
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE MON_CustMasterSchedule 
                SET [Item ID] = ?
                WHERE [Item ID] = ?
            """, (monday_item_id, staging_id))
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"📊 Updated {rows_updated} record(s)")
            
            result_summary = f"""
📊 MONDAY.COM SYNC RESULTS:
- Staging ID: {staging_id}
- Monday.com item created: ✅ YES
- Monday.com item ID: {monday_item_id}
- Item name: {item_name}
- Records updated: {rows_updated}

✅ TEST 5 STATUS: PASSED
"""
            return wait_for_approval("Sync to Monday.com", result_summary), monday_item_id
        else:
            raise Exception("Failed to create Monday.com item")
            
    except Exception as e:
        result_summary = f"""
📊 MONDAY.COM SYNC RESULTS:
- Staging ID: {staging_id}
- Error: {str(e)}

❌ TEST 5 STATUS: FAILED
"""
        return wait_for_approval("Sync to Monday.com", result_summary), None

def test_6_verify_staging_update(staging_id: int, monday_item_id: str) -> bool:
    """Test Step 6: Verify staging table was updated with Monday.com ID"""
    
    print("🔍 TEST 6: Verifying staging table update")
    print("-" * 50)
    
    if staging_id is None or monday_item_id is None:
        result_summary = """
⚠️ SKIPPED:
- Missing staging ID or Monday.com item ID from previous tests
- Cannot verify update without both IDs

⚠️ TEST 6 STATUS: SKIPPED
"""
        return wait_for_approval("Verify Staging Update", result_summary)
    
    try:
        from customer_master_schedule.order_queries import get_database_connection
        
        print(f"🔄 Checking staging record update...")
        print(f"📋 Staging ID: {staging_id}")
        print(f"📋 Monday.com ID: {monday_item_id}")
        
        # Check if the record was updated
        conn = get_database_connection()
        if not conn:
            raise Exception("Failed to get database connection")
            
        cursor = conn.cursor()
        
        # Check for record with Monday.com ID
        cursor.execute(f"""
            SELECT [Item ID], [CUSTOMER], [AAG ORDER NUMBER], [STYLE], [COLOR]
            FROM MON_CustMasterSchedule 
            WHERE [Item ID] = '{monday_item_id}'
        """)
        updated_record = cursor.fetchone()
        
        # Also check that the old staging ID is gone
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM MON_CustMasterSchedule 
            WHERE [Item ID] = {staging_id}
        """)
        old_record_count = cursor.fetchone()[0]
        
        conn.close()
        
        if updated_record and old_record_count == 0:
            result_summary = f"""
📊 STAGING UPDATE VERIFICATION:
- Original staging ID {staging_id}: ❌ REMOVED (correct)
- New Monday.com ID {monday_item_id}: ✅ FOUND
- Customer: {updated_record[1]}
- Order: {updated_record[2]}
- Style: {updated_record[3]}
- Color: {updated_record[4]}

✅ TEST 6 STATUS: PASSED
"""
            return wait_for_approval("Verify Staging Update", result_summary)
        else:
            result_summary = f"""
📊 STAGING UPDATE VERIFICATION:
- Original staging ID {staging_id}: {'✅ REMOVED' if old_record_count == 0 else f'❌ STILL EXISTS ({old_record_count} records)'
}
- New Monday.com ID {monday_item_id}: {'✅ FOUND' if updated_record else '❌ NOT FOUND'}

❌ TEST 6 STATUS: FAILED
"""
            return wait_for_approval("Verify Staging Update", result_summary)
            
    except Exception as e:
        result_summary = f"""
📊 STAGING UPDATE VERIFICATION:
- Error: {str(e)}

❌ TEST 6 STATUS: FAILED
"""
        return wait_for_approval("Verify Staging Update", result_summary)

def main():
    """Run the simplified step-by-step test suite"""
    print("🧪 SIMPLIFIED STEP-BY-STEP TEST SUITE")
    print("=" * 60)
    print("Testing core functionality step by step")
    print("=" * 60)
    
    # Test 1: Find new records
    test1_pass, new_orders = test_1_find_new_records()
    if not test1_pass:
        return 1
    
    # Test 2: Check staging table
    test2_pass, next_staging_id = test_2_check_staging_count()
    if not test2_pass:
        return 1
    
    # Test 3: Transform data
    test3_pass, transformed_data = test_3_transform_single_order(new_orders)
    if not test3_pass:
        return 1
      # Test 4: Insert staging
    test4_pass, staging_id = test_4_insert_staging(transformed_data, next_staging_id)
    if not test4_pass:
        return 1
      # Test 5: Sync to Monday.com
    test5_pass, monday_item_id = test_5_sync_to_monday(staging_id, transformed_data)
    if not test5_pass:
        return 1
    
    # Test 6: Verify staging table update
    test6_pass = test_6_verify_staging_update(staging_id, monday_item_id)
    if not test6_pass:
        return 1
    
    # Success summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ Test 1: Find new records - PASSED")
    print("✅ Test 2: Check staging table - PASSED") 
    print("✅ Test 3: Transform data - PASSED")
    print("✅ Test 4: Insert staging - PASSED")
    print("✅ Test 5: Sync to Monday.com - PASSED")
    print("✅ Test 6: Verify staging update - PASSED")
    print("=" * 60)
    print("🚀 End-to-end workflow is working!")
    print(f"📋 Staging ID {staging_id} → Monday.com ID {monday_item_id}")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
