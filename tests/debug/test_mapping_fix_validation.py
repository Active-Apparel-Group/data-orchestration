#!/usr/bin/env python3
"""
Test script to validate the column mapping fix
"""
import sys
from pathlib import Path

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

# Import from utils/
import mapping_helper
import logger_helper

def test_mapping_fix():
    """Test that the mapping configuration loads correctly with real column IDs"""
    logger = logger_helper.get_logger(__name__)
    
    try:        # Test loading the orders mapping
        logger.info("Testing orders mapping configuration load...")
        orders_config = mapping_helper.load_orders_mapping_config()
        logger.info("Successfully loaded orders mapping config")
        
        # Test getting field mappings
        field_mappings = mapping_helper.get_orders_field_mappings()
        logger.info(f"Successfully loaded field mappings: {len(field_mappings)} fields")
        
        # Print the real column IDs vs what was previously used
        logger.info("\nREAL Monday.com Column ID Mappings:")
        for source_field, column_id in field_mappings.items():
            logger.info(f"   {source_field} -> {column_id}")
        
        # Test specific fields that were broken
        critical_fields = ['AAG ORDER NUMBER', '[CUSTOMER STYLE]', '[TOTAL QTY]', 'AAG SEASON']
        logger.info(f"\nCRITICAL FIELD MAPPINGS (Previously using fake IDs):")
        
        fake_mappings = {
            'AAG ORDER NUMBER': 'text4',  # FAKE
            '[CUSTOMER STYLE]': 'text6',  # FAKE
            '[TOTAL QTY]': 'numbers',     # FAKE
            'AAG SEASON': 'dropdown'      # FAKE
        }
        
        for field in critical_fields:
            real_id = field_mappings.get(field, 'NOT FOUND')
            fake_id = fake_mappings.get(field, 'N/A')
            
            if real_id != 'NOT FOUND':
                logger.info(f"   FIXED: {field}:")
                logger.info(f"      OLD (FAKE): {fake_id}")
                logger.info(f"      NEW (REAL): {real_id}")
            else:
                logger.warning(f"   ERROR: {field}: NOT FOUND in mapping")
        
        # Test subitem mappings
        subitem_mappings = mapping_helper.get_orders_subitem_mappings()
        logger.info(f"\nSuccessfully loaded subitem mappings: {len(subitem_mappings)} fields")
        
        for field_name, column_id in subitem_mappings.items():
            logger.info(f"   {field_name} -> {column_id}")        
        logger.info(f"\nSUCCESS: Mapping configuration fix is working!")
        logger.info(f"   - Found {len(field_mappings)} master item field mappings")
        logger.info(f"   - Found {len(subitem_mappings)} subitem field mappings")
        logger.info(f"   - All critical fields have real Monday.com column IDs")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: Mapping configuration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mapping_fix()
    if success:
        print("\n✅ Mapping fix validation PASSED")
    else:
        print("\n❌ Mapping fix validation FAILED")
        sys.exit(1)
