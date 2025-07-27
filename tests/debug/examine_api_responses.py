#!/usr/bin/env python3
"""
Examine API Response Data - Deep dive into Monday.com API logging responses
"""

import sys
import json
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🔍 Examining Monday.com API Response Data...")
    
    # Database connection
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        print("\n📊 Detailed API Response Analysis:")
        print("=" * 80)
        
        # Get the most recent API logging entries with full response data
        cursor.execute('''
            SELECT TOP 3
                [line_uuid],
                [monday_subitem_id],
                [api_operation_type],
                [api_request_timestamp],
                [api_response_timestamp],
                [api_status],
                [api_request_payload],
                [api_response_payload]
            FROM [ORDER_LIST_LINES] 
            WHERE [api_operation_type] IS NOT NULL 
            ORDER BY [api_request_timestamp] DESC
        ''')
        
        records = cursor.fetchall()
        
        for i, record in enumerate(records, 1):
            line_uuid = record[0]
            subitem_id = record[1]
            operation = record[2]
            req_time = record[3]
            resp_time = record[4]
            status = record[5]
            request_payload = record[6]
            response_payload = record[7]
            
            print(f"\n🔍 Record {i}:")
            print(f"   Line UUID: {str(line_uuid)[:8]}...")
            print(f"   Monday Subitem ID: {subitem_id}")
            print(f"   Operation: {operation}")
            print(f"   Status: {status}")
            print(f"   Request Time: {req_time}")
            print(f"   Response Time: {resp_time}")
            
            print(f"\n📤 REQUEST PAYLOAD:")
            if request_payload:
                try:
                    # Try to parse as JSON for pretty printing
                    if request_payload.strip().startswith('[') or request_payload.strip().startswith('{'):
                        parsed_request = json.loads(request_payload)
                        print(json.dumps(parsed_request, indent=2)[:500] + "..." if len(str(parsed_request)) > 500 else json.dumps(parsed_request, indent=2))
                    else:
                        print(f"   Raw: {request_payload[:500]}..." if len(request_payload) > 500 else request_payload)
                except json.JSONDecodeError:
                    print(f"   Raw: {request_payload[:500]}..." if len(request_payload) > 500 else request_payload)
            else:
                print("   ❌ No request payload")
            
            print(f"\n📥 RESPONSE PAYLOAD:")
            if response_payload:
                try:
                    # Try to parse as JSON for pretty printing
                    if response_payload.strip().startswith('[') or response_payload.strip().startswith('{'):
                        parsed_response = json.loads(response_payload)
                        print(json.dumps(parsed_response, indent=2)[:500] + "..." if len(str(parsed_response)) > 500 else json.dumps(parsed_response, indent=2))
                    else:
                        print(f"   Raw: {response_payload[:500]}..." if len(response_payload) > 500 else response_payload)
                except json.JSONDecodeError:
                    print(f"   Raw: {response_payload[:500]}..." if len(response_payload) > 500 else response_payload)
            else:
                print("   ❌ No response payload")
            
            print("-" * 80)
        
        # Check if there are any records with successful responses
        print("\n📈 Response Status Analysis:")
        cursor.execute('''
            SELECT [api_status], COUNT(*) as count
            FROM [ORDER_LIST_LINES] 
            WHERE [api_operation_type] IS NOT NULL
            GROUP BY [api_status]
            ORDER BY count DESC
        ''')
        
        statuses = cursor.fetchall()
        for status, count in statuses:
            print(f"   {status}: {count} records")
        
        # Check for any non-empty response payloads
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM [ORDER_LIST_LINES] 
            WHERE [api_operation_type] IS NOT NULL 
            AND [api_response_payload] IS NOT NULL 
            AND [api_response_payload] != '' 
            AND [api_response_payload] != '{}'
        ''')
        
        non_empty_responses = cursor.fetchone()[0]
        print(f"\n   Records with non-empty responses: {non_empty_responses}")
        
        # Check the header table too
        print("\n📊 Checking Header Table (FACT_ORDER_LIST):")
        cursor.execute('''
            SELECT TOP 3
                [AAG ORDER NUMBER],
                [monday_item_id],
                [api_operation_type],
                [api_status],
                [api_request_payload],
                [api_response_payload]
            FROM [FACT_ORDER_LIST] 
            WHERE [api_operation_type] IS NOT NULL 
            ORDER BY [api_request_timestamp] DESC
        ''')
        
        headers = cursor.fetchall()
        if headers:
            for i, header in enumerate(headers, 1):
                print(f"\n🔍 Header {i}:")
                print(f"   Order: {header[0]}")
                print(f"   Monday Item ID: {header[1]}")
                print(f"   Operation: {header[2]}")
                print(f"   Status: {header[3]}")
                
                if header[4]:  # request payload
                    print(f"   Request: {header[4][:100]}..." if len(str(header[4])) > 100 else header[4])
                if header[5]:  # response payload
                    print(f"   Response: {header[5][:100]}..." if len(str(header[5])) > 100 else header[5])
        else:
            print("   ❌ No API logging data found in FACT_ORDER_LIST")
        
        cursor.close()
    
    print("\n✅ API Response Analysis Complete!")

if __name__ == "__main__":
    main()
