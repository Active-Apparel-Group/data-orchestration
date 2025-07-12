#!/usr/bin/env python3
"""
Integrated Workflow Test - Customer Batching + Staging Processing

Tests the complete workflow from change detection through staging processing.
"""

import sys
from pathlib import Path
import pandas as pd

# Add utils to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import logger_helper
from customer_batcher import CustomerBatcher
from staging_processor import StagingProcessor

def test_integrated_workflow():
    """Test the complete integrated workflow"""
    logger = logger_helper.get_logger(__name__)
    
    print("=" * 70)
    print("INTEGRATED WORKFLOW TEST - CUSTOMER BATCHING + STAGING PROCESSING")
    print("=" * 70)
    
    # Step 1: Get customer batches
    print("\n1. CUSTOMER BATCHING")
    print("-" * 30)
    
    batcher = CustomerBatcher(max_batch_size=50)
    
    # Test with GREYSON customer (limit 5 for testing)
    batch_result = batcher.process_customer_batch(
        customer_filter='GREYSON',
        limit=5
    )
    
    if batch_result['status'] != 'SUCCESS':
        print(f"   ERROR: Customer batching failed - {batch_result.get('error', 'Unknown error')}")
        return
    
    print(f"   Status: {batch_result['status']}")
    print(f"   Batches created: {batch_result['summary']['total_batches']}")
    print(f"   Total records: {batch_result['summary']['total_records']}")
    print(f"   Change types: {batch_result['summary']['change_type_summary']}")
    
    # Step 2: Process each batch through staging
    print("\n2. STAGING PROCESSING")
    print("-" * 30)
    
    processor = StagingProcessor()
    
    processing_results = []
    
    for batch in batch_result['batches']:
        customer = batch['customer']
        batch_data = batch['data']
        
        print(f"\n   Processing batch: {batch['batch_id']}")
        print(f"   Customer: {customer}")
        print(f"   Records: {batch['record_count']}")
        
        # Process the batch through staging
        result = processor.process_customer_batch_complete(customer, batch_data)
        processing_results.append(result)
        
        print(f"   Status: {result['status']}")
        print(f"   Master schedule: {result['master_schedule']['processed']}/{result['master_schedule']['total']}")
        print(f"   Subitems: {result['subitems']['processed']}")
        
        if result['errors']:
            print(f"   Errors: {len(result['errors'])}")
    
    # Step 3: Summary
    print("\n3. WORKFLOW SUMMARY")
    print("-" * 30)
    
    total_processed = sum(r['master_schedule']['processed'] for r in processing_results)
    successful_batches = sum(1 for r in processing_results if r['status'] == 'SUCCESS')
    total_batches = len(processing_results)
    
    print(f"   Total batches processed: {total_batches}")
    print(f"   Successful batches: {successful_batches}")
    print(f"   Total orders processed: {total_processed}")
    print(f"   Success rate: {successful_batches/total_batches*100:.1f}%")
    
    # Show detailed results
    print("\n4. DETAILED RESULTS")
    print("-" * 30)
    
    for i, result in enumerate(processing_results, 1):
        print(f"\n   Batch {i}: {result['customer']}")
        print(f"     Batch ID: {result['batch_id']}")
        print(f"     Status: {result['status']}")
        print(f"     Staging: {result['staging']['orders']} orders staged")
        print(f"     Master: {result['master_schedule']['processed']}/{result['master_schedule']['total']} processed")
        print(f"     Subitems: {result['subitems']['processed']} processed")
        
        if result['errors']:
            print(f"     Errors:")
            for error in result['errors']:
                print(f"       - {error}")
    
    print("\n" + "=" * 70)
    print("INTEGRATED WORKFLOW TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_integrated_workflow()
