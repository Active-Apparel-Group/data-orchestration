"""
MERGE Logic Diagnostic Test
===========================
Purpose: Test the exact MERGE logic that's failing in unpivot_sizes_direct.j2
Root Cause: UNPIVOT works (52 XL records), but MERGE produces 0 records

Strategy: Test the MERGE operation step by step to find where records are lost
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

def test_merge_logic():
    """Test the exact MERGE logic that's failing"""
    
    print("🔍 MERGE LOGIC DIAGNOSTIC")
    print("="*50)
    
    # Load config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Test the source subquery of the MERGE operation
    source_subquery = '''
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
            FROM ORDER_LIST_V2
            UNPIVOT (
                qty FOR size_code IN ([XL])
            ) AS sizes
        ) AS unpivoted
        WHERE unpivoted.sync_state = 'PENDING'
        AND unpivoted.qty > 0
    '''
    
    # Test if existing records exist in ORDER_LIST_LINES
    existing_check = '''
        SELECT COUNT(*) FROM ORDER_LIST_LINES
    '''
    
    # Test business key matching
    business_key_test = '''
        SELECT COUNT(*) 
        FROM (
            SELECT record_uuid, 'XL' as size_code, [XL] as qty
            FROM ORDER_LIST_V2 
            WHERE sync_state = 'PENDING' AND [XL] > 0
        ) source
        LEFT JOIN ORDER_LIST_LINES target 
        ON target.record_uuid = source.record_uuid 
        AND target.size_code = source.size_code
        WHERE target.record_uuid IS NULL  -- Would be INSERT
    '''
    
    queries = {
        "1. Source subquery record count": f"SELECT COUNT(*) FROM ({source_subquery}) AS test_source",
        "2. Existing ORDER_LIST_LINES count": existing_check,
        "3. Business key matching (INSERTs)": business_key_test,
        "4. Sample source data": f"SELECT TOP 3 record_uuid, size_code, qty FROM ({source_subquery}) AS test_source"
    }
    
    # Execute queries
    with db.get_connection(config.db_key) as conn:
        cursor = conn.cursor()
        
        for description, query in queries.items():
            try:
                cursor.execute(query)
                
                if "Sample" in description:
                    results = cursor.fetchall()
                    print(f"✅ {description}:")
                    for row in results:
                        print(f"    {row}")
                else:
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    print(f"✅ {description}: {count}")
                
            except Exception as e:
                print(f"❌ {description}: ERROR - {str(e)}")
    
    print("\n🔧 DIAGNOSIS:")
    print("If source subquery shows 52 records but MERGE creates 0:")
    print("  - Business key logic might be wrong")
    print("  - MERGE conditions might be filtering everything out")
    print("  - Template might have syntax issues")

if __name__ == "__main__":
    test_merge_logic()
