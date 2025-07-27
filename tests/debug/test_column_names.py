#!/usr/bin/env python3
"""
Check column names in v_order_list_hash_nulls view
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print('🔍 Checking actual column names in v_order_list_hash_nulls view...')
        cursor.execute('SELECT TOP 1 * FROM [v_order_list_hash_nulls]')
        columns = [desc[0] for desc in cursor.description]
        
        print(f'Total columns: {len(columns)}')
        print('Key columns found:')
        customer_col = None
        po_col = None
        hash_col = None
        uuid_col = None
        
        for i, col in enumerate(columns):
            if any(word.lower() in col.lower() for word in ['customer', 'po', 'hash', 'record', 'uuid']):
                print(f'  {i}: {col}')
                
                if 'customer' in col.lower() and 'name' in col.lower():
                    customer_col = col
                elif 'po' in col.lower() and 'number' in col.lower():
                    po_col = col
                elif 'hash' in col.lower():
                    hash_col = col
                elif 'record_uuid' in col.lower():
                    uuid_col = col
        
        print(f'\\nIdentified key columns:')
        print(f'  Customer: {customer_col}')
        print(f'  PO: {po_col}')
        print(f'  Hash: {hash_col}')
        print(f'  UUID: {uuid_col}')
        
        # Test querying with the correct column names
        if customer_col and hash_col:
            print('\\n🧪 Testing query with correct column names...')
            try:
                query = f'SELECT TOP 3 [{customer_col}], [{hash_col}] FROM [v_order_list_hash_nulls] WHERE [{customer_col}] LIKE \'%GREYSON%\''
                cursor.execute(query)
                results = cursor.fetchall()
                print(f'✅ Query successful: {len(results)} GREYSON records')
                for i, row in enumerate(results):
                    print(f'  {i+1}. Customer: {row[0]}, Hash: {row[1]}')
            except Exception as e:
                print(f'❌ Query failed: {e}')
        
        cursor.close()

if __name__ == "__main__":
    main()
