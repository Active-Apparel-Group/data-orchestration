#!/usr/bin/env python3
"""
Standard Import Template for Data Orchestration Scripts
Use this template for all new scripts and apply to existing scripts during refactoring

This template implements the standardized repository root finding pattern
and consistent utils module importing across all scripts.
"""

import sys
import os
from pathlib import Path

# NEW STANDARD: Find repository root, then find utils (Option 2)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path using repository root method
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import centralized modules
import db_helper as db
import logger_helper
import mapping_helper as mapping

# Initialize logger with script-specific name
# Replace "script_name" with actual script purpose (e.g., "monday_planning_etl", "order_sync", etc.)
logger = logger_helper.get_logger("script_name")

# Load configuration from centralized config
config = db.load_config()

# Example usage patterns:

# For Monday.com board scripts:
# board_config = mapping.get_board_config('board_name')
# BOARD_ID = int(board_config['board_id'])
# TABLE_NAME = board_config['table_name']
# DATABASE_NAME = board_config['database']

# For database operations:
# conn = db.get_connection(DATABASE_NAME)
# result = db.run_query(query, DATABASE_NAME)
# db.execute(sql, DATABASE_NAME)

# For logging:
# logger.info("Starting script execution")
# logger.error("Error occurred: %s", error_message)
# logger.debug("Debug information")

def main():
    """Main script function"""
    logger.info("Script started")
    
    try:
        # Your script logic here
        logger.info("Script logic goes here")
        
        logger.info("Script completed successfully")
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()
