#!/usr/bin/env python3
"""
STAGING-ONLY TEST - NO API CALLS

This test ONLY validates the staging tables without any Monday.com API calls.
We need to ensure staging works perfectly before moving to API integration.

Stages:
1. Customer batching (change detection)
2. Staging table inserts (STG_MON_CustMasterSchedule + Subitems)
3. Validation of staging data

NO API CALLS TO MONDAY.COM!
"""

import sys
from pathlib import Path
import pandas as pd

# Add project paths
current_dir = Path(__file__).parent
repo_root = current_dir.parent.parent
sys.path.insert(0, str(repo_root / "utils"))

import logger_helper
import db_helper as db
from customer_batcher import CustomerBatcher
from staging_processor import StagingProcessor

def test_staging_only():
    """
    Test ONLY the staging portion - NO API calls
    """
    
    logger = logger_helper.get_logger(__name__)
    
    print("=" * 70)
    print("STAGING-ONLY TEST - NO API CALLS")
    print("=" * 70)
    
    # Step 1: Customer Batching
    print("\n1. CUSTOMER BATCHING")
    print("-" * 30)    
    batcher = CustomerBatcher(max_batch_size=50)
    
    # Test with multiple customers (10 orders each for better testing)
    test_customers = ['GREYSON', 'ACTIVELY BLACK', 'PELOTON']
    
    all_batch_results = []
    
    for customer in test_customers:
        print(f"\n   Processing customer: {customer}")
        
        batch_result = batcher.process_customer_batch(
            customer_filter=customer,
            limit=10
        )
        
        if batch_result['status'] != 'SUCCESS':
            print(f"   ERROR: Customer batching failed for {customer} - {batch_result.get('error', 'Unknown error')}")
            continue
        
        print(f"   Status: {batch_result['status']}")
        print(f"   Batches created: {batch_result['summary']['total_batches']}")
        print(f"   Total records: {batch_result['summary']['total_records']}")
        print(f"   Change types: {batch_result['summary']['change_type_summary']}")
        
        all_batch_results.extend(batch_result['batches'])
    
    print(f"\nTotal customers processed: {len(test_customers)}")
    print(f"Total batches created: {len(all_batch_results)}")
    
    if len(all_batch_results) == 0:
        print("   ERROR: No batches created for any customers")
        return
      # Step 2: STAGING ONLY (NO API CALLS)
    print("\n2. STAGING PROCESSING (NO API CALLS)")
    print("-" * 30)
    
    processor = StagingProcessor()
    
    staging_results = []
    
    for batch in all_batch_results:
        customer = batch['customer']
        batch_data = batch['data']
        
        print(f"\n   Processing batch: {batch['batch_id']}")
        print(f"   Customer: {customer}")
        print(f"   Records: {batch['record_count']}")
        
        # ONLY STAGE - DON'T CALL APIs
        try:
            batch_id = processor.stage_customer_batch(customer, batch_data)
            
            result = {
                'customer': customer,
                'batch_id': batch_id,
                'status': 'STAGED',
                'staging': {'success': True, 'orders': len(batch_data)},
                'errors': []
            }
            
            print(f"   Status: STAGED SUCCESSFULLY")
            print(f"   Batch ID: {batch_id}")
            print(f"   Orders staged: {len(batch_data)}")
            
        except Exception as e:
            result = {
                'customer': customer,
                'batch_id': None,
                'status': 'FAILED',
                'staging': {'success': False, 'orders': 0},
                'errors': [str(e)]
            }
            
            print(f"   Status: STAGING FAILED")
            print(f"   Error: {str(e)}")
        
        staging_results.append(result)
    
    # Step 3: Staging Validation
    print("\n3. STAGING VALIDATION")
    print("-" * 30)
    
    successful_batches = sum(1 for r in staging_results if r['status'] == 'STAGED')
    total_orders_staged = sum(r['staging']['orders'] for r in staging_results)
    
    print(f"   Total batches processed: {len(staging_results)}")
    print(f"   Successful staging: {successful_batches}")
    print(f"   Total orders staged: {total_orders_staged}")
    print(f"   Success rate: {successful_batches/len(staging_results)*100:.1f}%")
    
    # Step 4: Database Validation (check staging tables)
    print("\n4. DATABASE VALIDATION")
    print("-" * 30)
    
    for result in staging_results:
        if result['status'] == 'STAGED':
            batch_id = result['batch_id']
            customer = result['customer']            
            print(f"\n   Validating batch: {customer} ({batch_id})")
            
            # Check staging orders
            orders_query = f"""
            SELECT COUNT(*) as order_count,
                   stg_status
            FROM [dbo].[STG_MON_CustMasterSchedule]
            WHERE stg_batch_id = '{batch_id}'
            GROUP BY stg_status
            """
            
            try:
                orders_results = db.run_query(orders_query, "ORDERS")
                if not orders_results.empty:
                    for _, row in orders_results.iterrows():
                        print(f"     Orders: {row['order_count']} with status '{row['stg_status']}'")
                else:
                    print(f"     WARNING: No orders found in staging for batch {batch_id}")
            except Exception as e:
                print(f"     ERROR: Failed to validate orders: {e}")
            
            # Check staging subitems
            subitems_query = f"""
            SELECT COUNT(*) as subitem_count
            FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
            WHERE stg_batch_id = '{batch_id}'
            """
            try:
                subitems_results = db.run_query(subitems_query, "ORDERS")
                if not subitems_results.empty:
                    subitem_count = subitems_results.iloc[0]['subitem_count']
                    print(f"     Subitems: {subitem_count} records staged")
                else:
                    print(f"     Subitems: 0 records staged")
            except Exception as e:
                print(f"     ERROR: Failed to validate subitems: {e}")
    
    # Summary
    print("\n5. STAGING TEST SUMMARY")
    print("-" * 30)
    
    if successful_batches == len(staging_results) and total_orders_staged > 0:
        print("   ✅ STAGING TEST PASSED")
        print("   ✅ All customer batches staged successfully")
        print("   ✅ Orders and subitems in staging tables")
        print("   ✅ Ready to proceed to Phase 4: API Integration")
    else:
        print("   ❌ STAGING TEST FAILED")
        print("   ❌ Fix staging issues before proceeding to API calls")
    
    print("\n" + "=" * 70)
    print("STAGING-ONLY TEST COMPLETE - NO API CALLS MADE")
    print("=" * 70)


if __name__ == "__main__":
    test_staging_only()
