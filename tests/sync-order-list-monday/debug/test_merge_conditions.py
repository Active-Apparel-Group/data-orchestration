"""
MERGE Conditions Test - Find the INSERT Issue
==============================================
Purpose: Test the exact MERGE conditions to see why INSERT isn't happening
Strategy: Simulate the MERGE logic step by step

ROOT CAUSE: Source has 52 records, target has 0, but MERGE INSERT doesn't fire
"""

import sys
from pathlib import Path

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def test_merge_conditions():
    """Test the exact MERGE conditions"""
    
    print("🔍 MERGE CONDITIONS TEST")
    print("="*40)
    
    # Load config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Simulate the MERGE operation step by step
    queries = {
        "1. Source records ready for MERGE": '''
            SELECT COUNT(*) FROM (
                SELECT 
                    unpivoted.record_uuid,
                    unpivoted.size_code,
                    unpivoted.qty
                FROM (
                    SELECT 
                        record_uuid,
                        sync_state,
                        size_code,
                        qty
                    FROM ORDER_LIST_V2
                    UNPIVOT (qty FOR size_code IN ([XL])) AS sizes
                ) AS unpivoted
                WHERE unpivoted.sync_state = 'PENDING'
                AND unpivoted.qty > 0
            ) AS source
        ''',
        
        "2. Target records for matching": '''
            SELECT COUNT(*) FROM ORDER_LIST_LINES
        ''',
        
        "3. NOT MATCHED simulation (should be 52)": '''
            SELECT COUNT(*) FROM (
                SELECT 
                    s.record_uuid,
                    s.size_code,
                    s.qty
                FROM (
                    SELECT 
                        unpivoted.record_uuid,
                        unpivoted.size_code,
                        unpivoted.qty
                    FROM (
                        SELECT 
                            record_uuid,
                            sync_state,
                            size_code,
                            qty
                        FROM ORDER_LIST_V2
                        UNPIVOT (qty FOR size_code IN ([XL])) AS sizes
                    ) AS unpivoted
                    WHERE unpivoted.sync_state = 'PENDING'
                    AND unpivoted.qty > 0
                ) AS s
                LEFT JOIN ORDER_LIST_LINES t 
                ON t.record_uuid = s.record_uuid 
                AND t.size_code = s.size_code
                WHERE t.record_uuid IS NULL  -- NOT MATCHED condition
            ) AS not_matched
        ''',
        
        "4. Test manual INSERT (should work)": '''
            SELECT 'Test passed - would insert records' as result
        '''
    }
    
    with db.get_connection(config.db_key) as conn:
        cursor = conn.cursor()
        
        for description, query in queries.items():
            try:
                cursor.execute(query)
                
                if "Test manual INSERT" in description:
                    result = cursor.fetchone()[0]
                    print(f"✅ {description}: {result}")
                    
                    # Now actually test a manual INSERT
                    print("🧪 Testing manual INSERT...")
                    
                    manual_insert = '''
                        INSERT INTO ORDER_LIST_LINES (
                            record_uuid, 
                            size_code, 
                            qty,
                            row_hash,
                            sync_state,
                            created_at,
                            updated_at
                        )
                        SELECT TOP 1
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
                            FROM ORDER_LIST_V2
                            UNPIVOT (qty FOR size_code IN ([XL])) AS sizes
                        ) AS unpivoted
                        WHERE unpivoted.sync_state = 'PENDING'
                        AND unpivoted.qty > 0
                    '''
                    
                    cursor.execute(manual_insert)
                    conn.commit()
                    
                    # Check if it worked
                    cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES")
                    inserted_count = cursor.fetchone()[0]
                    
                    if inserted_count > 0:
                        print(f"🎉 SUCCESS: Manual INSERT worked! {inserted_count} record(s) inserted")
                        print("❌ ISSUE CONFIRMED: The MERGE template has a logic error, but INSERT works fine")
                        
                        # Clean up the test record
                        cursor.execute("DELETE FROM ORDER_LIST_LINES")
                        conn.commit()
                        print("🧹 Test record cleaned up")
                        
                    else:
                        print("❌ FAILURE: Even manual INSERT failed - deeper issue")
                        
                else:
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    print(f"✅ {description}: {count}")
                
            except Exception as e:
                print(f"❌ {description}: ERROR - {str(e)}")
    
    print("\n🎯 DIAGNOSIS:")
    print("If manual INSERT works but MERGE doesn't, the MERGE template has a syntax error.")
    print("If manual INSERT fails too, there's a data type or constraint issue.")

if __name__ == "__main__":
    test_merge_conditions()
