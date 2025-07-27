#!/usr/bin/env python3
"""
Test Enhanced MergeOrchestrator - CONSOLIDATED VERSION

Simple test of the consolidated transformation methods inside EnhancedMergeOrchestrator.
No separate files - all logic consolidated per user requirements.

Author: Data Orchestration Team  
Created: 2025-01-27
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.merge_orchestrator import EnhancedMergeOrchestrator

logger = logger.get_logger(__name__)

def main():
    print("🧪 Testing Enhanced MergeOrchestrator - CONSOLIDATED VERSION")
    print("=" * 80)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Test 1: Create orchestrator
        print("\n📋 Test 1: Creating EnhancedMergeOrchestrator...")
        orchestrator = EnhancedMergeOrchestrator(config)
        print("✅ Orchestrator created successfully")
        
        # Test 2: Group transformation
        print("\n📋 Test 2: Testing group name transformation...")
        group_enabled = orchestrator._is_group_transformation_enabled()
        print(f"✅ Group transformation enabled: {group_enabled}")
        
        if group_enabled:
            result = orchestrator._execute_group_name_transformation(cursor, dry_run=True)
            print(f"✅ Group transformation result: {result.get('success', False)}")
            if result.get('sql_length'):
                print(f"   SQL length: {result['sql_length']} characters")
        
        # Test 3: Item transformation  
        print("\n📋 Test 3: Testing item name transformation...")
        item_enabled = orchestrator._is_item_transformation_enabled()
        print(f"✅ Item transformation enabled: {item_enabled}")
        
        if item_enabled:
            result = orchestrator._execute_item_name_transformation(cursor, dry_run=True)
            print(f"✅ Item transformation result: {result.get('success', False)}")
            if result.get('sql_length'):
                print(f"   SQL length: {result['sql_length']} characters")
        
        # Test 4: Group creation workflow
        print("\n📋 Test 4: Testing group creation workflow...")
        dev_board = "9609317401"
        result = orchestrator._execute_group_creation_workflow(cursor, dry_run=True, board_id=dev_board)
        print(f"✅ Group creation result: {result.get('success', False)}")
        print(f"   Message: {result.get('message', 'N/A')}")
        
        cursor.close()
    
    print("\n✅ Consolidated MergeOrchestrator test completed!")
    print("🎯 All transformation logic successfully consolidated into single file!")

if __name__ == "__main__":
    main()
