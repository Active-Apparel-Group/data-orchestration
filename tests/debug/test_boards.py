"""
Test Boards Script: Validate both board 8709134353 and 8446553051
Purpose: Test refactored load_boards.py with both challenging boards
"""
import sys
from pathlib import Path
import logging

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

def test_board(board_id: str, description: str):
    """Test a specific board"""
    logger = logger_helper.get_logger(__name__)
    
    print(f"\n" + "="*60)
    print(f"TESTING BOARD {board_id}: {description}")
    print(f"="*60)
    
    try:
        # Load metadata for the board
        logger.info(f"Loading metadata for board {board_id}")
        metadata = load_board_json_config(int(board_id))
        
        # Test the ETL pipeline
        result = execute_etl_pipeline(int(board_id), metadata)
        
        # If we get here without exception, the ETL was successful
        # (execute_etl_pipeline returns None on success, raises exception on failure)
        if result is None:
            print(f"SUCCESS: Board {board_id} processed successfully")
            print(f"   ETL completed without errors")
            return True
        elif result and result.get('success', False):
            print(f"SUCCESS: Board {board_id} processed successfully")
            print(f"   Rows processed: {result.get('rows_processed', 'Unknown')}")
            print(f"   Processing time: {result.get('processing_time', 'Unknown')}")
            return True
        else:
            print(f"FAILED: Board {board_id} processing failed")
            print(f"   Error: {result.get('error', 'Unknown error') if result else 'Unknown error'}")
            return False
        
    except Exception as e:
        logger.exception(f"Board {board_id} test failed: {e}")
        print(f"EXCEPTION: Board {board_id} failed with exception: {e}")
        return False

def main():
    """Test both challenging boards"""
    logger = logger_helper.get_logger(__name__)
    
    print("BOARD TESTING VALIDATION")
    print("Testing refactored load_boards.py with challenging boards")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        board_id = sys.argv[1]
        if board_id == "8709134353":
            boards_to_test = [("8709134353", "Planning Board (has column duplication)")]
        elif board_id == "8446553051":
            boards_to_test = [("8446553051", "Fabric Library (has DECIMAL columns)")]
        else:
            boards_to_test = [(board_id, f"Board {board_id}")]
    else:
        # Test both boards by default
        boards_to_test = [
            ("8709134353", "Planning Board (has column duplication)"),
            ("8446553051", "Fabric Library (has DECIMAL columns)")
        ]
    
    results = {}
    
    for board_id, description in boards_to_test:
        success = test_board(board_id, description)
        results[board_id] = success
    
    # Summary
    print(f"\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print(f"="*60)
    
    all_passed = True
    for board_id, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"Board {board_id}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\nSUCCESS: All boards processed successfully!")
        print("Refactoring is complete and working.")
    else:
        print("\nFAILED: Some boards failed processing.")
        print("Additional debugging needed.")

if __name__ == "__main__":
    main()
