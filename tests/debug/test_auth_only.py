"""
Test Authentication for ORDER_LIST Blob Uploader
Purpose: Test Microsoft Graph authentication interactively
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

import logger_helper
import auth_helper

def test_authentication():
    """Test Microsoft Graph authentication"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing Microsoft Graph authentication...")
    
    try:
        logger.info("Attempting to get Microsoft Graph token...")
        logger.info("This may require browser authentication...")
        
        token = auth_helper.get_token()
        
        if token:
            logger.info("SUCCESS: Authentication token acquired")
            logger.info(f"Token length: {len(token)} characters")
            logger.info(f"Token starts with: {token[:20]}...")
            return True
        else:
            logger.error("FAIL: No token returned")
            return False
            
    except Exception as e:
        logger.error(f"FAIL: Authentication error: {e}")
        return False

def main():
    """Test authentication"""
    logger = logger_helper.get_logger(__name__)
    logger.info("=== ORDER_LIST Authentication Test ===")
    
    success = test_authentication()
    
    if success:
        logger.info("SUCCESS: Authentication test passed!")
        logger.info("Ready to test file discovery and upload.")
    else:
        logger.error("FAIL: Authentication test failed.")
        logger.error("Fix authentication before proceeding.")

if __name__ == "__main__":
    main()
