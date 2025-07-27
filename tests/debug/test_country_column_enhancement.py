"""
Test Country Column Enhancement for Monday.com Update Scripts
Purpose: Validate country column type detection and formatting
Date: 2025-07-15
"""
import sys
from pathlib import Path
import pandas as pd

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "update"))

import logger_helper

# Test imports
try:
    from update_boards import UniversalMondayUpdater
    from update_boards_batch import BatchMondayUpdater
    from country_mapper import format_country_for_monday, COUNTRY_CODES
    print("✅ Successfully imported enhanced update scripts")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_country_mapping():
    """Test country code mapping functionality"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🧪 Testing Country Code Mapping")
    
    # Test cases
    test_countries = ['Cambodia', 'Vietnam', 'China', 'Unknown Country', None, '']
    
    updater = UniversalMondayUpdater()
    
    for country in test_countries:
        result = updater.format_country_value(country)
        logger.info(f"Country: '{country}' → {result}")
    
    # Test Cambodia specifically (the failing case)
    cambodia_result = updater.format_country_value('Cambodia')
    expected = {"countryCode": "KH", "countryName": "Cambodia"}
    
    if cambodia_result == expected:
        logger.info("✅ Cambodia country formatting PASSED")
        return True
    else:
        logger.error(f"❌ Cambodia country formatting FAILED. Expected: {expected}, Got: {cambodia_result}")
        return False

def test_column_type_detection():
    """Test column type detection from board metadata"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🧪 Testing Column Type Detection")
    
    try:
        updater = UniversalMondayUpdater()
        
        # Load board metadata for board 8709134353
        metadata = updater.load_board_metadata(8709134353)
        
        # Test country column detection
        country_column_type = updater.detect_column_type('country_mksv4c5v', metadata)
        
        if country_column_type == 'country':
            logger.info("✅ Country column type detection PASSED")
            
            # Test formatting with the metadata
            test_value = 'Cambodia'
            formatted = updater.format_column_value('country_mksv4c5v', test_value, metadata)
            expected = {"countryCode": "KH", "countryName": "Cambodia"}
            
            if formatted == expected:
                logger.info("✅ Country column formatting with metadata PASSED")
                return True
            else:
                logger.error(f"❌ Country column formatting FAILED. Expected: {expected}, Got: {formatted}")
                return False
        else:
            logger.error(f"❌ Column type detection FAILED. Expected: 'country', Got: '{country_column_type}'")
            return False
            
    except Exception as e:
        logger.error(f"❌ Column type detection test FAILED with error: {e}")
        return False

def test_batch_updater():
    """Test batch updater country functionality"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🧪 Testing Batch Updater Country Functionality")
    
    try:
        # Note: We can't test with actual config file, so just test the class instantiation
        # and method availability
        batch_updater = BatchMondayUpdater()
        
        # Test if methods exist
        if hasattr(batch_updater, 'format_country_value'):
            # Test Cambodia formatting
            cambodia_result = batch_updater.format_country_value('Cambodia')
            expected = {"countryCode": "KH", "countryName": "Cambodia"}
            
            if cambodia_result == expected:
                logger.info("✅ Batch updater country formatting PASSED")
                return True
            else:
                logger.error(f"❌ Batch updater formatting FAILED. Expected: {expected}, Got: {cambodia_result}")
                return False
        else:
            logger.error("❌ Batch updater missing format_country_value method")
            return False
            
    except Exception as e:
        logger.error(f"❌ Batch updater test FAILED with error: {e}")
        return False

def main():
    """Run all country column enhancement tests"""
    logger = logger_helper.get_logger(__name__)
    logger.info("🚀 Starting Country Column Enhancement Tests")
    
    tests = [
        ("Country Mapping", test_country_mapping),
        ("Column Type Detection", test_column_type_detection),
        ("Batch Updater", test_batch_updater)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 ALL TESTS PASSED - Country column enhancement is working!")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Need to fix issues before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
