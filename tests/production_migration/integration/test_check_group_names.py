#!/usr/bin/env python3
"""
Check Group Name Values
======================
Purpose: Check what's in the group_name column for GREYSON records
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db

def main():
    print("🔍 Checking Group Name Values for GREYSON Records")
    print("=" * 50)
    
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT TOP 5
                [CUSTOMER NAME],
                [PO NUMBER], 
                [group_name],
                [item_name]
            FROM [FACT_ORDER_LIST]
            WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
              AND [PO NUMBER] = '4755'
              AND [sync_state] = 'PENDING'
        """)
        
        results = cursor.fetchall()
        
        for customer, po, group_name, item_name in results:
            print(f"Customer: '{customer}'")
            print(f"PO: '{po}'") 
            print(f"group_name: '{group_name}' (type: {type(group_name)})")
            print(f"item_name: '{item_name}' (type: {type(item_name)})")
            print("---")

if __name__ == "__main__":
    main()
