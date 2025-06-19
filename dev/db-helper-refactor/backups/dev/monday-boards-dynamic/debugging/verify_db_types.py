#!/usr/bin/env python3
"""
Verify the data types in the production database
"""

# Standard repository root finding pattern
import sys
from pathlib import Path

def find_repo_root() -> Path:
    """Find repository root by looking for marker files"""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in ['.git', 'pyproject.toml', 'requirements.txt']):
            return parent
    return current.parent

# Add utils to path for consistent imports
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

# Initialize logger
logger = logger_helper.get_logger("verify_db_types")

def verify_database_types():
    # First, check what columns exist
    columns_query = """
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'MON_Customer_Master_Schedule'
    ORDER BY ORDINAL_POSITION
    """
    
    columns_result = db.run_query(columns_query, 'orders')
    logger.info('Columns in MON_Customer_Master_Schedule table:')
    for _, row in columns_result.iterrows():
        logger.info(f'  {row["COLUMN_NAME"]} ({row["DATA_TYPE"]})')
    
    logger.info('\n' + '='*50)
    
    # Then get sample data from key columns
    result = db.run_query('SELECT TOP 3 [Item ID], [CUSTOMER PRICE], [FINAL FOB (USD)] FROM MON_Customer_Master_Schedule', 'orders')
    logger.info('Sample data from production table:')
    
    for i, (_, row) in enumerate(result.iterrows()):
        logger.info(f'Record {i+1}:')
        logger.info(f'  Item ID: {row["Item ID"]} (type: {type(row["Item ID"])})')
        logger.info(f'  Customer Price: {row["CUSTOMER PRICE"]} (type: {type(row["CUSTOMER PRICE"])})')
        logger.info(f'  Final FOB: {row["FINAL FOB (USD)"]} (type: {type(row["FINAL FOB (USD)"])})')
        logger.info('---')

if __name__ == "__main__":
    verify_database_types()
