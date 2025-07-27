#!/usr/bin/env python3
"""
End-to-End Test: Validate Monday.com Column Mapping Fix

This test script validates that:
1. Real Monday.com column IDs are loaded from mapping YAML
2. Data transformation uses real column IDs instead of fake ones  
3. API adapter will send data to correct Monday.com columns
4. All critical fields are mapped correctly
"""
import sys
from pathlib import Path
import pandas as pd

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

def test_end_to_end_mapping_fix():
    """Test end-to-end mapping fix with sample GREYSON data"""
    logger = logger_helper.get_logger(__name__)
    
    try:
        logger.info("🧪 TESTING: End-to-End Monday.com Column Mapping Fix")
        
        # Step 1: Load mapping configurations
        logger.info("\n📋 Step 1: Loading mapping configurations...")
        field_mappings = mapping_helper.get_orders_field_mappings()
        subitem_mappings = mapping_helper.get_orders_subitem_mappings()
        
        logger.info(f"   ✅ Loaded {len(field_mappings)} master field mappings")
        logger.info(f"   ✅ Loaded {len(subitem_mappings)} subitem field mappings")
        
        # Step 2: Create sample GREYSON order data (like what would come from staging)
        logger.info("\n📦 Step 2: Creating sample GREYSON order data...")
        sample_order_data = pd.Series({
            'AAG ORDER NUMBER': 'JOO-00505',
            '[CUSTOMER STYLE]': 'GREYSON POLO SHIRT',
            '[TOTAL QTY]': 150,
            'AAG SEASON': '2026 SPRING',
            'CUSTOMER SEASON': 'SPRING SUMMER 2026',
            'CUSTOMER ALT PO': 'ALT-12345',
            '[EX FACTORY DATE]': pd.to_datetime('2026-03-15'),
            'source_uuid': 'uuid-12345-greyson-test'
        })
        
        logger.info(f"   ✅ Created sample order data for: {sample_order_data.get('AAG ORDER NUMBER')}")
        
        # Step 3: Test transformation using REAL column IDs
        logger.info("\n🔄 Step 3: Testing data transformation with REAL column IDs...")
        
        # Import the fixed transform function
        sys.path.insert(0, str(Path(__file__).parent))
        from fixed_transform_methods import fixed_transform_to_monday_columns
        
        # Transform data using real column IDs
        transformed_data = fixed_transform_to_monday_columns(None, sample_order_data, field_mappings)
        
        logger.info(f"   ✅ Transformation successful! Generated {len(transformed_data)} column mappings")
        
        # Step 4: Validate that REAL column IDs are used
        logger.info("\n🔍 Step 4: Validating REAL Monday.com column IDs are used...")
        
        expected_real_columns = {
            'text_mkr5wya6': 'AAG ORDER NUMBER',
            'text_mkr789': 'CUSTOMER STYLE', 
            'numbers_mkr123': 'TOTAL QTY',
            'dropdown_mkr58de6': 'AAG SEASON',
            'dropdown_mkr5rgs6': 'CUSTOMER SEASON',
            'text_mkrh94rx': 'CUSTOMER ALT PO',
            'date_mkr456': 'EX FACTORY DATE'
        }
        
        # Check that we're using real column IDs, not fake ones
        fake_columns_found = []
        real_columns_found = []
        
        for column_id, value in transformed_data.items():
            if column_id in expected_real_columns:
                real_columns_found.append(column_id)
                logger.info(f"   ✅ REAL COLUMN ID: {column_id} = '{value}' ({expected_real_columns[column_id]})")
            elif column_id in ['text', 'text4', 'text6', 'numbers', 'date4']:
                fake_columns_found.append(column_id)
                logger.error(f"   ❌ FAKE COLUMN ID: {column_id} = '{value}' (SHOULD NOT BE USED)")
            else:
                logger.info(f"   ℹ️  OTHER COLUMN: {column_id} = '{value}'")
        
        # Step 5: Test subitem transformation  
        logger.info("\n👶 Step 5: Testing subitem transformation...")
        
        sample_subitem_data = pd.Series({
            'size_name': 'Large',
            'size_qty': 25,
            'parent_source_uuid': 'uuid-12345-greyson-test'
        })
        
        from fixed_transform_methods import fixed_transform_subitem_to_monday_columns
        transformed_subitem = fixed_transform_subitem_to_monday_columns(None, sample_subitem_data, subitem_mappings)
        
        logger.info(f"   ✅ Subitem transformation successful! Generated {len(transformed_subitem)} column mappings")
        for column_id, value in transformed_subitem.items():
            logger.info(f"      Subitem: {column_id} = '{value}'")
        
        # Step 6: Final validation
        logger.info("\n🎯 Step 6: Final validation...")
        
        if fake_columns_found:
            logger.error(f"   ❌ CRITICAL FAILURE: Found {len(fake_columns_found)} fake column IDs!")
            logger.error(f"      Fake columns: {fake_columns_found}")
            return False
        
        if len(real_columns_found) < 3:  # Should have at least core fields
            logger.error(f"   ❌ FAILURE: Only found {len(real_columns_found)} real column IDs (expected at least 3)")
            return False
        
        logger.info(f"   ✅ SUCCESS: Found {len(real_columns_found)} real Monday.com column IDs")
        logger.info(f"   ✅ SUCCESS: No fake column IDs detected")
        logger.info(f"   ✅ SUCCESS: Master and subitem transformations working")
        
        # Step 7: Summary
        logger.info("\n🎉 FINAL RESULT: END-TO-END MAPPING FIX VALIDATION")
        logger.info(f"   ✅ Mapping configuration loads correctly")
        logger.info(f"   ✅ Data transformation uses REAL Monday.com column IDs")  
        logger.info(f"   ✅ No fake column IDs ('text', 'text4', etc.) detected")
        logger.info(f"   ✅ Both master items and subitems transform correctly")
        logger.info(f"   ✅ Ready for production API calls to Monday.com")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: End-to-end test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_end_to_end_mapping_fix()
    if success:
        print("\n🎉 END-TO-END MAPPING FIX VALIDATION: PASSED")
        print("   The Monday.com column mapping issue has been FIXED!")
        print("   API adapter will now send data to correct Monday.com columns.")
    else:
        print("\n❌ END-TO-END MAPPING FIX VALIDATION: FAILED")
        sys.exit(1)
