#!/usr/bin/env python3
"""
Debug Header Data Structure - Check exact format of header records
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 Debug Header Data Structure...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get sample header record
        query = """
        SELECT TOP 1 
            [group_name], 
            group_name,
            [CUSTOMER NAME],
            [PO NUMBER],
            record_uuid
        FROM [FACT_ORDER_LIST] 
        WHERE [group_name] IS NOT NULL
        """
        
        print(f"📋 Query: {query}")
        cursor.execute(query)
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        print(f"🏷️  Column Names: {column_names}")
        
        # Get data
        row = cursor.fetchone()
        if row:
            # Convert to dict
            header_dict = dict(zip(column_names, row))
            print(f"📊 Header Dict Keys: {list(header_dict.keys())}")
            print(f"📊 Header Dict: {header_dict}")
            
            # Test the exact logic
            group_name = header_dict.get('group_name')
            bracketed_group_name = header_dict.get('[group_name]')
            customer_name = header_dict.get('CUSTOMER NAME')
            
            print(f"\n🧪 Testing Access Methods:")
            print(f"  header_dict.get('group_name'): {repr(group_name)}")
            print(f"  header_dict.get('[group_name]'): {repr(bracketed_group_name)}")
            print(f"  header_dict.get('CUSTOMER NAME'): {repr(customer_name)}")
            
            # Check what would happen in the method
            if group_name:
                print(f"✅ SUCCESS: Would use group_name: '{group_name}'")
            elif bracketed_group_name:
                print(f"⚠️  BRACKETED: Would use [group_name]: '{bracketed_group_name}'")
            else:
                print(f"❌ FALLBACK: Would use customer name: '{customer_name}'")
        else:
            print("❌ No records found")
        
        cursor.close()

if __name__ == "__main__":
    main()
