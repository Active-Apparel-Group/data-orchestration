#!/usr/bin/env python3
"""
PLAN MODE: Schema Discovery for Group ID Analysis
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🔍 PLAN MODE: Schema Discovery for Group ID Analysis...")
    
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        # Check FACT_ORDER_LIST schema
        print("\n📋 FACT_ORDER_LIST Schema Analysis...")
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'FACT_ORDER_LIST'
            AND COLUMN_NAME LIKE '%group%'
            ORDER BY ORDINAL_POSITION
        """)
        
        group_columns = cursor.fetchall()
        print(f"Found {len(group_columns)} group-related columns:")
        for col in group_columns:
            print(f"  - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        # Check for monday-related columns
        print("\n📋 Monday.com Related Columns...")
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'FACT_ORDER_LIST'
            AND (COLUMN_NAME LIKE '%monday%' OR COLUMN_NAME LIKE '%group%id%')
            ORDER BY COLUMN_NAME
        """)
        
        monday_columns = cursor.fetchall()
        print(f"Found {len(monday_columns)} Monday.com related columns:")
        for col in monday_columns:
            print(f"  - {col[0]}")
        
        cursor.close()

if __name__ == "__main__":
    main()
