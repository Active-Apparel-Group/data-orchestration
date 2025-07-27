"""
SQL Test Suite Runner
=====================

Runs all SQL query tests in the tests/sql_queries/ folder.
Provides comprehensive validation of all database queries used in the project.

Location: tests/sql_queries/run_all_tests.py
"""

import sys
from pathlib import Path
import importlib.util

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/
import logger_helper

def run_all_sql_tests():
    """Run all SQL tests in the sql_queries folder"""
    
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting SQL test suite")
    
    print("🧪 SQL TEST SUITE")
    print("=" * 50)
    
    test_files = [
        'test_customer_analysis_query.py',
        'test_customer_detail_query.py'
    ]
    
    test_results = []
    
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
        
        print(f"\n🔬 Running: {test_file}")
        print("-" * 40)
        
        try:
            # Import and run the test
            spec = importlib.util.spec_from_file_location("test_module", test_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # Run the main test function (assuming it follows naming convention)
            if hasattr(test_module, 'test_customer_analysis_query'):
                result = test_module.test_customer_analysis_query()
                test_results.append(('Customer Analysis Query', result['success']))
            elif hasattr(test_module, 'test_customer_detail_query'):
                result = test_module.test_customer_detail_query()
                test_results.append(('Customer Detail Query', result['success']))
            else:
                print(f"❌ No test function found in {test_file}")
                test_results.append((test_file, False))
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            test_results.append((test_file, False))
            logger.error(f"Test execution failed: {test_file} - {e}")
    
    # Summary
    print("\n📊 TEST SUITE SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<40} | {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        logger.info("All SQL tests passed successfully")
    else:
        print("⚠️  Some tests failed - review results above")
        logger.warning(f"SQL test failures: {total - passed} out of {total} tests failed")
    
    return test_results

if __name__ == "__main__":
    run_all_sql_tests()
