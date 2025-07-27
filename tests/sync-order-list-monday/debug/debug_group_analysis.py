#!/usr/bin/env python3
"""
Debug Group Analysis - Check group_name and group_id status
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db

def main():
    print("🔍 GROUP ANALYSIS - Checking group_name and group_id status")
    print("=" * 80)
    
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        print("📋 Query 1: swp_ORDER_LIST_SYNC (source table)")
        query1 = """
        SELECT DISTINCT [AAG SEASON], [CUSTOMER SEASON], group_name, group_id 
        FROM swp_ORDER_LIST_SYNC
        WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'
        """
        cursor.execute(query1)
        results1 = cursor.fetchall()
        
        if results1:
            for row in results1:
                print(f"   AAG SEASON: {row[0]}")
                print(f"   CUSTOMER SEASON: {row[1]}")
                print(f"   group_name: {row[2]}")
                print(f"   group_id: {row[3]}")
        else:
            print("   No records found")
        
        print("\n📋 Query 2: FACT_ORDER_LIST (target table)")
        query2 = """
        SELECT DISTINCT [AAG SEASON], [CUSTOMER SEASON], group_name, group_id 
        FROM FACT_ORDER_LIST
        WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'
        """
        cursor.execute(query2)
        results2 = cursor.fetchall()
        
        if results2:
            for row in results2:
                print(f"   AAG SEASON: {row[0]}")
                print(f"   CUSTOMER SEASON: {row[1]}")
                print(f"   group_name: {row[2]}")
                print(f"   group_id: {row[3]}")
        else:
            print("   No records found")
        
        print("\n📊 Record counts:")
        cursor.execute("SELECT COUNT(*) FROM swp_ORDER_LIST_SYNC WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'")
        source_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'")
        target_count = cursor.fetchone()[0]
        
        print(f"   swp_ORDER_LIST_SYNC records: {source_count}")
        print(f"   FACT_ORDER_LIST records: {target_count}")
        
        # Check MON_Boards_Groups table
        print("\n📋 Query 3: MON_Boards_Groups (tracking table)")
        query3 = """
        SELECT group_name, group_id, board_id
        FROM MON_Boards_Groups
        WHERE group_name = 'GREYSON 2025 FALL'
        """
        cursor.execute(query3)
        results3 = cursor.fetchall()
        
        if results3:
            print(f"   Found {len(results3)} group entries:")
            for i, row in enumerate(results3, 1):
                print(f"   Entry {i}: group_name='{row[0]}', monday_group_id='{row[1]}', board_id={row[2]}")
        else:
            print("   No group tracking records found")
        
        cursor.close()

if __name__ == "__main__":
    main()
