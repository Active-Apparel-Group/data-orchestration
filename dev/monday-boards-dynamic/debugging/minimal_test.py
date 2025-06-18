#!/usr/bin/env python3
"""
Minimal test to isolate the Item ID conversion issue
"""

import requests
import pandas as pd
import os

# Load Monday.com API token
API_TOKEN = os.getenv("MONDAY_API_TOKEN")
if not API_TOKEN:
    print("ERROR: MONDAY_API_TOKEN environment variable not set")
    exit(1)

# Simple test of process_items logic
def test_item_id_conversion():
    print("🧪 Testing Item ID conversion in isolation...")
    
    # Get one item from Monday.com API directly
    query = """
    query {
        boards(ids: 9200517329) {
            items_page(limit: 1) {
                items {
                    id
                    name
                    updated_at
                    group { title }
                }
            }
        }
    }
    """
    
    headers = {"Authorization": API_TOKEN, "Content-Type": "application/json"}
    response = requests.post("https://api.monday.com/v2", 
                           json={"query": query}, 
                           headers=headers)
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        return
    
    items = response.json()["data"]["boards"][0]["items_page"]["items"]
    item = items[0]
    
    print(f"Raw item['id']: {repr(item['id'])} (type: {type(item['id'])})")
    
    # Test the exact code from the generated script
    record = {
        "StyleKey": item["name"],
        "UpdateDate": item["updated_at"],
        "Group": item["group"]["title"],
        "Item ID": int(item["id"])  # Convert to integer for BIGINT compatibility
    }
    
    print(f"Record Item ID: {repr(record['Item ID'])} (type: {type(record['Item ID'])})")
    
    # Create DataFrame like in process_items
    records = [record]
    df = pd.DataFrame(records)
    
    print(f"DataFrame Item ID dtype: {df['Item ID'].dtype}")
    print(f"DataFrame Item ID value: {df['Item ID'].iloc[0]} (type: {type(df['Item ID'].iloc[0])})")

if __name__ == "__main__":
    test_item_id_conversion()
