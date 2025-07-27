#!/usr/bin/env python3
"""
TASK 19.17 - ORDER_LIST_DELTA Table Safe Removal
Integration test for validating and safely removing ORDER_LIST_DELTA table
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    """
    TASK 19.17: Safe removal of ORDER_LIST_DELTA table
    
    Steps:
    1. Validate table exists and get current state
    2. Check for dependencies and recent activity
    3. Assess safe removal readiness
    4. Provide removal recommendations
    """
    
    print("🔍 TASK 19.17 - ORDER_LIST_DELTA Table Safe Removal")
    print("=" * 65)
    
    try:
        # Database connection using our established pattern
        with db.get_connection('dms') as connection:
            cursor = connection.cursor()
            
            # Phase 1: Table Existence and Structure Analysis
            print("\n📊 PHASE 1: Table Analysis")
            print("-" * 40)
            
            # Check if ORDER_LIST_DELTA exists
            cursor.execute("""
            SELECT CASE WHEN EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ORDER_LIST_DELTA'
            ) THEN 'EXISTS' ELSE 'NOT FOUND' END as table_status
            """)
            status = cursor.fetchone()[0]
            print(f"📊 ORDER_LIST_DELTA Table Status: {status}")
            
            if status != 'EXISTS':
                print("✅ Table not found - nothing to remove!")
                return
            
            # Get row count
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_DELTA")
            count = cursor.fetchone()[0]
            print(f"📈 Current Row Count: {count:,}")
            
            # Get column count
            cursor.execute("""
            SELECT COUNT(*) as column_count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ORDER_LIST_DELTA'
            """)
            cols = cursor.fetchone()[0]
            print(f"📋 Column Count: {cols}")
            
            # Phase 2: Dependency Analysis
            print("\n🔍 PHASE 2: Dependency Analysis")
            print("-" * 40)
            
            # Check for foreign key references
            cursor.execute("""
            SELECT 
                fk.name AS foreign_key_name,
                OBJECT_NAME(fk.parent_object_id) AS referencing_table,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS referencing_column,
                OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            WHERE OBJECT_NAME(fk.referenced_object_id) = 'ORDER_LIST_DELTA'
               OR OBJECT_NAME(fk.parent_object_id) = 'ORDER_LIST_DELTA'
            """)
            
            fk_deps = cursor.fetchall()
            if fk_deps:
                print(f"⚠️  Found {len(fk_deps)} foreign key dependencies:")
                for dep in fk_deps:
                    print(f"   - {dep[1]}.{dep[2]} → {dep[3]}.{dep[4]} ({dep[0]})")
            else:
                print("✅ No foreign key dependencies found")
            
            # Check for views that reference the table
            cursor.execute("""
            SELECT DISTINCT 
                v.name AS view_name,
                v.type_desc AS object_type
            FROM sys.views v
            INNER JOIN sys.sql_dependencies d ON v.object_id = d.object_id
            INNER JOIN sys.objects o ON d.referenced_major_id = o.object_id
            WHERE o.name = 'ORDER_LIST_DELTA'
            """)
            
            view_deps = cursor.fetchall()
            if view_deps:
                print(f"⚠️  Found {len(view_deps)} view dependencies:")
                for dep in view_deps:
                    print(f"   - {dep[0]} ({dep[1]})")
            else:
                print("✅ No view dependencies found")
                
            # Phase 3: Recent Activity Analysis
            print("\n📅 PHASE 3: Activity Analysis")
            print("-" * 40)
            
            # Check for recent modifications
            cursor.execute("""
            SELECT 
                modify_date,
                create_date,
                DATEDIFF(day, modify_date, GETDATE()) as days_since_modified
            FROM sys.tables 
            WHERE name = 'ORDER_LIST_DELTA'
            """)
            
            activity = cursor.fetchone()
            if activity:
                print(f"📅 Created: {activity[1]}")
                print(f"📅 Last Modified: {activity[0]}")
                print(f"📊 Days Since Modified: {activity[2]}")
            
            # Check index usage statistics
            cursor.execute("""
            SELECT 
                i.name as index_name,
                us.last_user_seek,
                us.last_user_scan,
                us.last_user_lookup,
                us.user_seeks + us.user_scans + us.user_lookups as total_usage
            FROM sys.indexes i
            LEFT JOIN sys.dm_db_index_usage_stats us ON i.object_id = us.object_id AND i.index_id = us.index_id
            WHERE i.object_id = OBJECT_ID('ORDER_LIST_DELTA')
            AND i.index_id > 0
            """)
            
            index_usage = cursor.fetchall()
            if index_usage:
                print(f"📊 Index Usage Analysis:")
                total_usage = sum(idx[4] or 0 for idx in index_usage)
                print(f"   - Total Index Usage: {total_usage}")
                for idx in index_usage:
                    if idx[4] and idx[4] > 0:
                        print(f"   - {idx[0]}: {idx[4]} operations")
            else:
                print("✅ No index usage detected")
            
            # Phase 4: Safety Assessment
            print("\n🔒 PHASE 4: Safety Assessment")
            print("-" * 40)
            
            safe_to_remove = True
            removal_blockers = []
            
            if fk_deps:
                safe_to_remove = False
                removal_blockers.append(f"{len(fk_deps)} foreign key dependencies")
                
            if view_deps:
                safe_to_remove = False
                removal_blockers.append(f"{len(view_deps)} view dependencies")
                
            if activity and activity[2] < 7:  # Modified within last 7 days
                safe_to_remove = False
                removal_blockers.append("Recent modifications detected")
                
            if total_usage > 0:
                safe_to_remove = False
                removal_blockers.append("Recent index usage detected")
            
            # Final Assessment
            print("\n🎯 FINAL ASSESSMENT")
            print("=" * 65)
            
            if safe_to_remove:
                print("✅ SAFE TO REMOVE")
                print("📋 Recommended Actions:")
                print("   1. Create backup of current table structure")
                print("   2. Execute DROP TABLE ORDER_LIST_DELTA")
                print("   3. Monitor system for 24-48 hours")
                print("   4. Update documentation")
                
                # Generate removal script
                print("\n🛠️  Removal Script:")
                print("-" * 40)
                print("-- TASK 19.17: ORDER_LIST_DELTA Safe Removal")
                print("-- Generated:", "GETDATE()")
                print("")
                print("-- Step 1: Backup table structure")
                print("SELECT * INTO ORDER_LIST_DELTA_BACKUP_20250728 FROM ORDER_LIST_DELTA WHERE 1=0;")
                print("")
                print("-- Step 2: Safe removal")
                print("DROP TABLE ORDER_LIST_DELTA;")
                print("")
                print("-- Step 3: Verification")
                print("SELECT CASE WHEN EXISTS (")
                print("    SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ORDER_LIST_DELTA'")
                print(") THEN 'STILL EXISTS' ELSE 'SUCCESSFULLY REMOVED' END;")
                
            else:
                print("⚠️  NOT SAFE TO REMOVE")
                print("🚫 Removal Blockers:")
                for blocker in removal_blockers:
                    print(f"   - {blocker}")
                print("\n📋 Required Actions Before Removal:")
                if fk_deps:
                    print("   - Remove or modify foreign key constraints")
                if view_deps:
                    print("   - Update or remove dependent views")
                if activity and activity[2] < 7:
                    print("   - Wait for modification cool-down period")
                if total_usage > 0:
                    print("   - Identify and stop processes using the table")
            
            cursor.close()
            
    except Exception as e:
        logger.error(f"Error during DELTA table analysis: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False
    
    print(f"\n🎉 TASK 19.17 Analysis Complete")
    return True

if __name__ == "__main__":
    main()
