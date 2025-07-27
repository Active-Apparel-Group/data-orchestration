#!/usr/bin/env python3
"""
Check API Logging Data - Verify Monday.com API logging system captured data
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🔍 Checking Monday.com API Logging Data...")
    
    # Database connection
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        # First, let's check what tables exist with ORDER_LIST in the name
        print("\n🔍 Finding ORDER_LIST tables...")
        cursor.execute('''
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME LIKE '%ORDER_LIST%'
            ORDER BY TABLE_NAME
        ''')
        tables = cursor.fetchall()
        print("Available ORDER_LIST tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check the main ORDER_LIST table for API logging columns
        print("\n📊 API Logging Data in ORDER_LIST:")
        print("=" * 60)
        cursor.execute('''
            SELECT TOP 5
                [AAG ORDER NUMBER], 
                [monday_item_id],
                [api_operation_type],
                [api_request_timestamp],
                [api_response_timestamp],
                [api_status],
                LEFT([api_request_payload], 100) as request_preview,
                LEFT([api_response_payload], 100) as response_preview
            FROM [FACT_ORDER_LIST] 
            WHERE [api_operation_type] IS NOT NULL 
            ORDER BY [api_request_timestamp] DESC
        ''')
        headers = cursor.fetchall()
        
        if headers:
            for i, row in enumerate(headers, 1):
                print(f"\n{i}. Order: {row[0]}")
                print(f"   Monday Item ID: {row[1]}")
                print(f"   Operation: {row[2]}")
                print(f"   Status: {row[5]}")
                print(f"   Request Time: {row[3]}")
                print(f"   Response Time: {row[4]}")
                if row[6]:
                    print(f"   Request Preview: {row[6]}...")
                if row[7]:
                    print(f"   Response Preview: {row[7]}...")
        else:
            print("   ❌ No API logging data found in ORDER_LIST")
        
        print("\n📊 API Logging Data in ORDER_LIST_LINES:")
        print("=" * 60)
        cursor.execute('''
            SELECT TOP 5
                [line_uuid],
                [monday_subitem_id],
                [api_operation_type],
                [api_request_timestamp],
                [api_response_timestamp],
                [api_status],
                LEFT([api_request_payload], 100) as request_preview,
                LEFT([api_response_payload], 100) as response_preview
            FROM [ORDER_LIST_LINES] 
            WHERE [api_operation_type] IS NOT NULL 
            ORDER BY [api_request_timestamp] DESC
        ''')
        lines = cursor.fetchall()
        
        if lines:
            for i, row in enumerate(lines, 1):
                print(f"\n{i}. Line UUID: {str(row[0])[:8]}...")
                print(f"   Monday Subitem ID: {row[1]}")
                print(f"   Operation: {row[2]}")
                print(f"   Status: {row[5]}")
                print(f"   Request Time: {row[3]}")
                print(f"   Response Time: {row[4]}")
                if row[6]:
                    print(f"   Request Preview: {row[6]}...")
                if row[7]:
                    print(f"   Response Preview: {row[7]}...")
        else:
            print("   ❌ No API logging data found in ORDER_LIST_LINES")
        
        print("\n📈 API Logging Summary:")
        print("=" * 60)
        
        # Count total API logged records
        cursor.execute('''
            SELECT COUNT(*) as header_count 
            FROM [FACT_ORDER_LIST] 
            WHERE [api_operation_type] IS NOT NULL
        ''')
        header_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) as line_count 
            FROM [ORDER_LIST_LINES] 
            WHERE [api_operation_type] IS NOT NULL
        ''')
        line_count = cursor.fetchone()[0]
        
        print(f"   Headers with API logging: {header_count}")
        print(f"   Lines with API logging: {line_count}")
        print(f"   Total records with API logging: {header_count + line_count}")
        
        # Check for different operation types
        cursor.execute('''
            SELECT [api_operation_type], COUNT(*) as count
            FROM (
                SELECT [api_operation_type] FROM [ORDER_LIST] WHERE [api_operation_type] IS NOT NULL
                UNION ALL
                SELECT [api_operation_type] FROM [ORDER_LIST_LINES] WHERE [api_operation_type] IS NOT NULL
            ) combined
            GROUP BY [api_operation_type]
            ORDER BY count DESC
        ''')
        operations = cursor.fetchall()
        
        if operations:
            print(f"\n   Operations captured:")
            for op, count in operations:
                print(f"     {op}: {count} records")
        
        # Check for different statuses
        cursor.execute('''
            SELECT [api_status], COUNT(*) as count
            FROM (
                SELECT [api_status] FROM [ORDER_LIST] WHERE [api_status] IS NOT NULL
                UNION ALL
                SELECT [api_status] FROM [ORDER_LIST_LINES] WHERE [api_status] IS NOT NULL
            ) combined
            GROUP BY [api_status]
            ORDER BY count DESC
        ''')
        statuses = cursor.fetchall()
        
        if statuses:
            print(f"\n   Status breakdown:")
            for status, count in statuses:
                print(f"     {status}: {count} records")
        
        cursor.close()
    
    print("\n✅ API Logging Data Check Complete!")

if __name__ == "__main__":
    main()
