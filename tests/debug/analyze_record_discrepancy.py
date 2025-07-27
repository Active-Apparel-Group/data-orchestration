#!/usr/bin/env python3
"""
Analyze Record Discrepancy - 69 vs 67 Records
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("📊 RECORD DISCREPANCY ANALYSIS")
    print("=" * 50)
    
    # Get config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # 1. Check source records 
        print("1️⃣ SOURCE RECORDS")
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST")
        source_count = cursor.fetchone()[0]
        print(f"   Total records in FACT_ORDER_LIST: {source_count}")
        
        # 2. Check records with Monday IDs
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST WHERE monday_item_id IS NOT NULL AND monday_item_id != ''")
        monday_item_count = cursor.fetchone()[0]
        print(f"   Records with monday_item_id: {monday_item_count}")
        
        # 3. Check unique headers with Monday IDs (should be 69)
        cursor.execute("""
            SELECT COUNT(DISTINCT record_uuid) 
            FROM FACT_ORDER_LIST 
            WHERE monday_item_id IS NOT NULL AND monday_item_id != ''
        """)
        header_count = cursor.fetchone()[0]
        print(f"   Unique headers with Monday IDs: {header_count}")
        
        # 4. Check for headers vs lines pattern
        print("\n2️⃣ HEADERS VS LINES ANALYSIS")
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN monday_item_id IS NOT NULL AND monday_item_id != '' THEN 1 END) as headers_with_items,
                COUNT(CASE WHEN monday_subitem_id IS NOT NULL AND monday_subitem_id != '' THEN 1 END) as lines_with_subitems
            FROM FACT_ORDER_LIST
        """)
        result = cursor.fetchone()
        headers_with_items, lines_with_subitems = result
        print(f"   Headers with monday_item_id: {headers_with_items}")
        print(f"   Lines with monday_subitem_id: {lines_with_subitems}")
        
        # 5. Check terminal output patterns
        print("\n3️⃣ TERMINAL OUTPUT ANALYSIS")
        print("   From terminal execution:")
        print("     - Total synced: 322 records")
        print("     - Successful batches: 67/67")  
        print("     - Headers: 67, Lines: 255")
        print("     - Expected: 67 headers + 255 lines = 322 ✅")
        
        # 6. Find the missing 2 headers
        print("\n4️⃣ MISSING HEADERS INVESTIGATION")
        cursor.execute("""
            SELECT COUNT(DISTINCT record_uuid) 
            FROM FACT_ORDER_LIST 
            WHERE monday_item_id IS NOT NULL AND monday_item_id != ''
        """)
        actual_headers = cursor.fetchone()[0]
        expected_headers = 69
        missing_count = expected_headers - actual_headers
        print(f"   Expected headers: {expected_headers}")
        print(f"   Actual headers with Monday IDs: {actual_headers}")
        print(f"   Missing headers: {missing_count}")
        
        if missing_count > 0:
            print(f"\n5️⃣ FINDING MISSING RECORD UUIDs")
            # Find all unique record_uuids
            cursor.execute("SELECT DISTINCT record_uuid FROM FACT_ORDER_LIST")
            all_record_uuids = {row[0] for row in cursor.fetchall()}
            
            # Find record_uuids with Monday IDs
            cursor.execute("""
                SELECT DISTINCT record_uuid 
                FROM FACT_ORDER_LIST 
                WHERE monday_item_id IS NOT NULL AND monday_item_id != ''
            """)
            synced_record_uuids = {row[0] for row in cursor.fetchall()}
            
            # Find missing ones
            missing_record_uuids = all_record_uuids - synced_record_uuids
            
            print(f"   Missing record UUIDs ({len(missing_record_uuids)}):")
            for record_uuid in missing_record_uuids:
                # Get details for this record
                cursor.execute("""
                    SELECT [AAG ORDER NUMBER], [CUSTOMER NAME], [PO NUMBER], COUNT(*) as total_lines
                    FROM FACT_ORDER_LIST 
                    WHERE record_uuid = ?
                    GROUP BY record_uuid, [AAG ORDER NUMBER], [CUSTOMER NAME], [PO NUMBER]
                """, record_uuid)
                details = cursor.fetchone()
                if details:
                    aag_order, customer, po, line_count = details
                    print(f"     {record_uuid}")
                    print(f"       Order: {aag_order}, Customer: {customer}, PO: {po}")
                    print(f"       Lines: {line_count}")
        else:
            print("   ✅ No missing headers found!")
            
        # 7. Summary and conclusion
        print(f"\n6️⃣ CONCLUSION")
        print(f"   The discrepancy analysis shows:")
        if missing_count == 0:
            print("   ✅ All database headers have Monday IDs")
            print("   ✅ Issue may be with Monday.com display/filtering")
            print("   ✅ Check Monday.com board directly for 69 items")
        else:
            print(f"   ⚠️  {missing_count} headers failed to get Monday IDs")
            print("   🔍 These records may have encountered API errors")
            print("   📋 Check sync_error_message column for details")
        
        cursor.close()

if __name__ == "__main__":
    main()
