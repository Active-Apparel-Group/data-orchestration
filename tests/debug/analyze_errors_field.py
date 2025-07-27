#!/usr/bin/env python3
"""
Analyze the 'errors' field in API responses to understand why headers are marked as ERROR
"""

import sys
from pathlib import Path
import json

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🔍 Analyzing 'errors' field in Monday.com API responses...")
    
    with db.get_connection("orders") as connection:
        cursor = connection.cursor()
        
        # Get the most recent header responses marked as ERROR
        query = """
        
        SELECT TOP 5
            [AAG ORDER NUMBER],
            api_operation_type,
            api_request_payload,
            api_response_payload
        FROM [FACT_ORDER_LIST]
        WHERE api_status = 'ERROR'
        AND api_response_payload IS NOT NULL
        ORDER BY sync_completed_at DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"\n📊 Found {len(results)} recent ERROR responses to analyze:")
        print("=" * 80)
        
        for i, row in enumerate(results, 1):
            order_number = row[0]
            operation = row[1]
            request_str = row[2]
            response_str = row[3]
            
            print(f"\n🔍 Response {i}: {order_number} ({operation})")
            print(f"   Status: ERROR (from WHERE clause)")
            
            try:
                # Parse the response JSON
                response = json.loads(response_str)
                
                print(f"   Response type: {type(response)}")
                print(f"   Response keys: {list(response.keys())}")
                
                # Check for 'success' field
                if 'success' in response:
                    print(f"   'success' field: {response['success']}")
                
                # Check for 'errors' field and its content
                if 'errors' in response:
                    errors = response['errors']
                    print(f"   'errors' field present: {type(errors)}")
                    print(f"   'errors' content: {errors}")
                    print(f"   'errors' is empty: {not errors}")
                    print(f"   'errors' length: {len(errors) if errors else 0}")
                else:
                    print("   'errors' field: NOT PRESENT")
                
                # Show key parts of response
                print(f"   Full response preview: {str(response)[:200]}...")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Failed to parse response JSON: {e}")
                print(f"   Raw response: {response_str[:200]}...")
            
            print("-" * 80)
        
        cursor.close()

if __name__ == "__main__":
    main()
