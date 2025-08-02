#!/usr/bin/env python3
"""
Simple Monday.com Group Batch Deleter (Synchronous)
==================================================
Purpose: Simple script to batch delete groups from Monday.com board
Usage: python tests/debug/simple_batch_delete_groups.py --board-id YOUR_BOARD_ID [--execute]

SAFETY FEATURES:
- Dry run by default
- Confirmation prompts
- Batch processing
- Error handling
"""

import sys
import requests
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def get_api_token() -> str:
    """Get Monday.com API token using same pattern as monday_api_client"""
    import os
    
    try:
        # Use the same pattern as monday_api_client.py  
        config = db.load_config()
        api_token = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
        
        if not api_token or api_token == "your_monday_api_token_here":
            # Fallback to environment variable only
            api_token = os.getenv("MONDAY_API_KEY")
        
        if not api_token:
            raise ValueError("Monday.com API token not found. Set MONDAY_API_KEY environment variable or configure in db.load_config()")
        
        return api_token
        
    except Exception as e:
        logger.error(f"Failed to retrieve Monday.com API token: {e}")
        raise

def make_api_call(query: str, variables: Dict[str, Any], api_token: str) -> Dict[str, Any]:
    """Make GraphQL API call to Monday.com"""
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        return data
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

def get_all_groups(board_id: str, api_token: str) -> List[Dict[str, Any]]:
    """Get all groups from Monday.com board"""
    print(f"🔍 Fetching groups from board {board_id}...")
    
    query = """
    query GetBoardGroups($boardId: ID!) {
      boards(ids: [$boardId]) {
        groups {
          id
          title
          archived
          deleted
        }
      }
    }
    """
    
    variables = {"boardId": board_id}
    
    response = make_api_call(query, variables, api_token)
    
    if "data" in response and "boards" in response["data"]:
        boards = response["data"]["boards"]
        if boards and len(boards) > 0:
            groups = boards[0].get("groups", [])
            
            # Filter active groups only
            active_groups = [
                group for group in groups 
                if not group.get("deleted", False) and not group.get("archived", False)
            ]
            
            print(f"✅ Found {len(active_groups)} active groups:")
            for i, group in enumerate(active_groups, 1):
                print(f"   {i}. {group['id']} - '{group['title']}'")
            
            return active_groups
        else:
            print(f"❌ No boards found for ID {board_id}")
            return []
    else:
        raise Exception(f"Unexpected response: {response}")

def delete_group(board_id: str, group_id: str, api_token: str) -> bool:
    """Delete a single group"""
    mutation = """
    mutation DeleteGroup($boardId: ID!, $groupId: String!) {
      delete_group(board_id: $boardId, group_id: $groupId) {
        id
        deleted
      }
    }
    """
    
    variables = {
        "boardId": board_id,
        "groupId": group_id
    }
    
    try:
        response = make_api_call(mutation, variables, api_token)
        
        if "data" in response and "delete_group" in response["data"]:
            result = response["data"]["delete_group"]
            # Success is indicated by presence of id in response, not the deleted field
            return result and "id" in result
        else:
            print(f"❌ Unexpected response for group {group_id}: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to delete group {group_id}: {e}")
        return False

def batch_delete_groups(board_id: str, groups: List[Dict[str, Any]], api_token: str, dry_run: bool = True) -> Dict[str, Any]:
    """Delete groups in batches"""
    batch_size = 10
    total_groups = len(groups)
    
    if dry_run:
        print(f"\n🔬 DRY RUN MODE: Would delete {total_groups} groups")
        return {
            "success": True,
            "deleted_count": total_groups,
            "dry_run": True
        }
    
    # Confirmation for live execution
    print(f"\n⚠️  WARNING: About to delete {total_groups} groups from board {board_id}")
    print("This action CANNOT be undone!")
    confirmation = input("Type 'DELETE' to confirm: ")
    
    if confirmation != "DELETE":
        print("❌ Deletion cancelled")
        return {"success": False, "error": "Cancelled by user"}
    
    print(f"\n🗑️  Starting deletion of {total_groups} groups...")
    
    deleted_count = 0
    errors = []
    
    for i in range(0, total_groups, batch_size):
        batch = groups[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_groups + batch_size - 1) // batch_size
        
        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} groups)...")
        
        for group in batch:
            group_id = group["id"]
            group_title = group["title"]
            
            print(f"   Deleting: {group_id} - '{group_title}'")
            
            success = delete_group(board_id, group_id, api_token)
            
            if success:
                deleted_count += 1
                print(f"   ✅ Deleted successfully")
            else:
                error_msg = f"Failed to delete group {group_id}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Small delay between deletions
            time.sleep(0.5)
        
        print(f"✅ Batch {batch_num} complete: {deleted_count}/{i + len(batch)} total deleted")
        
        # Delay between batches
        if i + batch_size < total_groups:
            print("⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    return {
        "success": len(errors) == 0,
        "deleted_count": deleted_count,
        "errors": errors,
        "dry_run": False
    }

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Batch delete Monday.com groups")
    parser.add_argument("--board-id", required=True, help="Monday.com board ID")
    parser.add_argument("--execute", action="store_true", 
                       help="Execute real deletion (default is dry run)")
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    mode = "DRY RUN" if dry_run else "LIVE EXECUTION"
    
    print(f"🚀 Monday.com Group Batch Deleter")
    print(f"   Board ID: {args.board_id}")
    print(f"   Mode: {mode}")
    
    try:
        # Get API token
        api_token = get_api_token()
        
        # Get all groups
        groups = get_all_groups(args.board_id, api_token)
        
        if not groups:
            print("🎉 No groups found to delete")
            return 0
        
        # Execute batch deletion
        start_time = datetime.now()
        results = batch_delete_groups(args.board_id, groups, api_token, dry_run)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Final results
        if results["success"]:
            print(f"\n🎉 {mode} completed successfully!")
            print(f"   Groups processed: {results['deleted_count']}")
            print(f"   Execution time: {execution_time:.2f}s")
        else:
            print(f"\n❌ Deletion failed")
            if "error" in results:
                print(f"   Error: {results['error']}")
            if "errors" in results:
                print(f"   Individual errors: {len(results['errors'])}")
            return 1
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
