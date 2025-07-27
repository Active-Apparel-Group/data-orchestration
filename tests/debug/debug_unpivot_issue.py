"""
Debug unpivot template issue - check why 0 records were processed
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipelines.utils import db

def debug_unpivot_issue():
    """Debug why unpivot_sizes_direct template processed 0 records"""
    print("🔍 Debugging Unpivot Template Issue")
    print("=" * 50)
    
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        
        # 1. Check PENDING records in ORDER_LIST_V2
        print("1. Checking PENDING records in ORDER_LIST_V2...")
        cursor.execute("""
            SELECT TOP 3
                [AAG ORDER NUMBER],
                [CUSTOMER NAME], 
                [PO NUMBER],
                sync_state,
                [XS], [S], [M], [L], [XL]
            FROM ORDER_LIST_V2 
            WHERE sync_state = 'PENDING'
        """)
        
        pending_records = cursor.fetchall()
        print(f"   Found {len(pending_records)} PENDING records (showing first 3):")
        
        for i, record in enumerate(pending_records):
            aag_order, customer, po, sync_state, xs, s, m, l, xl = record
            print(f"   Record {i+1}: {aag_order} | {customer} | {po} | {sync_state}")
            print(f"      Size samples: XS={xs}, S={s}, M={m}, L={l}, XL={xl}")
        
        # 2. Check if any size columns have non-zero values
        print("\n2. Checking for non-zero size quantities...")
        cursor.execute("""
            SELECT COUNT(*) as pending_count,
                   SUM(CASE WHEN [XS] > 0 THEN 1 ELSE 0 END) as xs_nonzero,
                   SUM(CASE WHEN [S] > 0 THEN 1 ELSE 0 END) as s_nonzero,
                   SUM(CASE WHEN [M] > 0 THEN 1 ELSE 0 END) as m_nonzero,
                   SUM(CASE WHEN [L] > 0 THEN 1 ELSE 0 END) as l_nonzero,
                   SUM(CASE WHEN [XL] > 0 THEN 1 ELSE 0 END) as xl_nonzero
            FROM ORDER_LIST_V2 
            WHERE sync_state = 'PENDING'
        """)
        
        quantity_check = cursor.fetchone()
        pending_count, xs_nonzero, s_nonzero, m_nonzero, l_nonzero, xl_nonzero = quantity_check
        
        print(f"   PENDING records: {pending_count}")
        print(f"   Non-zero quantities: XS={xs_nonzero}, S={s_nonzero}, M={m_nonzero}, L={l_nonzero}, XL={xl_nonzero}")
        
        total_nonzero = xs_nonzero + s_nonzero + m_nonzero + l_nonzero + xl_nonzero
        print(f"   Total non-zero size entries: {total_nonzero}")
        
        # 3. Test a simplified unpivot query manually
        print("\n3. Testing simplified UNPIVOT query...")
        cursor.execute("""
            SELECT COUNT(*) as unpivot_count
            FROM (
                SELECT 
                    record_uuid,
                    sync_state,
                    size_code,
                    qty
                FROM ORDER_LIST_V2
                UNPIVOT (
                    qty FOR size_code IN ([XS], [S], [M], [L], [XL])
                ) AS sizes
                WHERE sync_state = 'PENDING'
                AND qty > 0
            ) AS unpivoted
        """)
        
        unpivot_count = cursor.fetchone()[0]
        print(f"   Manual UNPIVOT result: {unpivot_count} records would be created")
        
        # 4. Check if the issue is with the template variables
        print("\n4. Checking template context variables...")
        
        # Check what size columns are being discovered
        from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
        from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine
        
        config = load_delta_sync_config('development')
        engine = SQLTemplateEngine(config)
        context = engine.get_template_context()
        
        print(f"   Size columns discovered: {len(context['size_columns'])}")
        print(f"   First 10 size columns: {context['size_columns'][:10]}")
        print(f"   Target table: {context['target_table']}")
        print(f"   Lines table: {context['lines_table']}")
        
        return unpivot_count > 0

if __name__ == "__main__":
    debug_unpivot_issue()
