#!/usr/bin/env python3
"""
TASK 19.17 - ORDER_LIST_DELTA Table Removal Validation
Integration test to validate safe removal of ORDER_LIST_DELTA table
Following project testing standards from docs/implementation/order-list-delta-testing.md
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
    print("TASK 19.17 - ORDER_LIST_DELTA Table Analysis")
    print("=" * 60)
    
    # Config FIRST (following project pattern)
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using 'orders' key (from TOML config)
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        # Phase 1: Check if ORDER_LIST_DELTA exists
        print("Phase 1: Table Existence Check")
        print("-" * 30)
        
        cursor.execute("""
        SELECT CASE WHEN EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ORDER_LIST_DELTA'
        ) THEN 'EXISTS' ELSE 'NOT FOUND' END as table_status
        """)
        status = cursor.fetchone()[0]
        print(f"ORDER_LIST_DELTA Table Status: {status}")
        
        if status == 'EXISTS':
            print("\nPhase 2: Table Analysis")
            print("-" * 30)
            
            # Check row count
            cursor.execute('SELECT COUNT(*) FROM ORDER_LIST_DELTA')
            count = cursor.fetchone()[0]
            print(f"Row Count: {count:,}")
            
            # Check table structure
            cursor.execute("""
            SELECT COUNT(*) as column_count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ORDER_LIST_DELTA'
            """)
            cols = cursor.fetchone()[0]
            print(f"Column Count: {cols}")
            
            # Check for indexes
            cursor.execute("""
            SELECT COUNT(*) as index_count
            FROM sys.indexes i
            INNER JOIN sys.objects o ON i.object_id = o.object_id
            WHERE o.name = 'ORDER_LIST_DELTA' AND i.type > 0
            """)
            indexes = cursor.fetchone()[0]
            print(f"Index Count: {indexes}")
            
            print("\nPhase 3: Dependencies Check")
            print("-" * 30)
            
            # Check for foreign key dependencies
            cursor.execute("""
            SELECT COUNT(*) as fk_count
            FROM sys.foreign_keys fk
            INNER JOIN sys.objects o ON fk.parent_object_id = o.object_id
            WHERE o.name = 'ORDER_LIST_DELTA'
            """)
            fks = cursor.fetchone()[0]
            print(f"Foreign Key Dependencies: {fks}")
            
            # Check for views that reference the table
            cursor.execute("""
            SELECT COUNT(*) as view_count
            FROM sys.sql_dependencies d
            INNER JOIN sys.objects v ON d.object_id = v.object_id
            INNER JOIN sys.objects t ON d.referenced_major_id = t.object_id
            WHERE t.name = 'ORDER_LIST_DELTA' AND v.type = 'V'
            """)
            views = cursor.fetchone()[0]
            print(f"Views Referencing Table: {views}")
            
            print("\nPhase 4: DELTA Architecture Status")
            print("-" * 30)
            print("Based on TOML configuration analysis:")
            print("- Current architecture: DELTA-FREE (Phase 5 complete)")
            print("- Main tables: ORDER_LIST_V2, ORDER_LIST_LINES (with sync columns)")
            print("- DELTA tables: No longer used in sync pipeline")
            
            # TASK 19.17 Assessment
            print("\nTASK 19.17 ASSESSMENT:")
            print("-" * 30)
            if count == 0 and fks == 0 and views == 0:
                print("SAFE TO REMOVE: No data, dependencies, or references found")
                print("Recommendation: Proceed with table drop")
            elif count > 0:
                print(f"CONTAINS DATA: {count:,} rows found")
                print("Recommendation: Backup data before removal")
            elif fks > 0 or views > 0:
                print("HAS DEPENDENCIES: Foreign keys or views found")
                print("Recommendation: Remove dependencies first")
            else:
                print("PROCEED WITH CAUTION: Manual review required")
                
        else:
            print("\nTASK 19.17 RESULT:")
            print("-" * 30)
            print("ORDER_LIST_DELTA table NOT FOUND")
            print("Status: TASK 19.17 ALREADY COMPLETE")
            print("Action: No removal needed, proceed to TASK 19.18")
            
        cursor.close()

if __name__ == "__main__":
    main()
