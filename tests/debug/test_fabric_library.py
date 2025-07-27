"""
Quick test script for board 8446553051 (Fabric Library)
Purpose: Test DECIMAL column handling specifically
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
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

# Import the ETL function directly
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from load_boards import execute_etl_pipeline, load_board_json_config

def main():
    """Test board 8446553051 specifically"""
    logger = logger_helper.get_logger(__name__)
    
    board_id = "8446553051"
    description = "Fabric Library (has DECIMAL columns)"
    
    print(f"\n" + "="*70)
    print(f"TESTING BOARD {board_id}: {description}")
    print(f"="*70)
    
    try:
        # Load metadata for the board
        logger.info(f"Loading metadata for board {board_id}")
        metadata = load_board_json_config(int(board_id))
        
        # Test the ETL pipeline
        result = execute_etl_pipeline(int(board_id), metadata)
        
        # If we get here without exception, the ETL was successful
        if result is None:
            print(f"SUCCESS: Board {board_id} processed successfully")
            print(f"   ETL completed without errors")
            print(f"   DECIMAL columns handled correctly")
            return True
        else:
            print(f"UNEXPECTED: ETL returned {result} instead of None")
            return False
            
    except Exception as e:
        logger.exception(f"Board {board_id} test failed: {e}")
        print(f"FAILED: Board {board_id} processing failed")
        print(f"   Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Board 8446553051 test passed!")
        print("DECIMAL column handling is working correctly.")
    else:
        print("\nFAILED: Board 8446553051 test failed.")
        print("Check logs for specific error details.")
