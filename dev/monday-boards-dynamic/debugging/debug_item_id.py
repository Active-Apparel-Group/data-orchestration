#!/usr/bin/env python3
"""
Quick Item ID Analysis for Customer Master Schedule Board
"""

import os
import sys
import json
import requests
from pathlib import Path

# Repository root discovery
def find_repo_root():
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
import db_helper as db

config = db.load_config()
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_URL = "https://api.monday.com/v2"
HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": "2025-04",
    "Content-Type": "application/json"
}

def analyze_item_id_column():
    """Analyze the specific Item ID column issue"""
    
    query = '''
    query {
        boards(ids: [9200517329]) {
            items_page(limit: 10) {
                items {
                    id
                    name
                    column_values {
                        column {
                            id
                            title
                            type
                        }
                        value
                        text
                        ... on ItemIdValue { item_id }
                    }
                }
            }
        }
    }
    '''
    
    response = requests.post(API_URL, json={"query": query}, headers=HEADERS)
    data = response.json()
    
    print("🔍 ITEM ID ANALYSIS")
    print("=" * 50)
    
    items = data['data']['boards'][0]['items_page']['items']
    
    for i, item in enumerate(items[:3]):  # Check first 3 items
        print(f"\nItem {i+1}: {item['name']}")
        print(f"  Item.id: '{item['id']}' (type: {type(item['id'])})")
        
        for cv in item['column_values']:
            if cv['column']['title'] == 'Item ID':
                print(f"  Column Info:")
                print(f"    Title: {cv['column']['title']}")
                print(f"    Type: {cv['column']['type']}")
                print(f"    ID: {cv['column']['id']}")
                print(f"  Values:")
                print(f"    cv.value: '{cv.get('value')}' (type: {type(cv.get('value'))})")
                print(f"    cv.text: '{cv.get('text')}' (type: {type(cv.get('text'))})")
                print(f"    cv.item_id: '{cv.get('item_id')}' (type: {type(cv.get('item_id'))})")
                break

if __name__ == "__main__":
    analyze_item_id_column()
