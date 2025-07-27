#!/usr/bin/env python3
"""
Find Multi-Customer Test Data - 3 customers, 1 PO each
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
    # Load config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    print('🔍 Finding top 3 customers with single POs for testing...')
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get customers with single POs (best for testing)
        cursor.execute('''
            SELECT 
                [CUSTOMER NAME],
                [PO NUMBER],
                COUNT(*) as record_count,
                MIN([AAG ORDER NUMBER]) as first_order,
                MAX([AAG ORDER NUMBER]) as last_order
            FROM swp_ORDER_LIST_SYNC 
            WHERE [CUSTOMER NAME] IS NOT NULL 
              AND [PO NUMBER] IS NOT NULL
              AND [AAG ORDER NUMBER] IS NOT NULL
            GROUP BY [CUSTOMER NAME], [PO NUMBER]
            HAVING COUNT(*) >= 5  -- At least 5 records for meaningful test
            ORDER BY [CUSTOMER NAME], record_count DESC
        ''')
        
        results = cursor.fetchall()
        print(f'📊 Found {len(results)} customer/PO combinations with 5+ records')
        
        # Group by customer and pick top PO for each
        customers = {}
        for customer, po, count, first_order, last_order in results:
            if customer not in customers:
                customers[customer] = (po, count, first_order, last_order)
        
        # Take first 3 customers
        test_customers = list(customers.keys())[:3]
        
        print(f'\n🎯 Recommended 3-customer test configuration:')
        print('limit_customers = [', end='')
        for i, customer in enumerate(test_customers):
            if i > 0:
                print(', ', end='')
            print(f'"{customer}"', end='')
        print(']')
        
        print('limit_pos = [', end='')
        for i, customer in enumerate(test_customers):
            po, count, _, _ = customers[customer]
            if i > 0:
                print(', ', end='')
            print(f'"{po}"', end='')
        print(']')
        
        print(f'\n📋 Test data details:')
        total_records = 0
        for customer in test_customers:
            po, count, first_order, last_order = customers[customer]
            print(f'  - {customer} PO {po}: {count} records (Orders: {first_order} to {last_order})')
            total_records += count
        
        print(f'\n📊 Total test records: {total_records}')
        
        cursor.close()

if __name__ == "__main__":
    main()
