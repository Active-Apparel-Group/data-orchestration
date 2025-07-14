#!/usr/bin/env python3
"""
Board Inspector - Get basic information about a Monday.com board
"""

import os
import sys
import json
import requests
from pathlib import Path

# Find repository root and add utils to path
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db

# Load configuration
config = db.load_config()

# Monday.com API settings
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
API_VER = "2025-04"
API_URL = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")

if not MONDAY_TOKEN or MONDAY_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
    raise ValueError("Monday.com API token not configured")

HEADERS = {
    "Authorization": f"Bearer {MONDAY_TOKEN}",
    "API-Version": API_VER,
    "Content-Type": "application/json"
}

def inspect_board(board_id):
    """Get basic information about a board"""
    
    query = f"""
    query {{
        boards(ids: [{board_id}]) {{
            id
            name
            description
            state
            board_kind
            items_count
            groups {{
                id
                title
                color
            }}
            columns {{
                id
                title
                type
                settings_str
            }}
        }}
    }}
    """
    
    try:
        response = requests.post(API_URL, json={"query": query}, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        if 'errors' in data:
            print("❌ Monday.com API errors:", data['errors'])
            return None
        
        if not data['data']['boards']:
            print(f"❌ Board {board_id} not found or not accessible")
            return None
            
        board = data['data']['boards'][0]
        
        print(f"📋 BOARD INFORMATION")
        print(f"ID: {board['id']}")
        print(f"Name: {board['name']}")
        print(f"Description: {board.get('description', 'N/A')}")
        print(f"State: {board['state']}")
        print(f"Kind: {board['board_kind']}")
        print(f"Items Count: {board['items_count']}")
        
        print(f"\n📁 GROUPS ({len(board['groups'])}):")
        for group in board['groups']:
            print(f"  - {group['title']} (ID: {group['id']}, Color: {group['color']})")
        
        print(f"\n📊 COLUMNS ({len(board['columns'])}):")
        for col in board['columns']:
            print(f"  - {col['title']} (ID: {col['id']}, Type: {col['type']})")
            
        return board
        
    except Exception as e:
        print(f"❌ Error inspecting board: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        board_id = sys.argv[1]
    else:
        board_id = input("Enter board ID: ")
    
    inspect_board(board_id)
