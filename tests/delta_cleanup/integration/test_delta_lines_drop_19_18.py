#!/usr/bin/env python3
"""
TASK 19.18 - ORDER_LIST_LINES_DELTA Table Safe Removal
Execute safe removal of ORDER_LIST_LINES_DELTA table following same pattern as 19.17
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("TASK 19.18 - ORDER_LIST_LINES_DELTA Table Safe Removal")
    print("=" * 60)
    
    # Config FIRST (following project pattern)
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using 'orders' key
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        print("Phase 1: Pre-removal Validation")
        print("-" * 30)
        
        # Verify table exists
        cursor.execute("""
        SELECT CASE WHEN EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ORDER_LIST_LINES_DELTA'
        ) THEN 'EXISTS' ELSE 'NOT FOUND' END as table_status
        """)
        status = cursor.fetchone()[0]
        
        if status == 'NOT FOUND':
            print("ORDER_LIST_LINES_DELTA table NOT FOUND - already removed")
            print("TASK 19.18: ALREADY COMPLETE")
            return
            
        # Check table contents and dependencies
        cursor.execute('SELECT COUNT(*) FROM ORDER_LIST_LINES_DELTA')
        count = cursor.fetchone()[0]
        
        # Check for foreign key dependencies
        cursor.execute("""
        SELECT COUNT(*) as fk_count
        FROM sys.foreign_keys fk
        INNER JOIN sys.objects o ON fk.parent_object_id = o.object_id
        WHERE o.name = 'ORDER_LIST_LINES_DELTA'
        """)
        fks = cursor.fetchone()[0]
        
        print(f"Row Count: {count:,}")
        print(f"Foreign Key Dependencies: {fks}")
        
        if count > 0:
            print(f"WARNING: Table contains {count:,} rows")
            print("ABORTING: Table not empty - manual review required")
            return
            
        if fks > 0:
            print(f"WARNING: Table has {fks} foreign key dependencies")
            print("ABORTING: Dependencies must be removed first")
            return
            
        print("Table exists and is empty with no dependencies - SAFE TO PROCEED")
        
        print("\nPhase 2: Safe Table Removal")
        print("-" * 30)
        
        try:
            # Drop the table
            cursor.execute("DROP TABLE ORDER_LIST_LINES_DELTA")
            connection.commit()
            print("SUCCESS: ORDER_LIST_LINES_DELTA table dropped successfully")
            
            # Verify removal
            cursor.execute("""
            SELECT CASE WHEN EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ORDER_LIST_LINES_DELTA'
            ) THEN 'EXISTS' ELSE 'NOT FOUND' END as table_status
            """)
            verify_status = cursor.fetchone()[0]
            
            if verify_status == 'NOT FOUND':
                print("VERIFIED: Table successfully removed from database")
                print("TASK 19.18: COMPLETE")
                print("\nDELTA CLEANUP SUMMARY:")
                print("-" * 30)
                print("TASK 19.17: ORDER_LIST_DELTA - REMOVED")
                print("TASK 19.18: ORDER_LIST_LINES_DELTA - REMOVED")
                print("DELTA ARCHITECTURE: FULLY ELIMINATED")
            else:
                print("ERROR: Table still exists after drop command")
                
        except Exception as e:
            print(f"ERROR during table drop: {e}")
            connection.rollback()
            print("ROLLED BACK: No changes made to database")
            
        cursor.close()

if __name__ == "__main__":
    main()
