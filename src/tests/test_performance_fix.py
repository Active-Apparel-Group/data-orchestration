#!/usr/bin/env python3
"""
Performance test script to validate configuration caching improvements.
"""
import sys
import time
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from audit_pipeline.config import load_env, run_sql, load_customer_map
from audit_pipeline.etl import standardize_dataset, handle_master_order_list
from audit_pipeline.matching import match_records, add_match_keys, preload_customer_configs
import pandas as pd

def test_performance():
    print("=== Performance Test - Configuration Caching ===")
    
    # Load environment and customer mapping
    load_env()
    customer_alias_map = load_customer_map()
    
    # Create a small test dataset to focus on performance
    test_data = pd.DataFrame({
        'Customer': ['TEST_CUSTOMER'] * 100,  # 100 rows
        'Customer_PO': [f'PO_{i:03d}' for i in range(100)],
        'Style': [f'STYLE_{i:03d}' for i in range(100)],
        'Color': ['RED'] * 100,
        'Size': ['M'] * 100,
        'Qty': [1] * 100
    })
    
    print(f"Testing with {len(test_data)} rows...")
    
    # Test 1: Time the add_match_keys function with our caching
    start_time = time.time()
    
    # Standardize the test data
    standardized_data = standardize_dataset(test_data, 'TEST', 'Qty', customer_alias_map)
    
    # Add match keys (this is where the performance bottleneck was)
    result_data = add_match_keys(standardized_data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"✅ Performance Test Results:")
    print(f"   - Rows processed: {len(test_data)}")
    print(f"   - Time taken: {processing_time:.2f} seconds")
    print(f"   - Rate: {len(test_data)/processing_time:.1f} rows/second")
    
    if processing_time < 1.0:
        print("🚀 PERFORMANCE IMPROVEMENT SUCCESSFUL!")
        print("   Configuration caching is working - processing time under 1 second for 100 rows")
    else:
        print("⚠️  Performance may still need improvement")
    
    return processing_time

if __name__ == "__main__":
    test_performance()
