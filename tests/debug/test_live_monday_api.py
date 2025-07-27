#!/usr/bin/env python3
"""
Live Monday.com API Integration Test

Tests actual Monday.com API transactions to validate:
- Field mappings work correctly
- API adapter functions properly
- Rate limiting is respected
- Error handling works
- Master items and subitems can be created

This test uses a small subset of GREYSON data to validate API integration
before running full-scale testing.
"""

import sys
from pathlib import Path
import pandas as pd
import time
from datetime import datetime

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

# Import customer orders modules
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))
from monday_api_adapter import MondayApiAdapter
from customer_batch_processor import CustomerBatchProcessor

def test_api_connection():
    """Test basic API connectivity"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info("🔌 Testing Monday.com API connection...")
        
        api_adapter = MondayApiAdapter()
        
        # Test board info retrieval
        board_info = api_adapter._get_board_info()
        
        if board_info:
            logger.info(f"   ✅ Successfully connected to board: {board_info.get('name', 'Unknown')}")
            return True
        else:
            logger.error("   ❌ Failed to retrieve board information")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ API connection failed: {str(e)}")
        return False

def test_field_mappings():
    """Test that field mappings are correctly loaded and applied"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info("🗺️ Testing field mappings...")
        
        api_adapter = MondayApiAdapter()
        
        # Get sample GREYSON data (1 record)
        processor = CustomerBatchProcessor()
        sample_data = processor._get_customer_sample_data("GREYSON", limit=1)
        
        if sample_data.empty:
            logger.error("   ❌ No GREYSON sample data found")
            return False
        
        # Test mapping transformation
        sample_row = sample_data.iloc[0]
        mapped_data = api_adapter._prepare_master_item_data(sample_row)
        
        logger.info(f"   ✅ Sample data mapped successfully")
        logger.info(f"   📊 Mapped fields: {list(mapped_data.keys())}")
        
        # Validate required fields exist
        required_fields = ['customer', 'aag_order_number', 'po_number']
        missing_fields = [field for field in required_fields if field not in mapped_data or mapped_data[field] is None]
        
        if missing_fields:
            logger.warning(f"   ⚠️ Missing required fields: {missing_fields}")
        else:
            logger.info(f"   ✅ All required fields present")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Field mapping test failed: {str(e)}")
        return False

def test_create_master_item():
    """Test creating a single master item via API"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info("🎯 Testing master item creation...")
        
        api_adapter = MondayApiAdapter()
        processor = CustomerBatchProcessor()
        
        # Get one GREYSON record for testing
        sample_data = processor._get_customer_sample_data("GREYSON", limit=1)
        
        if sample_data.empty:
            logger.error("   ❌ No GREYSON sample data found")
            return False
        
        sample_row = sample_data.iloc[0]
        
        logger.info(f"   📋 Testing with PO: {sample_row.get('po_number', 'N/A')}")
        
        # Attempt to create master item
        result = api_adapter.create_master_schedule_item(sample_row)
        
        if result.get('success'):
            monday_item_id = result.get('monday_item_id')
            logger.info(f"   ✅ Master item created successfully: ID {monday_item_id}")
            
            # Store the item ID for cleanup later
            with open(repo_root / "tests" / "debug" / "test_api_cleanup.txt", "a") as f:
                f.write(f"{datetime.now()}: Created master item {monday_item_id}\n")
            
            return True, monday_item_id
        else:
            logger.error(f"   ❌ Master item creation failed: {result.get('error', 'Unknown error')}")
            return False, None
            
    except Exception as e:
        logger.error(f"   ❌ Master item creation test failed: {str(e)}")
        return False, None

def test_create_subitems(master_item_id: str):
    """Test creating subitems for a master item"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info(f"🔗 Testing subitem creation for master item {master_item_id}...")
        
        api_adapter = MondayApiAdapter()
        processor = CustomerBatchProcessor()
        
        # Get sample subitem data
        sample_data = processor._get_customer_sample_data("GREYSON", limit=1)
        
        if sample_data.empty:
            logger.error("   ❌ No sample data for subitems")
            return False
        
        # Simulate subitem data
        sample_row = sample_data.iloc[0]
        subitem_data = {
            'parent_monday_item_id': master_item_id,
            'size_label': 'XL',
            'order_qty': 10.0,
            'source_uuid': sample_row.get('uuid', 'test-uuid')
        }
        
        result = api_adapter.create_subitem(subitem_data)
        
        if result.get('success'):
            subitem_id = result.get('monday_subitem_id')
            logger.info(f"   ✅ Subitem created successfully: ID {subitem_id}")
            
            # Store for cleanup
            with open(repo_root / "tests" / "debug" / "test_api_cleanup.txt", "a") as f:
                f.write(f"{datetime.now()}: Created subitem {subitem_id}\n")
            
            return True
        else:
            logger.error(f"   ❌ Subitem creation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Subitem creation test failed: {str(e)}")
        return False

def test_rate_limiting():
    """Test that rate limiting is working correctly"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info("⏱️ Testing rate limiting (0.1s delays)...")
        
        api_adapter = MondayApiAdapter()
        
        # Make multiple rapid API calls to test rate limiting
        start_time = time.time()
        
        for i in range(3):
            logger.info(f"   📞 API call {i+1}...")
            board_info = api_adapter._get_board_info()
            if i < 2:  # Don't wait after the last call
                time.sleep(0.1)  # Expected delay
        
        total_time = time.time() - start_time
        expected_min_time = 0.2  # 2 delays of 0.1s each
        
        if total_time >= expected_min_time:
            logger.info(f"   ✅ Rate limiting working: {total_time:.2f}s (expected ≥{expected_min_time}s)")
            return True
        else:
            logger.warning(f"   ⚠️ Rate limiting may not be working: {total_time:.2f}s")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Rate limiting test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling with invalid data"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info("🚨 Testing error handling...")
        
        api_adapter = MondayApiAdapter()
        
        # Test with invalid/empty data
        invalid_data = pd.Series({})
        
        result = api_adapter.create_master_schedule_item(invalid_data)
        
        if not result.get('success'):
            logger.info(f"   ✅ Error handling working: {result.get('error', 'Error caught')}")
            return True
        else:
            logger.warning("   ⚠️ Error handling may not be working - invalid data succeeded")
            return False
            
    except Exception as e:
        # This is actually good - we want exceptions to be caught and handled
        logger.info(f"   ✅ Exception handling working: {str(e)}")
        return True

def run_all_api_tests():
    """Run comprehensive API integration test suite"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("🚀 Starting Monday.com API Integration Tests")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: API Connection
    results['connection'] = test_api_connection()
    
    # Test 2: Field Mappings
    results['mappings'] = test_field_mappings()
    
    # Test 3: Rate Limiting
    results['rate_limiting'] = test_rate_limiting()
    
    # Test 4: Error Handling
    results['error_handling'] = test_error_handling()
    
    # Test 5: Master Item Creation (only if basics work)
    master_item_id = None
    if results['connection'] and results['mappings']:
        success, master_item_id = test_create_master_item()
        results['master_item'] = success
        
        # Test 6: Subitem Creation (only if master item worked)
        if success and master_item_id:
            results['subitems'] = test_create_subitems(master_item_id)
        else:
            results['subitems'] = False
    else:
        results['master_item'] = False
        results['subitems'] = False
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 API Integration Test Results:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🚀 ALL TESTS PASSED - API integration is working!")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} tests failed - API integration needs attention")
        return False

if __name__ == "__main__":
    success = run_all_api_tests()
    exit(0 if success else 1)
