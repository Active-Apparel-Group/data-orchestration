#!/usr/bin/env python3
"""
Check Table Schema - Customer Columns
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("🔍 TABLE SCHEMA CHECK:")
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get all column names
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'swp_ORDER_LIST_SYNC'
            ORDER BY ORDINAL_POSITION
        """)
        
        all_columns = [row[0] for row in cursor.fetchall()]
        print(f"\nAll columns ({len(all_columns)}):")
        for i, col in enumerate(all_columns[:20]):  # First 20
            print(f"  {i+1:2d}. {col}")
        
        if len(all_columns) > 20:
            print(f"  ... and {len(all_columns) - 20} more columns")
        
        # Look for customer-related columns specifically
        customer_columns = [col for col in all_columns if 'CUSTOMER' in col.upper()]
        print(f"\n🎯 Customer-related columns ({len(customer_columns)}):")
        for col in customer_columns:
            print(f"  {col}")
        
        # Check for order/PO related columns
        po_columns = [col for col in all_columns if any(term in col.upper() for term in ['PO', 'ORDER'])]
        print(f"\n📋 PO/Order-related columns ({len(po_columns)}):")
        for col in po_columns:
            print(f"  {col}")
        
        cursor.close()

if __name__ == "__main__":
    main()
