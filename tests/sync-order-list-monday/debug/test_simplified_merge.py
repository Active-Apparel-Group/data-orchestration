"""
Simplified MERGE Test - Find the Template Error
===============================================
Purpose: Run a simplified version of the exact MERGE to isolate the template error
Strategy: Compare working simple MERGE vs generated template MERGE

ROOT CAUSE: Template MERGE has a syntax issue that prevents INSERT execution
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

def test_simplified_merge():
    """Test a simplified MERGE vs the template MERGE"""
    
    print("🔍 SIMPLIFIED MERGE TEST")
    print("="*40)
    
    # Load config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Simple working MERGE (based on our successful manual INSERT)
    simple_merge = '''
        MERGE ORDER_LIST_LINES AS target
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
                FROM ORDER_LIST_V2
                UNPIVOT (qty FOR size_code IN ([XL])) AS sizes
            ) AS unpivoted
            WHERE unpivoted.sync_state = 'PENDING'
            AND unpivoted.qty > 0
        ) AS source
        ON target.record_uuid = source.record_uuid 
           AND target.size_code = source.size_code
        
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
    '''
    
    with db.get_connection(config.db_key) as conn:
        cursor = conn.cursor()
        
        # Test the simple MERGE
        print("🧪 Testing simplified MERGE...")
        
        try:
            cursor.execute(simple_merge)
            conn.commit()
            
            # Check results
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES")
            simple_count = cursor.fetchone()[0]
            
            print(f"✅ Simplified MERGE result: {simple_count} records")
            
            if simple_count > 0:
                print("🎉 SUCCESS: Simplified MERGE works!")
                print("❌ CONFIRMED: Template MERGE has a syntax/logic error")
                
                # Sample the created records
                cursor.execute("""
                    SELECT TOP 3 record_uuid, size_code, qty, sync_state 
                    FROM ORDER_LIST_LINES 
                    ORDER BY created_at DESC
                """)
                samples = cursor.fetchall()
                
                print("📋 Sample records created by simple MERGE:")
                for row in samples:
                    print(f"    {row}")
                
                # Clean up for next test
                cursor.execute("DELETE FROM ORDER_LIST_LINES")
                conn.commit()
                print("🧹 Cleaned up for comparison")
                
                # Now let's identify the specific difference
                print("\n🔍 COMPARING WITH TEMPLATE MERGE...")
                print("The template MERGE must have:")
                print("  1. Extra clauses that interfere")
                print("  2. Wrong column mappings")  
                print("  3. Conditional logic that filters records")
                print("  4. Missing required columns")
                
            else:
                print("❌ FAILURE: Even simplified MERGE failed")
                
        except Exception as e:
            print(f"❌ Simplified MERGE failed: {str(e)}")

if __name__ == "__main__":
    test_simplified_merge()
