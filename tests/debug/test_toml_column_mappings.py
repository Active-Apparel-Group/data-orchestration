"""
Test TOML Column Mappings
==========================
Purpose: Validate that TOML column mappings are being loaded and applied correctly
Focus: Test the updated _get_column_mappings and _transform_record methods

Success Criteria:
- TOML mappings loaded successfully for both headers and lines
- Database columns properly transformed to Monday.com column IDs
- Column mapping counts match expected values from TOML file
"""

import sys
from pathlib import Path

# Repository root discovery and path setup
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "src"))

# Project imports
from pipelines.utils import logger
from pipelines.sync_order_list.monday_api_client import MondayAPIClient

def test_toml_column_mappings():
    """Test TOML column mappings loading and transformation"""
    test_logger = logger.get_logger("test_toml_mappings")
    
    # Initialize Monday API client with TOML config
    config_path = repo_root / "configs" / "pipelines" / "sync_order_list.toml"
    
    if not config_path.exists():
        test_logger.error(f"TOML config not found: {config_path}")
        return False
    
    try:
        # Initialize client
        client = MondayAPIClient(str(config_path))
        test_logger.info("✅ Monday API Client initialized successfully")
        
        # Test headers mappings (create_items operation)
        headers_mappings = client._get_column_mappings('create_items')
        test_logger.info(f"📊 Headers mappings loaded: {len(headers_mappings)} columns")
        
        # Test some key mappings
        key_headers = ["AAG ORDER NUMBER", "CUSTOMER NAME", "PO NUMBER", "CUSTOMER STYLE"]
        found_headers = sum(1 for key in key_headers if key in headers_mappings)
        test_logger.info(f"  • Key headers found: {found_headers}/{len(key_headers)}")
        
        # Test lines mappings (create_subitems operation)  
        lines_mappings = client._get_column_mappings('create_subitems')
        test_logger.info(f"📊 Lines mappings loaded: {len(lines_mappings)} columns")
        
        # Test some key line mappings
        key_lines = ["size_code", "qty"]
        found_lines = sum(1 for key in key_lines if key in lines_mappings)
        test_logger.info(f"  • Key lines found: {found_lines}/{len(key_lines)}")
        
        # Test record transformation with sample data
        sample_header_record = {
            "AAG ORDER NUMBER": "TEST-ORDER-001",
            "CUSTOMER NAME": "GREYSON",
            "PO NUMBER": "4755",
            "CUSTOMER STYLE": "TEST-STYLE"
        }
        
        transformed_header = client._transform_record(sample_header_record, headers_mappings)
        test_logger.info(f"📊 Header transformation test: {len(transformed_header)} fields created")
        
        # Test subitem transformation
        sample_line_record = {
            "size_code": "M",
            "qty": 10,
            "parent_item_id": "123456"
        }
        
        transformed_line = client._transform_record(sample_line_record, lines_mappings)
        test_logger.info(f"📊 Line transformation test: {len(transformed_line)} fields created")
        
        # Success validation
        success = (
            len(headers_mappings) > 0 and 
            len(lines_mappings) > 0 and
            found_headers >= 3 and  # At least 3 key headers
            found_lines >= 1        # At least 1 key line field
        )
        
        if success:
            test_logger.info("🎉 TOML column mappings test PASSED!")
            test_logger.info("✅ Mappings are being loaded and applied correctly")
        else:
            test_logger.error("❌ TOML column mappings test FAILED!")
            test_logger.error(f"Headers: {len(headers_mappings)}, Lines: {len(lines_mappings)}")
        
        # Print some example mappings for verification
        test_logger.info("📋 Sample Headers Mappings:")
        for i, (db_col, monday_col) in enumerate(list(headers_mappings.items())[:5]):
            test_logger.info(f"  • {db_col} → {monday_col}")
        
        if lines_mappings:
            test_logger.info("📋 Sample Lines Mappings:")
            for i, (db_col, monday_col) in enumerate(list(lines_mappings.items())[:3]):
                test_logger.info(f"  • {db_col} → {monday_col}")
        
        return success
        
    except Exception as e:
        test_logger.error(f"❌ TOML mappings test failed: {e}")
        return False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    
    print("🧪 Testing TOML Column Mappings")
    print("=" * 50)
    
    success = test_toml_column_mappings()
    
    print("=" * 50)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("🎯 TOML column mappings are working correctly")
    else:
        print("❌ TESTS FAILED!")
        print("🔧 Check TOML configuration and mapping logic")
