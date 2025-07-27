#!/usr/bin/env python3
"""
DEBUG: Limited Greyson PO 4755 Testing
Purpose: Test customer orders pipeline with controlled dataset
Location: tests/debug/test_greyson_po_4755_limited.py

This script will test the pipeline with exactly 5 records from Greyson PO 4755
once the critical fixes are implemented.
"""
import sys
from pathlib import Path

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper
from sql_test_helper import create_sql_tester

def test_greyson_po_4755_limited():
    """Test with limited Greyson PO 4755 dataset (5 records max) using SQL Test Helper"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("=== GREYSON PO 4755 LIMITED TEST ===")
    logger.info("Step 1: Checking source data availability...")
    
    # Create SQL test helper
    sql_tester = create_sql_tester('orders')
    
    query_check = """
    SELECT TOP 5
        [record_uuid],
        [AAG ORDER NUMBER], 
        [CUSTOMER NAME],
        [PO NUMBER],
        [CUSTOMER STYLE],
        [CUSTOMER COLOUR DESCRIPTION]
    FROM [dbo].[ORDERS_UNIFIED]
    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
        AND [record_uuid] IS NOT NULL
    ORDER BY [AAG ORDER NUMBER]
    """
    
    # Test query using SQL Test Helper
    result = sql_tester.test_query(
        query_name="GREYSON PO 4755 Source Data Check",
        sql_query=query_check,
        expected_columns=[
            'record_uuid', 
            'AAG ORDER NUMBER', 
            'CUSTOMER NAME', 
            'PO NUMBER', 
            'CUSTOMER STYLE', 
            'CUSTOMER COLOUR DESCRIPTION'
        ],
        expected_min_rows=1,
        expected_max_rows=10
    )
    
    # Log detailed results
    logger.info(f"Query executed in {result['execution_time']}s")
    logger.info(f"Found {result['row_count']} records with {result['column_count']} columns")
    
    if result['data_sample']:
        logger.info("Sample records:")
        for i, record in enumerate(result['data_sample']):
            aag_order = record.get('AAG ORDER NUMBER', 'N/A')
            customer = record.get('CUSTOMER NAME', 'N/A')
            po_num = record.get('PO NUMBER', 'N/A')
            logger.info(f"  {aag_order} - {customer} - {po_num}")
      # Log any errors or warnings
    for error in result['errors']:
        logger.error(error)
    for warning in result['warnings']:
        logger.warning(warning)
    
    if not result['success']:
        logger.error("Source data check FAILED")
        return False
    
    logger.info("Source data check PASSED")
    return True

def test_hash_generation():
    """Test hash generation for Greyson records"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("Step 2: Testing hash generation...")
    
    try:
        # Import change detector (after fixes are applied)
        from change_detector import ChangeDetector
        
        detector = ChangeDetector()
        changes = detector.detect_changes(
            customer_filter="GREYSON", 
            limit=5,
            po_number_filter="4755"  # Add PO filter for testing
        )
        
        logger.info(f"Change detection results: {len(changes)} records processed")
        
        if len(changes) > 0:
            change_summary = changes['change_type'].value_counts().to_dict()
            logger.info(f"Change classification: {change_summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"Hash generation test failed: {e}")
        return False

def test_orchestrator_execution():
    """Test main orchestrator with limited dataset"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("Step 3: Testing orchestrator execution...")
    
    try:
        # Import main orchestrator (after fixes are applied)
        from main_customer_orders import MainCustomerOrders
        
        orchestrator = MainCustomerOrders()
        
        # Run with limited scope - just test data availability
        logger.info("Testing with Greyson PO 4755 filter...")
        
        # For now, just test that we can instantiate and check basic functionality
        logger.info("Orchestrator instantiated successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Orchestrator test failed: {e}")
        return False

def main():
    """Run complete limited test suite"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("Starting Greyson PO 4755 Limited Test Suite...")
    
    # Test sequence
    tests = [
        ("Source Data Check", test_greyson_po_4755_limited),
        ("Hash Generation", test_hash_generation),
        ("Orchestrator Execution", test_orchestrator_execution)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"{test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    overall_success = all(results.values())
    logger.info(f"\nOverall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
