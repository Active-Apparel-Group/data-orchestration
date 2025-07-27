#!/usr/bin/env pythdef main():
    
   
"""
test_merge_step_by_step.py
Step-by-step diagnosis of MERGE template issue
"""

import sys
from pathlib import Path

print("🔬 Step-by-step MERGE diagnosis...")

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

 # Load config
config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
config = DeltaSyncConfig.from_toml(config_path)

with db.get_connection(config.db_key) as connection:
    cursor = connection.cursor()

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔬 Step-by-step MERGE diagnosis...")
    
    cursor, connection = db.get_connection()
    config = DeltaSyncConfig("development")
    
    # Clean up first
    print("🧹 Cleaning ORDER_LIST_LINES...")
    cursor.execute("DELETE FROM dbo.ORDER_LIST_LINES")
    connection.commit()
    
    # Step 1: Test the UNPIVOT subquery alone
    print("\n📋 Step 1: Testing UNPIVOT subquery...")
    test_unpivot = """
    SELECT 
        record_uuid,
        sync_state,
        size_code,
        qty
    FROM dbo.ORDER_LIST_V2
    UNPIVOT (
        qty FOR size_code IN ([XL])
    ) AS sizes
    WHERE sync_state = 'PENDING'
    AND qty > 0
    """
    
    cursor.execute(test_unpivot)
    unpivot_results = cursor.fetchall()
    print(f"   UNPIVOT results: {len(unpivot_results)} records")
    if unpivot_results:
        print(f"   Sample: {unpivot_results[0][:4]}")  # First 4 columns
    
    # Step 2: Test the source subquery (what goes into MERGE USING)
    print("\n📋 Step 2: Testing MERGE source subquery...")
    test_source = """
    SELECT 
        unpivoted.record_uuid,
        unpivoted.size_code,
        unpivoted.qty,
        CONVERT(CHAR(64), HASHBYTES('SHA2_256', 
            CONCAT_WS('|', unpivoted.record_uuid, unpivoted.size_code, unpivoted.qty)), 2) as row_hash,
        'NEW' as sync_state,
        GETUTCDATE() as created_at,
        GETUTCDATE() as updated_at
    FROM (
        SELECT 
            record_uuid,
            sync_state,
            size_code,
            qty
        FROM dbo.ORDER_LIST_V2
        UNPIVOT (
            qty FOR size_code IN ([XL])
        ) AS sizes
    ) AS unpivoted
    WHERE unpivoted.sync_state = 'PENDING'
    AND unpivoted.qty > 0
    """
    
    cursor.execute(test_source)
    source_results = cursor.fetchall()
    print(f"   Source subquery results: {len(source_results)} records")
    if source_results:
        print(f"   Sample: record_uuid={source_results[0][0]}, size_code={source_results[0][1]}, qty={source_results[0][2]}")
    
    # Step 3: Test simple INSERT instead of MERGE
    print("\n📋 Step 3: Testing simple INSERT instead of MERGE...")
    simple_insert = """
    INSERT INTO dbo.ORDER_LIST_LINES (
        record_uuid, 
        size_code, 
        qty,
        row_hash,
        sync_state,
        created_at,
        updated_at
    )
    SELECT 
        unpivoted.record_uuid,
        unpivoted.size_code,
        unpivoted.qty,
        CONVERT(CHAR(64), HASHBYTES('SHA2_256', 
            CONCAT_WS('|', unpivoted.record_uuid, unpivoted.size_code, unpivoted.qty)), 2) as row_hash,
        'NEW' as sync_state,
        GETUTCDATE() as created_at,
        GETUTCDATE() as updated_at
    FROM (
        SELECT 
            record_uuid,
            sync_state,
            size_code,
            qty
        FROM dbo.ORDER_LIST_V2
        UNPIVOT (
            qty FOR size_code IN ([XL])
        ) AS sizes
    ) AS unpivoted
    WHERE unpivoted.sync_state = 'PENDING'
    AND unpivoted.qty > 0
    """
    
    cursor.execute(simple_insert)
    inserted_count = cursor.rowcount
    connection.commit()
    print(f"   ✅ Simple INSERT created: {inserted_count} records")
    
    # Verify records exist
    cursor.execute("SELECT COUNT(*) FROM dbo.ORDER_LIST_LINES")
    final_count = cursor.fetchone()[0]
    print(f"   ✅ Final count in ORDER_LIST_LINES: {final_count}")
    
    # Step 4: Test the exact MERGE syntax
    print("\n📋 Step 4: Testing exact MERGE syntax...")
    cursor.execute("DELETE FROM dbo.ORDER_LIST_LINES")
    connection.commit()
    
    exact_merge = """
    MERGE dbo.ORDER_LIST_LINES AS target
    USING (
        SELECT 
            unpivoted.record_uuid,
            unpivoted.size_code,
            unpivoted.qty,
            CONVERT(CHAR(64), HASHBYTES('SHA2_256', 
                CONCAT_WS('|', unpivoted.record_uuid, unpivoted.size_code, unpivoted.qty)), 2) as row_hash,
            'NEW' as sync_state,
            GETUTCDATE() as created_at,
            GETUTCDATE() as updated_at
        FROM (
            SELECT 
                record_uuid,
                sync_state,
                size_code,
                qty
            FROM dbo.ORDER_LIST_V2
            UNPIVOT (
                qty FOR size_code IN ([XL])
            ) AS sizes
        ) AS unpivoted
        WHERE unpivoted.sync_state = 'PENDING'  -- Only process pending sync records
        AND unpivoted.qty > 0  -- Exclude zero quantities
    ) AS source
    ON target.record_uuid = source.record_uuid 
       AND target.size_code = source.size_code  -- Business key: record + size
    
    -- Handle NOT MATCHED records (INSERT) - Simplified to match working version
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            record_uuid, 
            size_code, 
            qty,
            row_hash,
            sync_state,
            created_at,
            updated_at
        )
        VALUES (
            source.record_uuid,
            source.size_code,
            source.qty,
            source.row_hash,
            source.sync_state,
            source.created_at,
            source.updated_at
        );
    """
    
    cursor.execute(exact_merge)
    merge_count = cursor.rowcount
    connection.commit()
    print(f"   📊 MERGE affected: {merge_count} records")
    
    # Final verification
    cursor.execute("SELECT COUNT(*) FROM dbo.ORDER_LIST_LINES")
    final_merge_count = cursor.fetchone()[0]
    print(f"   ✅ Final count after MERGE: {final_merge_count}")
    
    if final_merge_count > 0:
        print("\n🎉 MERGE works! The template should work too.")
    else:
        print("\n❌ MERGE failed - need to investigate further")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
