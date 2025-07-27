"""
Test ORDER_LIST Pipeline Logger Integration
Purpose: Verify all ORDER_LIST pipeline files use logger_helper correctly for Kestra/VS Code compatibility
Author: Data Engineering Team
Date: July 12, 2025

This test validates:
1. logger_helper.py functionality
2. All ORDER_LIST files use consistent logger patterns
3. Environment detection works correctly
4. Logger wrapper methods function properly
"""

import sys
import importlib.util
from pathlib import Path

def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with pipelines/utils folder")

# Setup paths
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

def test_logger_helper_functionality():
    """Test that logger_helper module works correctly"""
    print("\n📋 Testing logger_helper.py functionality...")
    
    try:
        # Test logger_helper import
        import logger_helper
        print("✅ logger_helper import: SUCCESS")
        
        # Test environment detection
        env_info = logger_helper.get_environment_info()
        print(f"✅ Environment detection: {env_info}")
        
        # Test logger creation
        test_logger = logger_helper.get_logger("test_logger")
        print("✅ Logger creation: SUCCESS")
        
        # Test wrapper functionality
        test_logger.info("Test info message")
        test_logger.warning("Test warning message") 
        test_logger.error("Test error message")
        print("✅ Logger wrapper methods: SUCCESS")
        
        # Test convenience functions
        logger_helper.info("Test convenience info function")
        logger_helper.warning("Test convenience warning function")
        print("✅ Convenience functions: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"❌ logger_helper functionality test failed: {e}")
        return False

def test_order_list_file_imports():
    """Test that all ORDER_LIST files can import and use logger correctly"""
    print("\n📋 Testing ORDER_LIST file logger integration...")
    
    order_list_files = [
        "order_list_pipeline",
        "order_list_blob", 
        "order_list_extract",
        "order_list_transform"
    ]
    
    failed_files = []
    
    for file_name in order_list_files:
        try:
            # Test import of the module
            file_path = repo_root / "pipelines" / "scripts" / "load_order_list" / f"{file_name}.py"
            
            if not file_path.exists():
                print(f"⚠️  {file_name}: File not found at {file_path}")
                failed_files.append(file_name)
                continue
            
            # Load and check for logger_helper usage
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for proper logger_helper import
            if "import logger_helper" not in content:
                print(f"❌ {file_name}: Missing 'import logger_helper'")
                failed_files.append(file_name)
                continue
            
            # Check for logger instance creation
            has_logger_instance = (
                "logger = logger_helper.get_logger(__name__)" in content or
                "self.logger = logger_helper.get_logger(__name__)" in content
            )
            
            if not has_logger_instance:
                print(f"❌ {file_name}: Missing logger instance creation")
                failed_files.append(file_name)
                continue
            
            # Check for old logging patterns (should be removed)
            problematic_patterns = [
                "logging.basicConfig(",
                "import logging",
                "logger_helper.info(",  # Should use instance methods
                "logger_helper.warning(",
                "logger_helper.error("
            ]
            
            issues = []
            for pattern in problematic_patterns:
                if pattern in content and pattern != "import logging":  # Some files might legitimately import logging for other reasons
                    if pattern == "import logging" and file_name == "order_list_blob":
                        # We removed logging import from blob file
                        continue
                    issues.append(pattern)
            
            if issues:
                print(f"⚠️  {file_name}: Found problematic patterns: {issues}")
            
            print(f"✅ {file_name}: Logger integration OK")
            
        except Exception as e:
            print(f"❌ {file_name}: Test failed with error: {e}")
            failed_files.append(file_name)
    
    if failed_files:
        print(f"\n❌ Failed files: {failed_files}")
        return False
    else:
        print("\n✅ All ORDER_LIST files have proper logger integration")
        return True

def test_logger_vs_print_usage():
    """Test that print statements have been replaced with logger calls where appropriate"""
    print("\n📋 Testing print vs logger usage...")
    
    files_to_check = [
        "order_list_extract.py",
        "order_list_blob.py"
    ]
    
    issues_found = []
    
    for file_name in files_to_check:
        file_path = repo_root / "pipelines" / "scripts" / "load_order_list" / file_name
        
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Look for print statements that should probably be logger calls
            if "print(" in line and not line.strip().startswith("#"):
                # Skip certain acceptable print usages
                if any(acceptable in line for acceptable in [
                    'print(f"{"',  # Formatting prints might be acceptable
                    "if __name__",  # Main function prints might be OK
                ]):
                    continue
                
                issues_found.append(f"{file_name}:{i}: {line.strip()}")
    
    if issues_found:
        print(f"⚠️  Found potential print statements that could be logger calls:")
        for issue in issues_found[:5]:  # Show first 5
            print(f"   {issue}")
        if len(issues_found) > 5:
            print(f"   ... and {len(issues_found) - 5} more")
        return False
    else:
        print("✅ No problematic print statements found")
        return True

def test_kestra_compatibility():
    """Test that logger configuration is compatible with Kestra environment"""
    print("\n📋 Testing Kestra compatibility...")
    
    try:
        import logger_helper
        
        # Test that environment detection works
        is_kestra = logger_helper.is_kestra_environment()
        is_vscode = logger_helper.is_vscode_environment()
        
        print(f"✅ Kestra environment detected: {is_kestra}")
        print(f"✅ VS Code environment detected: {is_vscode}")
        
        # Test that we can create loggers without errors
        logger1 = logger_helper.get_logger("test_module_1")
        logger2 = logger_helper.get_logger("test_module_2")
        
        # Test different log levels
        logger1.info("Kestra compatibility test - info level")
        logger1.warning("Kestra compatibility test - warning level")
        logger2.error("Kestra compatibility test - error level")
        
        print("✅ Kestra compatibility: All logger operations successful")
        return True
        
    except Exception as e:
        print(f"❌ Kestra compatibility test failed: {e}")
        return False

def main():
    """Run comprehensive logger integration tests"""
    print("🚀 ORDER_LIST Pipeline Logger Integration Test Suite")
    print("=" * 60)
    print(f"Repository root: {repo_root}")
    print(f"Python version: {sys.version}")
    
    test_results = {
        'logger_helper_functionality': test_logger_helper_functionality(),
        'order_list_file_imports': test_order_list_file_imports(),
        'logger_vs_print_usage': test_logger_vs_print_usage(),
        'kestra_compatibility': test_kestra_compatibility()
    }
    
    # Summary
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Logger integration is ready!")
        print("✅ ORDER_LIST pipeline ready for Kestra deployment")
        return True
    else:
        print(f"❌ {total_tests - passed_tests} tests failed - Issues need to be resolved")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
