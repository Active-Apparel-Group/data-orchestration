"""
Test File Discovery Only
Purpose: Test finding ORDER_LIST files without blob upload
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
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "load_order_list"))

import logger_helper

def test_file_discovery():
    """Test file discovery only (no upload)"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing ORDER_LIST file discovery...")
    
    try:
        from order_list_blob import OrderListBlobUploader
        import auth_helper
        
        logger.info("Creating uploader instance...")
        uploader = OrderListBlobUploader()
        
        logger.info("Getting authentication token...")
        token = auth_helper.get_token()
        if not token:
            logger.error("FAIL: Could not get authentication token")
            return False
        
        uploader.headers = {"Authorization": f"Bearer {token}"}
        logger.info("SUCCESS: Authentication configured")
        
        # Test discovery for one region only (USA CUSTOMERS)
        DRIVE_ID = "b!Aw3US9PgWEqI3AsHsnFh4VDpZqG7xMZFvusMriy0vjlVvmF4ME5wR6vdOy90ye56"
        
        logger.info("Testing file discovery for USA CUSTOMERS region...")
        uploader.find_and_accumulate_files(
            DRIVE_ID, 
            "USA CUSTOMERS", 
            "01TP4AHIF77VK3XMDH4BHYQUXVCLJD62AU", 
            depth=0
        )
        
        logger.info(f"Found {len(uploader.results)} ORDER_LIST files")
        
        if uploader.results:
            logger.info("Files discovered:")
            for i, file_info in enumerate(uploader.results, 1):
                # Test the new blob naming convention (just filename)
                blob_name = file_info['FileName']
                logger.info(f"  {i}. {file_info['Region']}/{file_info['Subfolder']}/{file_info['FileName']}")
                logger.info(f"     Will be saved as: {blob_name}")
                logger.info(f"     Size: {file_info.get('Size', 0)} bytes")
                logger.info(f"     Modified: {file_info.get('LastModified', 'Unknown')}")
            return True
        else:
            logger.warning("No ORDER_LIST files found")
            return False
        
    except Exception as e:
        logger.error(f"FAIL: File discovery error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Test file discovery"""
    logger = logger_helper.get_logger(__name__)
    logger.info("=== ORDER_LIST File Discovery Test ===")
    
    success = test_file_discovery()
    
    if success:
        logger.info("SUCCESS: File discovery test passed!")
        logger.info("Ready to test blob upload.")
    else:
        logger.error("FAIL: File discovery test failed.")
        logger.error("Fix issues before proceeding.")

if __name__ == "__main__":
    main()
