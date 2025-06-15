"""
Test script for Monday.com Board Groups Sync
============================================

This script tests the sync_board_groups functionality.

Usage:
    python test_sync.py [board_id]
    
Example:
    python test_sync.py 9200517329
"""

import sys
import os
import warnings
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

from sync_board_groups import MondayBoardGroupsSync


def test_sync(board_id='9200517329'):
    """Test the board groups sync"""
    try:
        print(f"[INFO] Testing board groups sync for board: {board_id}")
        syncer = MondayBoardGroupsSync(board_id)
        syncer.sync_board_groups()
        print("✅ Board groups sync completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Board groups sync failed: {e}")
        return False


def main():
    """Main entry point"""
    board_id = sys.argv[1] if len(sys.argv) > 1 else '9200517329'
    
    print("="*60)
    print("Monday.com Board Groups Sync Test")
    print("="*60)
    
    success = test_sync(board_id)
    
    print("="*60)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    test_sync()
