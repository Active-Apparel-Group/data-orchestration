#!/usr/bin/env python3
"""
PLAN MODE DIAGNOSTIC: Group ID Assignment Analysis
Check if group_name and group_id mapping is consistent in FACT_ORDER_LIST
and verify Monday.com API is using correct group_ids
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🔍 PLAN MODE: Group ID Assignment Diagnostic...")
    
    # Database connection
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        # Test 1: Check group_name to group_id mapping consistency
        print("\n📋 Test 1: Group Name to Group ID Mapping Analysis...")
        cursor.execute("""
            SELECT 
                group_name,
                group_id,
                COUNT(*) as record_count,
                COUNT(DISTINCT group_id) as unique_group_ids,
                MIN([AAG ORDER NUMBER]) as sample_order,
                MAX(created_at) as latest_record
            FROM FACT_ORDER_LIST
            WHERE sync_state = 'PENDING'
            AND group_name IS NOT NULL
            GROUP BY group_name, group_id
            ORDER BY group_name, group_id
        """)
        
        group_mappings = cursor.fetchall()
        print(f"Found {len(group_mappings)} group_name/group_id combinations:")
        
        group_id_issues = []
        for mapping in group_mappings:
            group_name, group_id, count, unique_ids, sample, latest = mapping
            if unique_ids > 1:
                group_id_issues.append(f"  ❌ {group_name}: {unique_ids} different group_ids")
            else:
                status = "✅ HAS GROUP_ID" if group_id else "❌ MISSING GROUP_ID"
                print(f"  {status} '{group_name}': {count} records, group_id={group_id}")
        
        if group_id_issues:
            print("\n⚠️ GROUP ID CONSISTENCY ISSUES:")
            for issue in group_id_issues:
                print(issue)
        
        # Test 2: Check for NULL group_ids with valid group_names
        print("\n🔍 Test 2: Missing Group IDs Analysis...")
        cursor.execute("""
            SELECT 
                group_name,
                COUNT(*) as records_without_group_id,
                MIN([AAG ORDER NUMBER]) as sample_order
            FROM FACT_ORDER_LIST
            WHERE sync_state = 'PENDING'
            AND group_name IS NOT NULL
            AND (group_id IS NULL OR group_id = '')
            GROUP BY group_name
            ORDER BY records_without_group_id DESC
        """)
        
        missing_group_ids = cursor.fetchall()
        if missing_group_ids:
            print(f"Found {len(missing_group_ids)} groups with missing group_ids:")
            for missing in missing_group_ids:
                print(f"  ❌ '{missing[0]}': {missing[1]} records missing group_id (sample: {missing[2]})")
        else:
            print("✅ All groups have group_ids assigned")
        
        # Test 3: Check sync engine's group assignment logic simulation
        print("\n🔧 Test 3: Sync Engine Group Assignment Simulation...")
        cursor.execute("""
            SELECT TOP 10
                [AAG ORDER NUMBER],
                [CUSTOMER NAME],
                group_name,
                group_id,
                sync_state,
                record_uuid
            FROM FACT_ORDER_LIST
            WHERE sync_state = 'PENDING'
            ORDER BY group_name, [CUSTOMER NAME]
        """)
        
        sample_headers = cursor.fetchall()
        print("Sample headers that sync engine would process:")
        for header in sample_headers:
            order_num, customer, group_name, group_id, sync_state, record_uuid = header
            group_status = f"group_id={group_id}" if group_id else "NO GROUP_ID"
            print(f"  Order: {order_num} | Customer: {customer}")
            print(f"    Group: '{group_name}' | {group_status} | UUID: {record_uuid}")
        
        # Test 4: Check if Monday.com API client should be using group_ids
        print("\n📊 Test 4: Monday.com API Construction Check...")
        print("Checking if sync engine passes group_ids to Monday.com API...")
        
        # Simulate what sync engine does
        if sample_headers:
            print("\nSync Engine Logic Simulation:")
            for header in sample_headers[:3]:  # Just first 3
                order_num, customer, group_name, group_id, sync_state, record_uuid = header
                
                print(f"\n  Processing: {order_num}")
                print(f"    _get_group_name_from_header() would return: '{group_name}'")
                print(f"    Available group_id in database: {group_id}")
                print(f"    ❓ QUESTION: Does Monday API client use group_id or group_name?")
        
        # Test 5: Check for duplicate group creation potential
        print("\n⚠️  Test 5: Duplicate Group Creation Risk Analysis...")
        cursor.execute("""
            SELECT 
                group_name,
                COUNT(DISTINCT group_id) as unique_group_ids,
                STRING_AGG(CAST(group_id AS VARCHAR), ', ') as all_group_ids
            FROM FACT_ORDER_LIST
            WHERE group_name IS NOT NULL
            AND group_id IS NOT NULL
            GROUP BY group_name
            HAVING COUNT(DISTINCT group_id) > 1
        """)
        
        duplicate_risks = cursor.fetchall()
        if duplicate_risks:
            print("🚨 FOUND DUPLICATE GROUP ID ASSIGNMENTS:")
            for risk in duplicate_risks:
                print(f"  Group '{risk[0]}' has {risk[1]} different IDs: {risk[2]}")
        else:
            print("✅ No duplicate group ID assignments found")
        
        cursor.close()

if __name__ == "__main__":
    main()
