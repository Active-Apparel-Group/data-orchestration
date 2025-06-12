#!/usr/bin/env python3
"""
Quick test to validate the performance fixes for the audit pipeline
"""
import sys
import os
import logging
import time
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / 'src'
sys.path.insert(0, str(src_dir))

from audit_pipeline.config import load_env, run_sql, load_customer_map
from audit_pipeline.etl import standardize_dataset, handle_master_order_list
from audit_pipeline.matching import match_records

def test_performance():
    """Test the audit pipeline with a small sample"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    start_time = time.time()
    logging.info("=== PERFORMANCE TEST STARTING ===")
    
    try:
        # Load environment and config
        load_env()
        customer_alias_map = load_customer_map()
        logging.info("✅ Configuration loaded")
        
        # Load data with sampling for performance test
        SAMPLE_SIZE = 100  # Small sample for testing
        
        logging.info("Loading sample data...")
        packed = run_sql('staging/v_packed_products.sql', 'distribution').head(SAMPLE_SIZE)
        shipped = run_sql('staging/v_shipped.sql', 'wah').head(SAMPLE_SIZE)
        master = run_sql('staging/v_master_order_list.sql', 'orders').head(SAMPLE_SIZE)
        
        logging.info(f"✅ Data loaded: {len(packed)} packed, {len(shipped)} shipped, {len(master)} orders")
        
        # Standardize datasets
        logging.info("Standardizing datasets...")
        orders_std = handle_master_order_list(master, customer_alias_map)
        packed_std = standardize_dataset(packed, 'PACKED', 'Qty', customer_alias_map)
        shipped_std = standardize_dataset(shipped, 'SHIPPED', 'Qty', customer_alias_map)
        
        logging.info(f"✅ Standardized: {len(packed_std)} packed, {len(shipped_std)} shipped, {len(orders_std)} orders")
        
        # Run matching
        logging.info("Running matching pipeline...")
        match_start = time.time()
        results, summary = match_records(packed_std, shipped_std, orders_std)
        match_time = time.time() - match_start
        
        logging.info(f"✅ Matching completed in {match_time:.2f} seconds")
        logging.info(f"   Results: {len(results)} total records")
        
        # Show sample results
        if not results.empty:
            match_summary = results['Match_Type'].value_counts()
            logging.info(f"   Match breakdown: {dict(match_summary)}")
            
            # Show sample of results
            logging.info("\n=== SAMPLE RESULTS ===")
            sample_cols = ['Canonical_Customer', 'Customer_PO', 'Style', 'Color', 'Size', 
                          'Packed_Qty', 'Shipped_Qty', 'Ordered_Qty', 'Match_Type', 'Match_Score']
            available_cols = [col for col in sample_cols if col in results.columns]
            
            if available_cols:
                print(results[available_cols].head(10).to_string(index=False))
        
        total_time = time.time() - start_time
        logging.info(f"\n=== PERFORMANCE TEST COMPLETED ===")
        logging.info(f"Total execution time: {total_time:.2f} seconds")
        logging.info(f"Matching time: {match_time:.2f} seconds")
        
        if total_time < 60:  # Less than 1 minute is good
            logging.info("🎉 Performance test PASSED - execution under 60 seconds")
            return True
        else:
            logging.warning("⚠️ Performance test SLOW - consider further optimization")
            return False
            
    except Exception as e:
        logging.error(f"❌ Performance test FAILED: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_performance()
    sys.exit(0 if success else 1)
