#!/usr/bin/env python3
"""
Simple Monday.com Group Deletion Script
Handles groups that can't be deleted gracefully
"""

import sys
from pathlib import Path
import requests
import json
import time

# Add repo root and src to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

class SimpleGroupDeleter:
    def __init__(self, board_id: str, dry_run: bool = True, exclude_groups: list = None):
        self.board_id = board_id
        self.dry_run = dry_run
        self.exclude_groups = exclude_groups or []
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self._get_api_token()}",
            "Content-Type": "application/json"
        }
    
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
            logger.error(f"Failed to get API token: {e}")
            raise
    
    def fetch_groups(self):
        """Fetch all groups from the board"""
        query = """
        query GetBoardGroups($boardId: ID!) {
          boards(ids: [$boardId]) {
            groups {
              id
              title
              items_page {
                items {
                  id
                  name
                }
              }
            }
          }
        }
        """
        
        variables = {"boardId": self.board_id}
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            
            groups = data["data"]["boards"][0]["groups"]
            
            # Filter out excluded groups
            if self.exclude_groups:
                original_count = len(groups)
                groups = [g for g in groups if g["id"] not in self.exclude_groups and g["title"] not in self.exclude_groups]
                excluded_count = original_count - len(groups)
                if excluded_count > 0:
                    logger.info(f"🚫 Excluded {excluded_count} groups from deletion")
            
            logger.info(f"📋 Found {len(groups)} groups to process")
            
            # Show group details
            for group in groups:
                item_count = len(group.get("items_page", {}).get("items", []))
                logger.info(f"   {group['id']}: '{group['title']}' ({item_count} items)")
            
            return groups
            
        except Exception as e:
            logger.error(f"Failed to fetch groups: {e}")
            return []
    
    def delete_group(self, group_id: str, group_title: str) -> bool:
        """Delete a single group"""
        if self.dry_run:
            logger.info(f"🔬 DRY RUN: Would delete group '{group_title}' ({group_id})")
            return True
        
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
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": mutation, "variables": variables},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"❌ GraphQL error deleting '{group_title}': {data['errors']}")
                return False
            
            result = data["data"]["delete_group"]
            if result and "id" in result:
                # Success is indicated by presence of id in response, not the deleted field
                logger.info(f"✅ Successfully deleted: '{group_title}' ({group_id})")
                return True
            else:
                logger.warning(f"⚠️  Could not delete '{group_title}' ({group_id}) - API returned null result")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error deleting '{group_title}': {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error deleting '{group_title}': {e}")
            return False
    
    def delete_all_groups(self):
        """Delete all groups with progress tracking"""
        groups = self.fetch_groups()
        
        if not groups:
            logger.warning("⚠️  No groups found to delete")
            return
        
        # Confirmation for live execution
        if not self.dry_run:
            print(f"\n⚠️  WARNING: About to delete {len(groups)} groups from board {self.board_id}")
            print("This action cannot be undone!")
            confirm = input("Type 'DELETE' to confirm: ")
            if confirm != "DELETE":
                logger.info("❌ Deletion cancelled by user")
                return
        
        logger.info(f"🚀 Starting deletion of {len(groups)} groups...")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, group in enumerate(groups, 1):
            try:
                logger.info(f"📝 Processing {i}/{len(groups)}: '{group['title']}'")
                
                # Check if group has items
                item_count = len(group.get("items_page", {}).get("items", []))
                if item_count > 0:
                    logger.info(f"   📊 Group has {item_count} items - attempting deletion...")
                
                success = self.delete_group(group["id"], group["title"])
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                
                # Small delay between deletions
                if not self.dry_run:
                    time.sleep(1)
                
            except KeyboardInterrupt:
                logger.warning("⚠️  Deletion interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error processing '{group['title']}': {e}")
                failed_count += 1
                continue
        
        # Final summary
        logger.info(f"\n📊 Deletion Summary:")
        logger.info(f"   ✅ Successful: {success_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        logger.info(f"   📝 Total processed: {success_count + failed_count}")
        
        if self.dry_run:
            logger.info("🔬 This was a DRY RUN - no actual deletions occurred")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Monday.com Group Deleter")
    parser.add_argument("--board-id", required=True, help="Monday.com board ID")
    parser.add_argument("--execute", action="store_true", help="Execute deletions (default is dry run)")
    parser.add_argument("--exclude", help="Comma-delimited list of group IDs or titles to exclude from deletion")
    
    args = parser.parse_args()
    
    # Parse exclude list
    exclude_groups = []
    if args.exclude:
        exclude_groups = [item.strip() for item in args.exclude.split(",")]
        logger.info(f"🚫 Will exclude these groups: {exclude_groups}")
    
    # Determine mode
    dry_run = not args.execute
    mode = "DRY RUN" if dry_run else "LIVE EXECUTION"
    
    logger.info(f"🚀 Starting Simple Monday.com Group Deleter")
    logger.info(f"   Board ID: {args.board_id}")
    logger.info(f"   Mode: {mode}")
    
    try:
        deleter = SimpleGroupDeleter(args.board_id, dry_run=dry_run, exclude_groups=exclude_groups)
        deleter.delete_all_groups()
        
        logger.info("✅ Script completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("⚠️  Script interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
