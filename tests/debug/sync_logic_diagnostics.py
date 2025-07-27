#!/usr/bin/env python3
"""
Sync Logic Diagnostics - Comprehensive Analysis
==============================================
Purpose: Diagnose the sync logic flaw in ORDER_LIST → Monday.com pipeline
Created: 2025-08-01 (Plan Mode Investigation)

Usage:
    python tests/debug/sync_logic_diagnostics.py --debug 01
    python tests/debug/sync_logic_diagnostics.py --debug 02
    python tests/debug/sync_logic_diagnostics.py --debug 03
    
Add more debug queries as we investigate...
"""

import sys
import argparse
from pathlib import Path

# Standard import pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def debug_01_user_query():
    """User's exact query to verify sync_state + action_type combinations"""
    print("🔍 DEBUG 01: User's Query - sync_state + action_type by customer")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        cursor.execute('''
        SELECT [CUSTOMER NAME], [sync_state], [action_type], COUNT(*) 
        FROM [FACT_ORDER_LIST] 
        GROUP BY [sync_state], [action_type], [CUSTOMER NAME]
        ORDER BY [CUSTOMER NAME]
        ''')
        
        print("📊 Results (Customer, sync_state, action_type, count):")
        pending_customers = {}
        synced_customers = {}
        
        for customer, sync_state, action_type, count in cursor.fetchall():
            print(f"  {customer}: {sync_state} + {action_type} = {count} records")
            
            if sync_state == 'PENDING':
                pending_customers[customer] = pending_customers.get(customer, 0) + count
            elif sync_state == 'SYNCED':
                synced_customers[customer] = synced_customers.get(customer, 0) + count
        
        print(f"\n📋 PENDING Summary: {len(pending_customers)} customers with PENDING records")
        for customer, count in sorted(pending_customers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {customer}: {count} PENDING")
            
        print(f"\n✅ SYNCED Summary: {len(synced_customers)} customers with SYNCED records")
        for customer, count in sorted(synced_customers.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {customer}: {count} SYNCED")
        
        cursor.close()

def debug_02_born_primitive_analysis():
    """Deep dive into BORN PRIMITIVE records to understand why CLI finds 0"""
    print("\n🔍 DEBUG 02: BORN PRIMITIVE Deep Analysis")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check BORN PRIMITIVE records in detail
        cursor.execute('''
        SELECT 
            [sync_state],
            [action_type], 
            [monday_item_id],
            [group_id],
            [sync_pending_at],
            [sync_completed_at],
            COUNT(*) as record_count
        FROM [FACT_ORDER_LIST]
        WHERE [CUSTOMER NAME] = 'BORN PRIMITIVE'
        GROUP BY [sync_state], [action_type], [monday_item_id], [group_id], [sync_pending_at], [sync_completed_at]
        ORDER BY [sync_state], record_count DESC
        ''')
        
        print("📊 BORN PRIMITIVE Record Analysis:")
        total_pending = 0
        total_synced = 0
        
        for sync_state, action_type, monday_item_id, group_id, pending_at, completed_at, count in cursor.fetchall():
            print(f"  {sync_state} + {action_type}: {count} records")
            print(f"    monday_item_id: {monday_item_id}, group_id: {group_id}")
            print(f"    pending_at: {pending_at}, completed_at: {completed_at}")
            
            if sync_state == 'PENDING':
                total_pending += count
            elif sync_state == 'SYNCED':
                total_synced += count
        
        print(f"\n📋 BORN PRIMITIVE Summary:")
        print(f"  Total PENDING: {total_pending}")
        print(f"  Total SYNCED: {total_synced}")
        print(f"  Total: {total_pending + total_synced}")
        
        cursor.close()

def debug_03_first_5_pending_analysis():
    """Analyze the first 5 PENDING INSERT records that CLI actually queries"""
    print("\n🔍 DEBUG 03: First 5 PENDING INSERT Records (CLI Query)")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Exact query that CLI runs
        cursor.execute('''
        SELECT TOP 5
            [CUSTOMER NAME],
            [AAG ORDER NUMBER], 
            [PO NUMBER],
            [monday_item_id],
            [group_id],
            [sync_state],
            [action_type],
            [sync_pending_at]
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]
        ''')
        
        print("📊 First 5 PENDING + INSERT Records (CLI Query):")
        records = cursor.fetchall()
        
        if not records:
            print("  ❌ NO RECORDS FOUND!")
        else:
            for customer, order_num, po_num, item_id, group_id, sync_state, action_type, pending_at in records:
                print(f"  {customer}: Order {order_num}, PO {po_num}")
                print(f"    State: {sync_state} + {action_type}, Item: {item_id}, Group: {group_id}")
                print(f"    Pending: {pending_at}")
        
        # Check if BORN PRIMITIVE is in later records
        cursor.execute('''
        SELECT TOP 20
            [CUSTOMER NAME],
            [AAG ORDER NUMBER]
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]
        ''')
        
        print(f"\n📋 First 20 PENDING + INSERT Customers:")
        customers_seen = set()
        for customer, order_num in cursor.fetchall():
            if customer not in customers_seen:
                print(f"  {customer} (Order: {order_num})")
                customers_seen.add(customer)
        
        if 'BORN PRIMITIVE' not in customers_seen:
            print("  ❌ BORN PRIMITIVE NOT in first 20 PENDING INSERT records!")
        
        cursor.close()

def debug_04_cli_logic_simulation():
    """Simulate the exact CLI logic to see what's happening"""
    print("\n🔍 DEBUG 04: CLI Logic Simulation")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Step 1: Get first 5 PENDING INSERT records (CLI default query)
        cursor.execute('''
        SELECT TOP 5
            [CUSTOMER NAME]
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]
        ''')
        
        first_5_customers = [row[0] for row in cursor.fetchall()]
        print(f"📊 First 5 PENDING INSERT customers: {first_5_customers}")
        
        # Step 2: Apply customer filter (BORN PRIMITIVE)
        born_primitive_in_first_5 = 'BORN PRIMITIVE' in first_5_customers
        print(f"📋 BORN PRIMITIVE in first 5? {born_primitive_in_first_5}")
        
        if not born_primitive_in_first_5:
            # Check BORN PRIMITIVE's position in queue
            cursor.execute('''
            SELECT ROW_NUMBER() OVER (ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]) as position,
                   [CUSTOMER NAME],
                   [AAG ORDER NUMBER]
            FROM [FACT_ORDER_LIST]
            WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
            ''')
            
            born_primitive_position = None
            for position, customer, order_num in cursor.fetchall():
                if customer == 'BORN PRIMITIVE':
                    born_primitive_position = position
                    print(f"🎯 BORN PRIMITIVE first appears at position {position} (Order: {order_num})")
                    break
            
            if born_primitive_position is None:
                print("❌ BORN PRIMITIVE NOT FOUND in PENDING + INSERT records!")
            else:
                print(f"⚠️ BORN PRIMITIVE starts at position {born_primitive_position}, but CLI only takes first 5")
        
        cursor.close()

def debug_05_orderby_impact():
    """Analyze the ORDER BY clause impact on record selection"""
    print("\n🔍 DEBUG 05: ORDER BY Clause Impact Analysis")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check group_name values for PENDING records
        cursor.execute('''
        SELECT 
            [group_name],
            [CUSTOMER NAME],
            COUNT(*) as record_count
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        GROUP BY [group_name], [CUSTOMER NAME]
        ORDER BY [group_name], [CUSTOMER NAME]
        ''')
        
        print("📊 GROUP NAME + CUSTOMER Analysis (ORDER BY impact):")
        group_customer_pairs = cursor.fetchall()
        
        # Show first 10 group/customer combinations
        print("  First 10 combinations in ORDER BY [group_name], [CUSTOMER NAME]:")
        for i, (group_name, customer, count) in enumerate(group_customer_pairs[:10]):
            print(f"    {i+1}. Group: {group_name}, Customer: {customer}, Count: {count}")
        
        # Find BORN PRIMITIVE position
        born_primitive_position = None
        for i, (group_name, customer, count) in enumerate(group_customer_pairs):
            if customer == 'BORN PRIMITIVE':
                born_primitive_position = i + 1
                print(f"\n🎯 BORN PRIMITIVE found at position {born_primitive_position}")
                print(f"    Group: {group_name}, Records: {count}")
                break
        
        if born_primitive_position and born_primitive_position > 5:
            print(f"⚠️ BORN PRIMITIVE at position {born_primitive_position} > 5 (limit)")
            print("   This explains why CLI limit=5 doesn't find BORN PRIMITIVE!")
        
        cursor.close()

def debug_06_customer_ordering_analysis():
    """Analyze why customer filtering fails with limits"""
    print("\n🔍 DEBUG 06: Customer Filtering vs Limit Analysis")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Show the first 20 records in ORDER BY sequence
        cursor.execute('''
        SELECT TOP 20
            ROW_NUMBER() OVER (ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]) as position,
            [CUSTOMER NAME],
            [group_name],
            [AAG ORDER NUMBER]
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]
        ''')
        
        print("📊 First 20 PENDING INSERT Records (ORDER BY sequence):")
        for position, customer, group_name, order_num in cursor.fetchall():
            print(f"  {position:2d}. {customer} - {group_name} - {order_num}")
        
        # Count customers in alphabetical order
        cursor.execute('''
        SELECT 
            [CUSTOMER NAME],
            MIN([group_name]) as first_group,
            COUNT(*) as record_count
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        GROUP BY [CUSTOMER NAME]
        ORDER BY MIN([group_name]), [CUSTOMER NAME]
        ''')
        
        print(f"\n📋 Customer Order in PENDING Queue (explains limit=5 filtering):")
        customers_in_order = cursor.fetchall()
        for i, (customer, first_group, count) in enumerate(customers_in_order):
            position = i + 1
            status = "✅ IN LIMIT=5" if position <= 5 else "❌ AFTER LIMIT"
            print(f"  {position:2d}. {customer}: {count} records, First Group: {first_group} ({status})")
        
        cursor.close()

def debug_07_customer_native_architecture():
    """Test the new customer-native architecture approach"""
    print("\n🔍 DEBUG 07: Customer-Native Architecture Test")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Step 1: Get all customers with PENDING records (new approach)
        cursor.execute('''
        SELECT DISTINCT [CUSTOMER NAME]
        FROM [FACT_ORDER_LIST]
        WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
        ORDER BY [CUSTOMER NAME]
        ''')
        
        customers_with_pending = [row[0] for row in cursor.fetchall()]
        print(f"📊 Customers with PENDING records: {len(customers_with_pending)}")
        for i, customer in enumerate(customers_with_pending[:10]):
            print(f"  {i+1:2d}. {customer}")
        if len(customers_with_pending) > 10:
            print(f"  ... and {len(customers_with_pending) - 10} more")
        
        # Step 2: Test BORN PRIMITIVE specifically
        if 'BORN PRIMITIVE' in customers_with_pending:
            print(f"\n✅ BORN PRIMITIVE found in customer list at position {customers_with_pending.index('BORN PRIMITIVE') + 1}")
            
            # Get BORN PRIMITIVE's records with limit
            cursor.execute('''
            SELECT TOP 5
                [CUSTOMER NAME],
                [AAG ORDER NUMBER],
                [PO NUMBER],
                [sync_state],
                [action_type]
            FROM [FACT_ORDER_LIST]
            WHERE [sync_state] = 'PENDING' AND [action_type] = 'INSERT'
              AND [CUSTOMER NAME] = 'BORN PRIMITIVE'
            ORDER BY [group_name], [CUSTOMER NAME], [AAG ORDER NUMBER]
            ''')
            
            born_primitive_records = cursor.fetchall()
            print(f"🎯 BORN PRIMITIVE records with limit=5: {len(born_primitive_records)}")
            for customer, order_num, po_num, state, action in born_primitive_records:
                print(f"    {customer}: Order {order_num}, PO {po_num}, {state}+{action}")
        else:
            print(f"\n❌ BORN PRIMITIVE NOT found in customers with PENDING records!")
        
        # Step 3: Show customer-native approach vs old approach
        print(f"\n📋 Architecture Comparison:")
        print(f"  🔴 OLD: Get TOP 5 mixed records → filter by customer → often 0 results")
        print(f"  🟢 NEW: Get customers → get each customer's TOP 5 → guaranteed results per customer")
        
        cursor.close()

def debug_08_api_payload_analysis():
    """Get API payload for Monday.com testing and analyze the dropdown error"""
    print("\n🔍 DEBUG 08: API Payload Analysis for Monday.com Testing")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the specific API payload that failed (BORN PRIMITIVE record from latest sync)
        cursor.execute('''
        SELECT api_request_payload, api_response_payload, api_status, sync_state
        FROM FACT_ORDER_LIST 
        WHERE record_uuid = 'FEB611BC-A390-47CD-BDD7-54D2CE76C169'
        ''')
        
        result = cursor.fetchone()
        if result and result[0]:
            payload, response, status, sync_state = result
            print('🔥 API PAYLOAD FOR MONDAY.COM TESTING:')
            print('=' * 60)
            print(payload)
            print('=' * 60)
            print(f'📊 Status: {status}, Sync State: {sync_state}')
            
            if response:
                print('\n🚨 API RESPONSE ERROR:')
                print(response)
                
            print('\n🎯 ERROR ANALYSIS:')
            print('Column causing error: dropdown_mkr5tgaa')
            print('Error: InvalidColumnSettingsException - Invalid Settings')
            print('This suggests the dropdown value is not in the allowed options')
            
        else:
            print('❌ No payload found for record_uuid: FEB611BC-A390-47CD-BDD7-54D2CE76C169')
            
            # Check if record exists
            cursor.execute('''
            SELECT record_uuid, sync_state, api_status, [CUSTOMER NAME], [AAG ORDER NUMBER]
            FROM FACT_ORDER_LIST 
            WHERE record_uuid = 'FEB611BC-A390-47CD-BDD7-54D2CE76C169'
            ''')
            
            check = cursor.fetchone()
            if check:
                print(f'📋 Record exists: {check[0]}')
                print(f'   Customer: {check[3]}, Order: {check[4]}')
                print(f'   sync_state: {check[1]}, api_status: {check[2]}')
            else:
                print('❌ Record not found in FACT_ORDER_LIST')
        
        cursor.close()

def debug_09_latest_api_errors():
    """Get the latest API errors and payloads for Monday.com testing"""
    print("🔍 DEBUG 09: Latest API Errors and Payloads")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Get the latest record that just failed (BORN PRIMITIVE) 
    query = f"""
    SELECT TOP 1 
        record_uuid,
        api_status,
        sync_state,
        api_request_payload,
        api_response_payload,
        [CUSTOMER NAME],
        [item_name]
    FROM FACT_ORDER_LIST 
    WHERE [CUSTOMER NAME] = 'BORN PRIMITIVE' 
      AND sync_state = 'PENDING'
    ORDER BY sync_pending_at DESC
    """
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        record = cursor.fetchone()
        
        if record:
            record_uuid, api_status, sync_state, request_payload, response_payload, customer, item_name = record
            print(f"🎯 Latest BORN PRIMITIVE record: {record_uuid}")
            print("=" * 80)
            print(f"📊 Customer: {customer}")
            print(f"📊 Item: {item_name}")
            print(f"📊 Record Status: api_status={api_status}, sync_state={sync_state}")
            
            if request_payload:
                print("✅ Found API request payload!")
                print("=" * 80)
                print("📨 REQUEST PAYLOAD (for Monday.com developer portal):")
                print("=" * 80)
                print(request_payload)
                print("=" * 80)
                
                if response_payload:
                    print("📨 RESPONSE PAYLOAD:")
                    print("=" * 80)
                    print(response_payload)
                    print("=" * 80)
            else:
                print("❌ No request payload found - API logging may have failed")
        else:
            print("❌ No BORN PRIMITIVE records found")
    
    # Also get latest API errors from all customers
    print("\n🚨 Latest API Errors (Top 5):")
    print("=" * 80)
    
    error_query = f"""
    SELECT TOP 5
        record_uuid,
        [CUSTOMER NAME],
        api_status,
        api_response_payload,
        sync_pending_at
    FROM FACT_ORDER_LIST 
    WHERE api_status = 'ERROR'
      AND api_response_payload IS NOT NULL
    ORDER BY sync_pending_at DESC
    """
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        cursor.execute(error_query)
        errors = cursor.fetchall()
        
        if errors:
            for error in errors:
                record_uuid, customer, api_status, response_payload, sync_date = error
                print(f"❌ {customer} | {record_uuid} | {sync_date}")
                if response_payload and len(response_payload) < 500:
                    print(f"   Response: {response_payload}")
                print()
        else:
            print("✅ No API errors found!")
        
        cursor.close()

def debug_10_api_payload_manual():
    """Debug 10: Manually reconstruct the API payload for the failing record"""
    print("🔍 DEBUG 10: Manual API Payload Reconstruction")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Get the failing BORN PRIMITIVE record data
    query = """
    SELECT TOP 1
        record_uuid,
        [CUSTOMER NAME],
        [item_name],
        [group_id],
        [AAG ORDER NUMBER],
        [CUSTOMER STYLE],
        [CUSTOMER COLOUR DESCRIPTION],
        [FINAL FOB (USD)],
        [ETA CUSTOMER WAREHOUSE DATE],
        [EX FACTORY DATE],
        [CATEGORY],
        [DROP],
        [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS]
    FROM FACT_ORDER_LIST 
    WHERE [CUSTOMER NAME] = 'BORN PRIMITIVE' 
      AND sync_state = 'PENDING'
      AND record_uuid = 'FEB611BC-A390-47CD-BDD7-54D2CE76C169'
    """
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        record = cursor.fetchone()
        
        if record:
            (record_uuid, customer, item_name, group_id, order_num, customer_style, 
             color_desc, fob, eta_date, ex_factory, category, drop, customer_color_code) = record
            
            print(f"🎯 Record: {record_uuid}")
            print(f"📊 Customer: {customer}")
            print(f"📊 Item: {item_name}")
            print(f"📊 Group ID: {group_id}")
            print("=" * 80)
            
            # Reconstruct the API payload manually
            print("📨 RECONSTRUCTED API PAYLOAD (for Monday.com testing):")
            print("=" * 80)
            
            # Based on the Monday.com API structure from the sync logs
            api_payload = {
                "query": "mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!, $create_labels_if_missing: Boolean) { create_item (board_id: $board_id, group_id: $group_id, item_name: $item_name, column_values: $column_values, create_labels_if_missing: $create_labels_if_missing) { id } }",
                "variables": {
                    "board_id": "9609317401",
                    "group_id": str(group_id) if group_id else "unknown",
                    "item_name": item_name or "Unknown Item",
                    "create_labels_if_missing": True,
                    "column_values": {
                        "text_mktby7q": order_num or "",
                        "text_mktby8z": customer_style or "",
                        "text_mktbya4": color_desc or "",
                        "numbers_mktbydn": float(fob) if fob else 0,
                        "date_mktbyfs": eta_date.strftime("%Y-%m-%d") if eta_date else None,
                        "date_mktbygz": ex_factory.strftime("%Y-%m-%d") if ex_factory else None,
                        "dropdown_mkr5s5n3": category if category else None,
                        "dropdown_mkr5w5e": drop if drop else None,
                        "dropdown_mktbreb3": customer_color_code if customer_color_code else None,
                        "dropdown_mkr5tgaa": "SAND"  # This is the failing column!
                    }
                }
            }
            
            import json
            payload_json = json.dumps(api_payload, indent=2, default=str)
            print(payload_json)
            print("=" * 80)
            
            print("🚨 PROBLEM IDENTIFIED:")
            print("Column 'dropdown_mkr5tgaa' is trying to set value 'SAND'")
            print("This causes InvalidColumnSettingsException")
            print("Solution: Check Monday.com board column settings for dropdown_mkr5tgaa")
            print("Either 'SAND' is not in allowed values, or create_labels_if_missing is not working")
            
        else:
            print("❌ Record not found")
        
        cursor.close()
    print("\n🔍 DEBUG 09: Latest API Errors and Payloads")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get specific record payload first
        print("🎯 Getting API payload for record: 5683C886-ABBB-4D16-BF43-48E12D963ED2")
        print("=" * 80)
        cursor.execute("""
            SELECT api_request_payload, api_response_payload, api_status, sync_state
            FROM FACT_ORDER_LIST 
            WHERE record_uuid = '5683C886-ABBB-4D16-BF43-48E12D963ED2'
        """)
        
        record = cursor.fetchone()
        if record:
            request_payload, response_payload, api_status, sync_state = record
            print(f"📊 Record Status: api_status={api_status}, sync_state={sync_state}")
            
            if request_payload:
                print("\n🔥 API REQUEST PAYLOAD FOR MONDAY.COM TESTING:")
                print("=" * 80)
                print(request_payload)
                print("=" * 80)
                
                if response_payload:
                    print(f"\n📝 API Response: {response_payload}")
            else:
                print("❌ No request payload found - record may not have been processed yet")
        else:
            print("❌ Record not found!")
        
        # Get latest API errors
        cursor.execute('''
        SELECT TOP 5
            record_uuid,
            [CUSTOMER NAME],
            [AAG ORDER NUMBER],
            api_operation_type,
            api_request_payload,
            api_response_payload,
            api_status,
            sync_completed_at
        FROM [FACT_ORDER_LIST]
        WHERE api_status = 'ERROR'
        AND api_response_payload IS NOT NULL
        ORDER BY sync_completed_at DESC
        ''')
        
        print('\n🚨 Latest API Errors (Top 5):')
        print('=' * 80)
        
        errors = cursor.fetchall()
        if not errors:
            print('✅ No API errors found!')
        else:
            for i, (uuid, customer, order, operation, request, response, status, completed) in enumerate(errors, 1):
                print(f'\n🔥 ERROR #{i}:')
                print(f'   Customer: {customer}, Order: {order}')
                print(f'   UUID: {uuid}')
                print(f'   Operation: {operation}, Status: {status}')
                print(f'   Time: {completed}')
                
                if 'dropdown_mkr5tgaa' in str(response):
                    print('   🎯 CONTAINS dropdown_mkr5tgaa ERROR!')
                    
                if request:
                    print('\n📤 API REQUEST PAYLOAD FOR MONDAY.COM:')
                    print(request)
                    print('=' * 40)
                
                if response:
                    print(f'\n📥 Response: {response[:300]}...' if len(response) > 300 else f'\n📥 Response: {response}')
        
        cursor.close()

def main():
    parser = argparse.ArgumentParser(description="Sync Logic Diagnostics")
    parser.add_argument('--debug', choices=['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'], 
                       help='Debug query to run')
    args = parser.parse_args()
    
    if not args.debug:
        print("Available debug options:")
        print("  --debug 01: User's sync_state + action_type query")
        print("  --debug 02: BORN PRIMITIVE deep analysis")  
        print("  --debug 03: First 5 PENDING INSERT records (CLI query)")
        print("  --debug 04: CLI logic simulation")
        print("  --debug 05: ORDER BY clause impact analysis")
        print("  --debug 06: Customer filtering vs limit analysis")
        print("  --debug 07: Customer-native architecture test")
        print("  --debug 08: API payload analysis for Monday.com testing")
        print("  --debug 09: Latest API errors and payloads")
        return
    
    print(f"🚀 Running Sync Logic Diagnostics - DEBUG {args.debug}")
    print("=" * 60)
    
    if args.debug == '01':
        debug_01_user_query()
    elif args.debug == '02':
        debug_02_born_primitive_analysis()
    elif args.debug == '03':
        debug_03_first_5_pending_analysis()
    elif args.debug == '04':
        debug_04_cli_logic_simulation()
    elif args.debug == '05':
        debug_05_orderby_impact()
    elif args.debug == '06':
        debug_06_customer_ordering_analysis()
    elif args.debug == '07':
        debug_07_customer_native_architecture()
    elif args.debug == '08':
        debug_08_api_payload_analysis()
    elif args.debug == '09':
        debug_09_latest_api_errors()
    elif args.debug == '10':
        debug_10_api_payload_manual()
    
    print("\n" + "=" * 60)
    print("🔍 Diagnostic complete!")

if __name__ == "__main__":
    main()
