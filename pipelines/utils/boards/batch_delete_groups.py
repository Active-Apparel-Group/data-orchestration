#!/usr/bin/env python3
"""
Batch Delete Monday.com Groups
=============================
Purpose: Get all groups from a Monday.com board and batch delete them (10 at a time)
Usage: python tests/debug/batch_delete_groups.py --board-id YOUR_BOARD_ID [--dry-run]

SAFETY FEATURES:
- Dry run mode by default
- Batch processing (10 groups at a time)
- Progress tracking and logging
- Error handling with retries
- Confirmation prompts for live execution
"""

import sys
import asyncio
import aiohttp
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import time

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.integrations.monday.graphql_loader import GraphQLLoader

logger = logger.get_logger(__name__)

class MondayGroupBatchDeleter:
    """
    Batch delete Monday.com groups with safety features
    """
    
    def __init__(self, board_id: str, dry_run: bool = True, exclude_groups: list = None):
        """
        Initialize the batch deleter
        
        Args:
            board_id: Monday.com board ID
            dry_run: If True, simulate deletion without actual API calls
            exclude_groups: List of group IDs or titles to exclude from deletion
        """
        self.board_id = board_id
        self.dry_run = dry_run
        self.exclude_groups = exclude_groups or []
        self.batch_size = 10
        self.concurrent_batches = 3  # Number of batches to process concurrently
        self.delay_between_batches = 2.0  # seconds
        self.max_retries = 3
        
        # Load configuration
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config = DeltaSyncConfig.from_toml(config_path)
        
        # Get Monday.com API token
        self.api_token = self._get_api_token()
        self.api_url = "https://api.monday.com/v2"
        
        # Initialize GraphQL loader for templates
        self.graphql_loader = GraphQLLoader()
        
        logger.info(f"🗑️ Monday.com Group Batch Deleter initialized")
        logger.info(f"   Board ID: {self.board_id}")
        logger.info(f"   Dry Run: {self.dry_run}")
        logger.info(f"   Batch Size: {self.batch_size}")
        logger.info(f"   Concurrent Batches: {self.concurrent_batches}")
    
    def _get_api_token(self) -> str:
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
    
    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """
        Get all groups from the Monday.com board
        
        Returns:
            List of group dictionaries with id and title
        """
        logger.info(f"🔍 Fetching all groups from board {self.board_id}...")
        
        # GraphQL query to get all groups
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
        
        variables = {
            "boardId": self.board_id
        }
        
        try:
            response_data = await self._make_api_call(query, variables)
            
            if "data" in response_data and "boards" in response_data["data"]:
                boards = response_data["data"]["boards"]
                if boards and len(boards) > 0:
                    groups = boards[0].get("groups", [])
                    
                    # Filter out already deleted or archived groups
                    active_groups = [
                        group for group in groups 
                        if not group.get("deleted", False) and not group.get("archived", False)
                    ]
                    
                    # Filter out excluded groups
                    if self.exclude_groups:
                        original_count = len(active_groups)
                        active_groups = [
                            g for g in active_groups 
                            if g["id"] not in self.exclude_groups and g["title"] not in self.exclude_groups
                        ]
                        excluded_count = original_count - len(active_groups)
                        if excluded_count > 0:
                            logger.info(f"🚫 Excluded {excluded_count} groups from deletion")
                    
                    logger.info(f"✅ Found {len(active_groups)} active groups to delete")
                    for group in active_groups:
                        logger.info(f"   Group: {group['id']} - '{group['title']}'")
                    
                    return active_groups
                else:
                    logger.warning(f"No boards found for ID {self.board_id}")
                    return []
            else:
                logger.error(f"Unexpected response structure: {response_data}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch groups: {e}")
            raise
    
    async def delete_groups_batch(self, groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Delete a batch of groups
        
        Args:
            groups: List of group dictionaries to delete
            
        Returns:
            Batch deletion results
        """
        if self.dry_run:
            logger.info(f"🔬 DRY RUN: Would delete {len(groups)} groups:")
            for group in groups:
                logger.info(f"   Would delete: {group['id']} - '{group['title']}'")
            
            return {
                "success": True,
                "deleted_count": len(groups),
                "dry_run": True,
                "errors": []
            }
        
        logger.info(f"🗑️ Deleting batch of {len(groups)} groups...")
        
        results = {
            "success": True,
            "deleted_count": 0,
            "errors": [],
            "dry_run": False
        }
        
        for group in groups:
            try:
                success = await self._delete_single_group(group)
                if success:
                    results["deleted_count"] += 1
                    logger.info(f"✅ Deleted group: {group['id']} - '{group['title']}'")
                else:
                    results["errors"].append(f"Failed to delete group {group['id']}")
                    results["success"] = False
                
                # Small delay between individual deletions
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error deleting group {group['id']}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["success"] = False
        
        return results
    
    async def _delete_single_group(self, group: Dict[str, Any]) -> bool:
        """
        Delete a single group with retry logic
        
        Args:
            group: Group dictionary with id and title
            
        Returns:
            True if deletion was successful
        """
        group_id = group["id"]
        
        # GraphQL mutation to delete group
        mutation = """
        mutation DeleteGroup($boardId: ID!, $groupId: String!) {
          delete_group(board_id: $boardId, group_id: $groupId) {
            id
            deleted
          }
        }
        """
        
        variables = {
            "boardId": self.board_id,
            "groupId": group_id
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                response_data = await self._make_api_call(mutation, variables)
                
                if "data" in response_data and "delete_group" in response_data["data"]:
                    delete_result = response_data["data"]["delete_group"]
                    if delete_result and "id" in delete_result:
                        # Success is indicated by presence of id in response, not the deleted field
                        logger.info(f"✅ Successfully deleted group '{group['title']}' ({group_id})")
                        return True
                    else:
                        # Group couldn't be deleted 
                        logger.warning(f"⚠️  Group '{group['title']}' ({group_id}) could not be deleted")
                        return False
                else:
                    logger.error(f"Unexpected deletion response for group {group_id}: {response_data}")
                    return False
                    
            except Exception as e:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed for group {group_id}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All attempts failed for group {group_id}: {e}")
                    return False
        
        return False
    
    async def _make_api_call(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make GraphQL API call to Monday.com
        
        Args:
            query: GraphQL query or mutation
            variables: Query variables
            
        Returns:
            API response data
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    
                    # Check for GraphQL errors
                    if "errors" in response_data:
                        error_messages = [error.get("message", str(error)) for error in response_data["errors"]]
                        raise Exception(f"GraphQL errors: {'; '.join(error_messages)}")
                    
                    return response_data
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def batch_delete_all_groups(self) -> Dict[str, Any]:
        """
        Execute complete batch deletion workflow
        
        Returns:
            Complete deletion results
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Get all groups
            groups = await self.get_all_groups()
            
            if not groups:
                logger.info("🎉 No groups found to delete")
                return {
                    "success": True,
                    "total_groups": 0,
                    "deleted_count": 0,
                    "batches_processed": 0,
                    "errors": [],
                    "execution_time": (datetime.now() - start_time).total_seconds()
                }
            
            # Safety confirmation for live execution
            if not self.dry_run:
                print(f"\n⚠️  WARNING: About to delete {len(groups)} groups from board {self.board_id}")
                print("This action cannot be undone!")
                confirmation = input("Type 'DELETE' to confirm: ")
                
                if confirmation != "DELETE":
                    logger.info("❌ Deletion cancelled by user")
                    return {
                        "success": False,
                        "error": "Deletion cancelled by user",
                        "execution_time": (datetime.now() - start_time).total_seconds()
                    }
            
            # Step 2: Process groups in concurrent batches
            total_results = {
                "success": True,
                "total_groups": len(groups),
                "deleted_count": 0,
                "batches_processed": 0,
                "errors": [],
                "dry_run": self.dry_run
            }
            
            # Create all batches first
            all_batches = []
            for i in range(0, len(groups), self.batch_size):
                batch = groups[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                all_batches.append((batch, batch_num))
            
            total_batches = len(all_batches)
            logger.info(f"🚀 Processing {total_batches} batches with {self.concurrent_batches} concurrent batches")
            
            # Process batches in concurrent groups
            for i in range(0, len(all_batches), self.concurrent_batches):
                concurrent_batch_group = all_batches[i:i + self.concurrent_batches]
                group_start = i + 1
                group_end = min(i + self.concurrent_batches, total_batches)
                
                logger.info(f"🔄 Processing concurrent batch group {group_start}-{group_end}/{total_batches}")
                
                # Create async tasks for concurrent processing
                tasks = []
                for batch, batch_num in concurrent_batch_group:
                    logger.info(f"   📦 Batch {batch_num}: {len(batch)} groups")
                    task = asyncio.create_task(self.delete_groups_batch(batch))
                    tasks.append((task, batch_num, len(batch)))
                
                # Wait for all tasks in this concurrent group to complete
                results = await asyncio.gather(*[task for task, _, _ in tasks], return_exceptions=True)
                
                # Process results
                for (task, batch_num, batch_size), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Batch {batch_num} failed with exception: {result}")
                        total_results["errors"].append(f"Batch {batch_num} failed: {result}")
                        total_results["success"] = False
                    else:
                        # Aggregate results
                        total_results["deleted_count"] += result["deleted_count"]
                        total_results["batches_processed"] += 1
                        total_results["errors"].extend(result["errors"])
                        
                        if not result["success"]:
                            total_results["success"] = False
                        
                        logger.info(f"✅ Batch {batch_num} complete: {result['deleted_count']}/{batch_size} groups deleted")
                
                # Delay between concurrent batch groups (except for last group)
                if i + self.concurrent_batches < len(all_batches):
                    logger.info(f"⏳ Waiting {self.delay_between_batches}s before next concurrent batch group...")
                    await asyncio.sleep(self.delay_between_batches)
            
            # Final results
            execution_time = (datetime.now() - start_time).total_seconds()
            total_results["execution_time"] = execution_time
            
            if total_results["success"]:
                mode = "DRY RUN" if self.dry_run else "LIVE"
                logger.info(f"🎉 {mode} batch deletion completed successfully!")
            else:
                logger.error(f"❌ Batch deletion completed with errors: {len(total_results['errors'])} errors")
            
            logger.info(f"📊 Final Results:")
            logger.info(f"   Total groups: {total_results['total_groups']}")
            logger.info(f"   Deleted: {total_results['deleted_count']}")
            logger.info(f"   Batches processed: {total_results['batches_processed']}")
            logger.info(f"   Execution time: {execution_time:.2f}s")
            logger.info(f"   Errors: {len(total_results['errors'])}")
            
            return total_results
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Batch deletion failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Batch delete Monday.com groups")
    parser.add_argument("--board-id", required=True, help="Monday.com board ID")
    parser.add_argument("--execute", action="store_true", help="Execute deletions (default is dry run)")
    parser.add_argument("--exclude", help="Comma-delimited list of group IDs or titles to exclude from deletion")
    
    args = parser.parse_args()
    
    # Parse exclude list
    exclude_groups = []
    if args.exclude:
        exclude_groups = [item.strip() for item in args.exclude.split(",")]
        logger.info(f"🚫 Will exclude these groups: {exclude_groups}")
    
    # Determine dry run mode
    dry_run = not args.execute
    
    logger.info(f"🚀 Starting Monday.com Group Batch Deleter")
    logger.info(f"   Board ID: {args.board_id}")
    logger.info(f"   Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    
    try:
        deleter = MondayGroupBatchDeleter(args.board_id, dry_run=dry_run, exclude_groups=exclude_groups)
        results = await deleter.batch_delete_all_groups()
        
        if results["success"]:
            print(f"\n✅ Success! Processed {results.get('deleted_count', 0)} groups in {results.get('execution_time', 0):.2f}s")
        else:
            print(f"\n❌ Failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
