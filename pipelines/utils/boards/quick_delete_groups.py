#!/usr/bin/env python3
"""
Quick Monday.com Group Deleter using existing infrastructure
==========================================================
Purpose: Delete all groups from Monday.com board using existing monday_api_client
Usage: python tests/debug/quick_delete_groups.py [--board-id BOARD_ID] [--execute]

Uses existing infrastructure:
- MondayAPIClient for API calls
- Existing configuration and logging
- Built-in retry logic and error handling
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

def get_all_groups_from_board(board_id: str) -> List[Dict[str, Any]]:
    """Get all groups using direct API call"""
    import os
    
    # Get API token using same pattern as monday_api_client.py
    try:
        config = db.load_config()
        api_token = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
        
        if not api_token or api_token == "your_monday_api_token_here":
            # Fallback to environment variable only
            api_token = os.getenv("MONDAY_API_KEY")
        
        if not api_token:
            raise ValueError("Monday.com API token not found. Set MONDAY_API_KEY environment variable or configure in db.load_config()")
        
    except Exception as e:
        logger.error(f"Failed to retrieve Monday.com API token: {e}")
        raise
    
    # Direct GraphQL query
    import requests
    
    query = f"""
    query {{
      boards(ids: {board_id}) {{
        groups {{
          id
          title
          archived
          deleted
        }}
      }}
    }}
    """
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.monday.com/v2",
        headers=headers,
        json={"query": query},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        if "data" in data and "boards" in data["data"]:
            boards = data["data"]["boards"]
            if boards and len(boards) > 0:
                groups = boards[0].get("groups", [])
                
                # Filter active groups
                active_groups = [
                    group for group in groups 
                    if not group.get("deleted", False) and not group.get("archived", False)
                ]
                
                return active_groups
        
        return []
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

def delete_groups_batch(board_id: str, groups: List[Dict[str, Any]], dry_run: bool = True) -> Dict[str, Any]:
    """Delete groups in batches using direct API calls"""
    import os
    
    # Get API token using same pattern as monday_api_client.py
    try:
        config = db.load_config()
        api_token = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
        
        if not api_token or api_token == "your_monday_api_token_here":
            # Fallback to environment variable only
            api_token = os.getenv("MONDAY_API_KEY")
        
        if not api_token:
            raise ValueError("Monday.com API token not found. Set MONDAY_API_KEY environment variable or configure in db.load_config()")
        
    except Exception as e:
        logger.error(f"Failed to retrieve Monday.com API token: {e}")
        raise
    
    import requests
    import time
    
    if dry_run:
        logger.info(f"🔬 DRY RUN: Would delete {len(groups)} groups:")
        for group in groups:
            logger.info(f"   Would delete: {group['id']} - '{group['title']}'")
        return {"success": True, "deleted_count": len(groups), "dry_run": True}
    
    # Confirmation for live execution
    print(f"\n⚠️  WARNING: About to delete {len(groups)} groups from board {board_id}")
    print("This action CANNOT be undone!")
    confirmation = input("Type 'DELETE' to confirm: ")
    
    if confirmation != "DELETE":
        logger.info("❌ Deletion cancelled by user")
        return {"success": False, "error": "Cancelled by user"}
    
    logger.info(f"🗑️ Starting deletion of {len(groups)} groups...")
    
    deleted_count = 0
    errors = []
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Process in batches of 10
    batch_size = 10
    for i in range(0, len(groups), batch_size):
        batch = groups[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(groups) + batch_size - 1) // batch_size
        
        logger.info(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} groups)...")
        
        for group in batch:
            group_id = group["id"]
            group_title = group["title"]
            
            # GraphQL mutation for individual deletion
            mutation = f"""
            mutation {{
              delete_group(board_id: {board_id}, group_id: "{group_id}") {{
                id
                deleted
              }}
            }}
            """
            
            try:
                response = requests.post(
                    "https://api.monday.com/v2",
                    headers=headers,
                    json={"query": mutation},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        error_msg = f"GraphQL error deleting {group_id}: {data['errors']}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                    elif "data" in data and "delete_group" in data["data"]:
                        result = data["data"]["delete_group"]
                        if result and result.get("deleted", False):
                            deleted_count += 1
                            logger.info(f"✅ Deleted: {group_id} - '{group_title}'")
                        else:
                            error_msg = f"Deletion failed for {group_id}: {result}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                    else:
                        error_msg = f"Unexpected response for {group_id}: {data}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                else:
                    error_msg = f"HTTP error deleting {group_id}: {response.status_code} {response.text}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                
                # Small delay between deletions
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Exception deleting {group_id}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"✅ Batch {batch_num} complete")
        
        # Delay between batches
        if i + batch_size < len(groups):
            logger.info("⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    return {
        "success": len(errors) == 0,
        "deleted_count": deleted_count,
        "errors": errors,
        "dry_run": False
    }

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Quick delete Monday.com groups")
    parser.add_argument("--board-id", default="9609317401", 
                       help="Monday.com board ID (default: 9609317401)")
    parser.add_argument("--execute", action="store_true", 
                       help="Execute real deletion (default is dry run)")
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    mode = "DRY RUN" if dry_run else "LIVE EXECUTION"
    
    logger.info(f"🚀 Quick Monday.com Group Deleter")
    logger.info(f"   Board ID: {args.board_id}")
    logger.info(f"   Mode: {mode}")
    
    try:
        # Step 1: Get all groups
        start_time = datetime.now()
        groups = get_all_groups_from_board(args.board_id)
        
        if not groups:
            logger.info("🎉 No groups found to delete")
            return 0
        
        logger.info(f"📋 Found {len(groups)} groups to process:")
        for i, group in enumerate(groups, 1):
            logger.info(f"   {i}. {group['id']} - '{group['title']}'")
        
        # Step 2: Delete groups
        results = delete_groups_batch(args.board_id, groups, dry_run)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Final results
        if results["success"]:
            logger.info(f"🎉 {mode} completed successfully!")
            logger.info(f"   Groups processed: {results['deleted_count']}")
            logger.info(f"   Execution time: {execution_time:.2f}s")
        else:
            logger.error(f"❌ Deletion completed with issues")
            if "error" in results:
                logger.error(f"   Error: {results['error']}")
            if "errors" in results:
                logger.error(f"   Individual errors: {len(results['errors'])}")
                for error in results["errors"][:5]:  # Show first 5 errors
                    logger.error(f"     - {error}")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
