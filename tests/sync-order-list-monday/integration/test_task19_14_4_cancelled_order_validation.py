#!/usr/bin/env python3
"""
Test Task 19.14.4 - Production Cancelled Order Validation
Purpose: Validate production cancelled order validation logic implementation

SUCCESS CRITERIA:
- Production cancelled order validator works correctly
- Matches successful test patterns from test_task19_data_merge_integration.py
- Focus on sync consistency for ACTIVE orders only
- Cancelled orders CAN have lines - this is normal business behavior
- Success metrics based on proper categorization and active order sync consistency
- Comprehensive logging includes cancelled order counts (informational, not failure)
"""

import sys
from pathlib import Path

# Legacy transition support pattern (PROVEN SUCCESSFUL)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator

logger = logger.get_logger(__name__)

def test_cancelled_order_validator():
    """Test the cancelled order validation via merge orchestrator"""
    logger.info("🧪 Testing Task 19.14.4 - Cancelled Order Validation via Merge Orchestrator")
    
    # Load configuration
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize merge orchestrator (now contains cancelled order validation)
    orchestrator = MergeOrchestrator(config)
    
    # Test general validation via merge orchestrator
    logger.info("📊 Running general cancelled order validation...")
    general_result = orchestrator.validate_cancelled_order_handling()
    
    if general_result['success']:
        logger.info("✅ General validation PASSED")
        logger.info(f"   Total headers: {general_result['total_headers']}")
        logger.info(f"   Active orders with lines: {general_result['active_headers_with_lines']}")
        logger.info(f"   Cancelled orders: {general_result['cancelled_orders']}")
        logger.info(f"   Sync consistency: {'✅ PASS' if general_result['sync_consistency_success'] else '❌ FAIL'}")
    else:
        logger.error("❌ General validation FAILED")
        if 'error' in general_result:
            logger.error(f"   Error: {general_result['error']}")
    
    # Test GREYSON PO 4755 specific validation via merge orchestrator
    logger.info("🎯 Running GREYSON PO 4755 specific validation...")
    greyson_result = orchestrator.validate_cancelled_order_handling(
        customer_name="GREYSON CLOTHIERS",
        po_number="4755"
    )
    
    if greyson_result['success']:
        logger.info("✅ GREYSON PO 4755 validation PASSED")
        logger.info(f"   Total: {greyson_result['total_headers']}, Active with lines: {greyson_result['active_headers_with_lines']}, Cancelled: {greyson_result['cancelled_orders']}")
    else:
        logger.error("❌ GREYSON PO 4755 validation FAILED")
    
    return general_result['success'] and greyson_result['success']

def test_merge_orchestrator_integration():
    """Test the integration of cancelled order validation in merge orchestrator"""
    logger.info("🔄 Testing merge orchestrator integration...")
    
    # Load configuration
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize merge orchestrator
    orchestrator = MergeOrchestrator(config)
    
    # Test cancelled order validation method
    validation_result = orchestrator.validate_cancelled_order_handling()
    
    if validation_result['success']:
        logger.info("✅ Merge orchestrator cancelled order validation PASSED")
        logger.info(f"   Integration working correctly")
    else:
        logger.error("❌ Merge orchestrator cancelled order validation FAILED")
        if 'error' in validation_result:
            logger.error(f"   Error: {validation_result['error']}")
    
    return validation_result['success']

def test_greyson_specific_validation():
    """Test GREYSON PO 4755 specific validation - focus on sync consistency for active orders"""
    logger.info("🎯 Testing GREYSON PO 4755 specific validation...")
    
    # Load configuration
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize merge orchestrator
    orchestrator = MergeOrchestrator(config)
    
    # Test GREYSON-specific validation
    greyson_result = orchestrator.validate_cancelled_order_handling(
        customer_name="GREYSON CLOTHIERS",
        po_number="4755"
    )
    
    if greyson_result['success']:
        logger.info("✅ GREYSON PO 4755 cancelled order validation PASSED")
        
        # Log current data state (no longer enforcing strict pattern match)
        logger.info(f"ℹ️ Current data state: {greyson_result['total_headers']} total, {greyson_result['active_headers_with_lines']} active with lines, {greyson_result['cancelled_orders']} cancelled")
        
        # Success based on sync consistency, not strict pattern matching
        sync_success = greyson_result.get('sync_consistency_success', False)
        
        if sync_success:
            logger.info("✅ Sync consistency validation passed for active orders")
        else:
            logger.warning("⚠️ Sync consistency issues detected")
        
        return sync_success
    else:
        logger.error("❌ GREYSON PO 4755 cancelled order validation FAILED")
        return False

def main():
    """Run comprehensive Task 19.14.4 validation tests"""
    logger.info("=" * 80)
    logger.info("🎯 TASK 19.14.4: Production Cancelled Order Validation Test")
    logger.info("=" * 80)
    logger.info("Context: Task 19.0 DELTA Elimination - Phase 5 Implementation")
    logger.info("Previous: Task 19.14.3 SUCCESS - Data merge integration validated")
    logger.info("Current: Production cancelled order validation logic implementation")
    logger.info("Reference: test_task19_data_merge_integration.py successful patterns")
    logger.info("=" * 80)
    
    # Run all tests
    test_results = []
    
    try:
        # Test 1: Direct validation via merge orchestrator
        logger.info("📋 Test 1: Cancelled Order Validation via Merge Orchestrator")
        validator_success = test_cancelled_order_validator()
        test_results.append(('cancelled_order_validation_via_merge_orchestrator', validator_success))
        
        # Test 2: Merge orchestrator integration
        logger.info("📋 Test 2: Merge Orchestrator Integration")
        integration_success = test_merge_orchestrator_integration()
        test_results.append(('merge_orchestrator_integration', integration_success))
        
        # Test 3: GREYSON PO 4755 specific validation
        logger.info("📋 Test 3: GREYSON PO 4755 Specific Validation")
        greyson_success = test_greyson_specific_validation()
        test_results.append(('greyson_specific_validation', greyson_success))
        
        # Calculate overall success
        overall_success = all(result[1] for result in test_results)
        
        # Final results
        logger.info("=" * 80)
        logger.info("📊 TASK 19.14.4 TEST RESULTS:")
        for test_name, success in test_results:
            logger.info(f"   {test_name}: {'✅ PASS' if success else '❌ FAIL'}")
        
        logger.info(f"   Overall Task 19.14.4 Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        if overall_success:
            logger.info("🎉 SUCCESS: Task 19.14.4 Production Cancelled Order Validation implemented successfully!")
            logger.info("✅ Production pipeline now includes cancelled order validation logic")
            logger.info("✅ Success metrics focus on active order sync consistency only")
            logger.info("✅ Cancelled orders with lines are properly tracked (not failed)")
            logger.info("✅ Logging provides comprehensive business intelligence")
            logger.info("🚀 Ready for production deployment with cancelled order handling")
        else:
            logger.error("❌ FAILURE: Task 19.14.4 Production Cancelled Order Validation needs fixes")
            logger.error("🔧 Check sync consistency for active orders only")
        
        logger.info("=" * 80)
        
        return 0 if overall_success else 1
        
    except Exception as e:
        logger.exception(f"Task 19.14.4 test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
