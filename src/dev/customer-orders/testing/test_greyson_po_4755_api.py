#!/usr/bin/env python3
"""
GREYSON PO 4755 API INTEGRATION TEST

This test focuses specifically on GREYSON PO 4755 and tests the complete
staging → Monday.com API workflow.

Stages:
1. Customer batching for GREYSON with PO filter
2. Staging table operations  
3. Monday.com API integration (master schedule + subitems)
4. Validation and cleanup

INCLUDES API CALLS TO MONDAY.COM!
"""

import sys
from pathlib import Path
import pandas as pd

# Add project paths
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add dev/customer-orders to path

# Import from utils/ (using dynamic path)
import logger_helper

# Import from local dev/customer-orders directory
from customer_batch_processor import CustomerBatchProcessor
from staging_processor import StagingProcessor

def test_greyson_po_4755_api_integration():
    """
    Test the complete workflow with GREYSON PO 4755 including API calls
    """
    
    logger = logger_helper.get_logger(__name__)
    
    print("=" * 80)
    print("GREYSON PO 4755 - FULL API INTEGRATION TEST")
    print("=" * 80)
    
    target_customer = 'GREYSON'
    target_po = '4755'
    
    # Step 1: Customer Batching with PO Filter
    print("\n1. CUSTOMER BATCHING - GREYSON PO 4755")
    print("-" * 50)    
    batcher = CustomerBatchProcessor()
    
    try:
        # Get batches for GREYSON 
        batch_result = batcher.process_customer_batch(
            customer_filter=target_customer,
            limit=20  # Reasonable limit for testing
        )
        
        if batch_result['status'] == 'SUCCESS':
            print(f"   ✅ Customer batching successful")
            print(f"   📦 Batches created: {len(batch_result['batches'])}")
            print(f"   📊 Total records: {batch_result['summary'].get('total_records', 0)}")
            print(f"   🔄 Change types: {batch_result['summary'].get('change_type_summary', {})}")
            
            # Get the first batch data for processing
            if batch_result['batches']:
                batch_data = batch_result['batches'][0]['data']
                
                # Filter for PO 4755 if it exists
                if 'PO NUMBER' in batch_data.columns:
                    po_filtered = batch_data[batch_data['PO NUMBER'] == target_po]
                    if not po_filtered.empty:
                        print(f"   🎯 Found {len(po_filtered)} records for PO {target_po}")
                        batch_data = po_filtered
                    else:
                        print(f"   📊 No PO {target_po} found, using first {len(batch_data)} GREYSON records")
                        print(f"   📋 Available POs: {sorted(batch_data['PO NUMBER'].unique()) if 'PO NUMBER' in batch_data.columns else 'Unknown'}")
            else:
                print(f"   ❌ No batch data available")
                return
                
        else:
            print(f"   ❌ Customer batching failed: {batch_result.get('error', 'Unknown error')}")
            return
            
    except Exception as e:
        print(f"   ❌ Customer batching error: {str(e)}")
        return
    
    # Step 2: Staging Operations
    print("\n2. STAGING OPERATIONS")
    print("-" * 30)    
    
    processor = StagingProcessor()
    
    try:
        # Stage the batch
        batch_id = processor.stage_customer_batch(target_customer, batch_data)
        print(f"   ✅ Staging successful - Batch ID: {batch_id}")
        print(f"   📊 Orders staged: {len(batch_data)}")
        
    except Exception as e:
        print(f"   ❌ Staging failed: {str(e)}")
        return
    
    # Step 3: Monday.com API Integration - Master Schedule
    print("\n3. MONDAY.COM API - MASTER SCHEDULE")
    print("-" * 40)
    
    try:
        # Process master schedule items (create Monday.com items)
        master_result = processor.process_master_schedule(batch_id)
        
        if master_result['success']:
            print(f"   ✅ Master schedule processing successful")
            print(f"   📊 Items created: {master_result['processed']}/{master_result['total']}")
        else:
            print(f"   ❌ Master schedule processing failed")
            print(f"   📊 Items processed: {master_result.get('processed', 0)}/{master_result.get('total', 0)}")
            
    except Exception as e:
        print(f"   ❌ Master schedule API error: {str(e)}")
        # Continue to test subitems even if master fails
    
    # Step 4: Monday.com API Integration - Subitems
    print("\n4. MONDAY.COM API - SUBITEMS")
    print("-" * 35)
    
    try:
        # Process subitems (create Monday.com subitems)
        subitems_result = processor.process_subitems(batch_id)
        
        if subitems_result['success']:
            print(f"   ✅ Subitems processing successful")
            print(f"   📊 Subitems created: {subitems_result['processed']}/{subitems_result['total']}")
        else:
            print(f"   ❌ Subitems processing failed")
            print(f"   📊 Subitems processed: {subitems_result.get('processed', 0)}/{subitems_result.get('total', 0)}")
            
    except Exception as e:
        print(f"   ❌ Subitems API error: {str(e)}")
    
    # Step 5: Validation
    print("\n5. API INTEGRATION VALIDATION")
    print("-" * 35)
    
    try:        # Query staging tables to check API success
        orders_validation = f"""
        SELECT 
            COUNT(*) as total_orders,
            SUM(CASE WHEN stg_monday_item_id IS NOT NULL THEN 1 ELSE 0 END) as api_success_orders,
            SUM(CASE WHEN stg_error_message IS NOT NULL THEN 1 ELSE 0 END) as api_error_orders
        FROM [dbo].[STG_MON_CustMasterSchedule] 
        WHERE stg_batch_id = '{batch_id}'
        """
        
        # Note: Would need db connection here for validation
        print(f"   📊 Batch ID for manual validation: {batch_id}")
        print(f"   🔍 Check staging tables for API results")
        print(f"   🌐 Check Monday.com boards for created items")
        
    except Exception as e:
        print(f"   ⚠️ Validation query error: {str(e)}")
    
    # Step 6: Summary
    print("\n6. API INTEGRATION TEST SUMMARY")
    print("-" * 40)
    
    print(f"   🎯 Target: GREYSON PO {target_po}")
    print(f"   📦 Batch ID: {batch_id}")
    print(f"   ✅ Staging completed successfully")
    print(f"   🌐 Monday.com API integration attempted")
    print(f"   🔍 Manual validation required in Monday.com")
    
    print("\n" + "=" * 80)
    print("GREYSON PO 4755 API INTEGRATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_greyson_po_4755_api_integration()
