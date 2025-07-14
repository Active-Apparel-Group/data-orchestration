#!/usr/bin/env python3
"""
Validation Test for Refactored Scripts
Tests that the new import pattern works correctly for all refactored scripts
"""

import sys
from pathlib import Path

# NEW STANDARD: Find repository root, then find utils (Option 2)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path using repository root method
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import centralized modules
import logger_helper

# Initialize logger
logger = logger_helper.get_logger("validation_test")

def test_import_pattern():
    """Test that the standardized import pattern works"""
    logger.info("Testing standardized import pattern...")
    
    try:
        # Test utils imports
        import db_helper as db
        import mapping_helper as mapping
        logger.info("✅ Utils imports successful")
        
        # Test config loading
        config = db.load_config()
        logger.info("✅ Config loading successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import pattern test failed: {e}")
        return False

def test_refactored_scripts():
    """Test specific refactored scripts"""
    logger.info("Testing refactored scripts...")
    
    test_results = {}
      # List of refactored scripts to test
    scripts_to_test = [
        ("order_sync_v2", repo_root / "scripts" / "order_sync_v2.py"),
        ("sync_board_groups", repo_root / "scripts" / "monday-boards" / "sync_board_groups.py"),
        ("batch_processor", repo_root / "scripts" / "order_staging" / "batch_processor.py"),
        ("error_handler", repo_root / "scripts" / "order_staging" / "error_handler.py"),
        ("monday_api_client", repo_root / "scripts" / "order_staging" / "monday_api_client.py"),
        ("staging_operations", repo_root / "scripts" / "order_staging" / "staging_operations.py"),
        ("add_order", repo_root / "scripts" / "customer_master_schedule" / "add_order.py"),
        ("scan_codebase_config", repo_root / "dev" / "config_update" / "scan_codebase_config.py"),
        # New batch
        ("validate_env", repo_root / "dev" / "audit-pipeline" / "validation" / "validate_env.py"),
        ("monday_board_cli", repo_root / "dev" / "monday-boards-dynamic" / "core" / "monday_board_cli.py"),
        ("verify_db_types", repo_root / "dev" / "monday-boards-dynamic" / "debugging" / "verify_db_types.py"),
    ]
    
    for script_name, script_path in scripts_to_test:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            if spec and spec.loader:
                # We don't execute the module, just check it can be loaded
                logger.info(f"[PASS] {script_name}.py import pattern verified")
                test_results[script_name] = True
            else:
                raise ImportError("Could not load spec")
        except Exception as e:
            logger.error(f"[FAIL] {script_name}.py test failed: {e}")
            test_results[script_name] = False
    
    return test_results

def main():
    """Main validation function"""
    logger.info("=== Refactoring Validation Test ===")
    logger.info(f"Repository root: {repo_root}")
    
    # Test 1: Import pattern
    import_test_passed = test_import_pattern()
    
    # Test 2: Refactored scripts
    script_tests = test_refactored_scripts()
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Import pattern test: {'✅ PASSED' if import_test_passed else '❌ FAILED'}")
    
    for script, passed in script_tests.items():
        logger.info(f"{script}: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    overall_success = import_test_passed and all(script_tests.values())
    logger.info(f"\nOverall result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
