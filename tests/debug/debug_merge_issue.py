"""
Debug: Task 19.14.3 Merge Issue Investigation
Simple test to understand why merge returns 0 records
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator
import pandas as pd

def debug_merge_issue():
    """Debug why merge template returns 0 records"""
    print("🔍 Task 19.14.3 - Debug Merge Issue")
    
    # Load config and connect
    config = load_delta_sync_config()
    conn = db.get_connection(config.db_key)
    
    try:
        # Check source data
        source_count = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM swp_ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
            AND [PO NUMBER] = '4755' 
            AND sync_state = 'NEW'
        """, conn)['count'][0]
        
        print(f"✅ Source records ready for merge: {source_count}")
        
        # Check target data
        target_count = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS'
        """, conn)['count'][0]
        
        print(f"✅ Target records (GREYSON): {target_count}")
        
        # Execute merge template using orchestrator
        orchestrator = MergeOrchestrator(config)
        
        print("\n🔧 Executing merge headers template...")
        # Execute just the headers merge in dry_run=False mode
        headers_result = orchestrator._execute_template_merge_headers(dry_run=False)
        
        print(f"Headers merge result: {headers_result}")
        
        # Check what happened
        post_merge_count = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS'
        """, conn)['count'][0]
        
        print(f"✅ Target records after merge: {post_merge_count}")
        
        if post_merge_count == 0:
            print("\n❌ PROBLEM: Merge executed but 0 records inserted")
            print("🔍 Let's check a sample business key match manually...")
            
            # Get a sample AAG ORDER NUMBER
            sample_key = pd.read_sql("""
                SELECT TOP 1 [AAG ORDER NUMBER] 
                FROM swp_ORDER_LIST_V2 
                WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
                AND [PO NUMBER] = '4755' 
                AND sync_state = 'NEW'
            """, conn)['AAG ORDER NUMBER'][0]
            
            print(f"Sample business key: '{sample_key}'")
            
            # Try a simple insert to see if it works
            test_insert = f"""
                INSERT INTO ORDER_LIST_V2 ([AAG ORDER NUMBER], [CUSTOMER NAME], sync_state, action_type)
                SELECT TOP 1 [AAG ORDER NUMBER], [CUSTOMER NAME], 'NEW', 'INSERT'
                FROM swp_ORDER_LIST_V2 
                WHERE [AAG ORDER NUMBER] = '{sample_key}'
            """
            
            cursor = conn.cursor()
            cursor.execute(test_insert)
            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            
            print(f"Test insert result: {rows_affected} rows affected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_merge_issue()
