"""
Quick Diagnostic: UNPIVOT Logic Issue Analysis
==============================================
Purpose: Quick diagnosis of why unpivot_sizes_direct.j2 creates 0 records
Strategy: Test the exact SQL logic that's failing in the template

FOCUS: Test the UNPIVOT operation directly on the data
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

def test_unpivot_issue():
    """Quick test to identify UNPIVOT issue"""
    
    print("🔍 QUICK UNPIVOT DIAGNOSTIC")
    print("="*50)
    
    # Load config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Test queries
    queries = {
        "1. Total records in ORDER_LIST_V2": """
            SELECT COUNT(*) FROM ORDER_LIST_V2
        """,
        
        "2. PENDING records in ORDER_LIST_V2": """
            SELECT COUNT(*) FROM ORDER_LIST_V2 WHERE sync_state = 'PENDING'
        """,
        
        "3. XL > 0 in PENDING records": """
            SELECT COUNT(*) FROM ORDER_LIST_V2 
            WHERE sync_state = 'PENDING' AND [XL] > 0
        """,
        
        "4. Simple XL UNPIVOT test": """
            SELECT COUNT(*) FROM (
                SELECT record_uuid, size_code, qty
                FROM ORDER_LIST_V2
                UNPIVOT (qty FOR size_code IN ([XL])) AS sizes
                WHERE sync_state = 'PENDING' AND qty > 0
            ) AS test
        """,
        
        "5. Multi-size UNPIVOT test": """
            SELECT COUNT(*) FROM (
                SELECT record_uuid, size_code, qty
                FROM ORDER_LIST_V2
                UNPIVOT (qty FOR size_code IN ([XS], [S], [M], [L], [XL], [XXL])) AS sizes
                WHERE sync_state = 'PENDING' AND qty > 0
            ) AS test
        """
    }
    
    # Execute queries
    with db.get_connection(config.db_key) as conn:
        cursor = conn.cursor()
        
        for description, query in queries.items():
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                count = result[0] if result else 0
                print(f"✅ {description}: {count}")
                
            except Exception as e:
                print(f"❌ {description}: ERROR - {str(e)}")
    
    print("\n🎯 If steps 1-3 show data but steps 4-5 show 0, the UNPIVOT logic is the issue!")
    print("🎯 If all steps show 0, the sync_state filter is the issue!")

if __name__ == "__main__":
    test_unpivot_issue()
