#!/usr/bin/env python3
"""
🔍 ORDER VERIFICATION TEST - Check if line ordering is preserved
Test the exact ordering of lines from DB → API → Response → Update
"""

import sys
from pathlib import Path
import json

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 Line Order Verification Test...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the exact failed record data
        failed_query = """
        SELECT 
            line_uuid,
            size_code,
            qty,
            monday_subitem_id,
            api_request_payload
        FROM ORDER_LIST_LINES 
        WHERE api_operation_type = 'subitem_creation'
        AND api_status = 'ERROR'
        ORDER BY size_code  -- Same order as sync engine uses
        """
        
        cursor.execute(failed_query)
        records = cursor.fetchall()
        
        if not records:
            print("❌ No failed subitem creation records found")
            return
        
        print(f"\n📋 Database Order (ORDER BY size_code):")
        for i, record in enumerate(records):
            print(f"   {i}: {record[0][:8]}... | Size: {record[1]} | Qty: {record[2]} | Monday ID: {record[3]}")
        
        # Parse the API request payload to see the order sent
        try:
            api_request = json.loads(records[0][4]) if records[0][4] else []
            
            print(f"\n📤 API Request Order (from payload):")
            for i, request_record in enumerate(api_request):
                line_uuid = request_record.get('line_uuid', 'unknown')[:8] + "..."
                size_code = request_record.get('size_code', 'unknown')
                qty = request_record.get('qty', 'unknown')
                print(f"   {i}: {line_uuid} | Size: {size_code} | Qty: {qty}")
            
            # Check if orders match
            print(f"\n🔍 Order Verification:")
            db_sizes = [record[1] for record in records]
            api_sizes = [r.get('size_code') for r in api_request]
            
            print(f"   DB Order:  {db_sizes}")
            print(f"   API Order: {api_sizes}")
            
            if db_sizes == api_sizes:
                print("   ✅ ORDERS MATCH - This is NOT the issue")
            else:
                print("   ❌ ORDER MISMATCH - This IS the issue!")
                
                # Show the mapping that would occur
                print(f"\n🔧 Incorrect Mapping that would occur:")
                for i in range(min(len(db_sizes), len(api_sizes))):
                    if i < len(records):
                        db_uuid = records[i][0][:8] + "..."
                        db_size = db_sizes[i]
                        api_size = api_sizes[i]
                        print(f"   DB Line {db_uuid} (Size {db_size}) → API response[{i}] (Size {api_size})")
            
            # Check individual line_uuid matching
            print(f"\n🔍 Line UUID Verification:")
            db_uuids = [record[0] for record in records]
            api_uuids = [r.get('line_uuid') for r in api_request]
            
            for i in range(min(len(db_uuids), len(api_uuids))):
                db_uuid = db_uuids[i][:8] + "..."
                api_uuid = api_uuids[i][:8] + "..." if api_uuids[i] else "None"
                match = "✅" if db_uuids[i] == api_uuids[i] else "❌"
                print(f"   {i}: DB {db_uuid} ↔ API {api_uuid} {match}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse API request payload: {e}")
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
        
        cursor.close()

if __name__ == "__main__":
    main()
