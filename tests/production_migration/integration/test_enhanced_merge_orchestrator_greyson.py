#!/usr/bin/env python3
"""
Enhanced Merge Orchestrator - GREYSON PO 4755 Transformation
===========================================================
Purpose: Run Enhanced Merge Orchestrator transformations on GREYSON PO 4755 data
Location: tests/production_migration/integration/test_enhanced_merge_orchestrator_greyson.py
Created: 2025-07-29

This runs the PROPER transformations that populate group_name and item_name 
BEFORE the CLI attempts to sync to Monday.com.

Order of Operations:
1. Enhanced Merge Orchestrator data preparation (Steps 1-6)
2. Enhanced Merge Orchestrator transformations (group_name, item_name)
3. CLI sync (with properly populated fields)
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.merge_orchestrator import EnhancedMergeOrchestrator

logger = logger.get_logger(__name__)

def main():
    print("🔧 Enhanced Merge Orchestrator - GREYSON PO 4755 Transformation")
    print("=" * 70)
    
    try:
        # Initialize configuration
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Initialize Enhanced Merge Orchestrator
        orchestrator = EnhancedMergeOrchestrator(config)
        
        print(f"📋 Configuration:")
        print(f"   Target table: {config.target_table}")
        print(f"   Lines table: {config.lines_table}")
        print(f"   Database: {config.db_key}")
        
        # Check current GREYSON data state BEFORE transformation
        print(f"\n📊 GREYSON PO 4755 Status BEFORE Transformation:")
        check_greyson_status()
        
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Step 1: Data Preparation Sequence (SQL Steps 1-6)
            print(f"\n🧹 Step 1: Data Preparation Sequence")
            print("-" * 40)
            
            prep_result = orchestrator._execute_data_preparation_sequence(cursor, dry_run=False)
            
            if prep_result['success']:
                print(f"✅ Data preparation completed: {prep_result['operations_completed']} operations")
                for result in prep_result.get('results', []):
                    if 'rows_affected' in result:
                        print(f"   {result['file']}: {result['rows_affected']} rows affected")
                    elif 'validation_rows' in result:
                        print(f"   {result['file']}: {result['validation_rows']} validation rows")
            else:
                print(f"❌ Data preparation failed: {prep_result.get('error', 'Unknown error')}")
                return {'success': False, 'error': prep_result.get('error')}
            
            # Step 2: Group Name Transformation
            print(f"\n🏷️ Step 2: Group Name Transformation")
            print("-" * 40)
            
            group_result = orchestrator._execute_group_name_transformation(cursor, dry_run=False)
            
            if group_result['success']:
                print(f"✅ Group name transformation completed")
                print(f"   Pattern: {group_result.get('pattern', 'N/A')}")
                print(f"   SQL length: {group_result.get('sql_length', 0)} characters")
            else:
                print(f"❌ Group name transformation failed: {group_result.get('error', 'Unknown error')}")
            
            # Step 3: Item Name Transformation
            print(f"\n📦 Step 3: Item Name Transformation")
            print("-" * 40)
            
            item_result = orchestrator._execute_item_name_transformation(cursor, dry_run=False)
            
            if item_result['success']:
                print(f"✅ Item name transformation completed")
                print(f"   Format: {item_result.get('format', 'N/A')}")
                print(f"   SQL length: {item_result.get('sql_length', 0)} characters")
            else:
                print(f"❌ Item name transformation failed: {item_result.get('error', 'Unknown error')}")
            
            # Commit all transformations
            connection.commit()
            
        # Check GREYSON data state AFTER transformation
        print(f"\n📊 GREYSON PO 4755 Status AFTER Transformation:")
        check_greyson_status()
        
        print(f"\n🎉 Enhanced Merge Orchestrator Transformation Complete!")
        print(f"✅ GREYSON PO 4755 data is now ready for CLI sync")
        
        return {
            'success': True,
            'data_preparation': prep_result,
            'group_transformation': group_result,
            'item_transformation': item_result
        }
        
    except Exception as e:
        logger.exception(f"Enhanced Merge Orchestrator transformation failed: {e}")
        return {'success': False, 'error': str(e)}

def check_greyson_status():
    """Check the current status of GREYSON PO 4755 records"""
    try:
        with db.get_connection('orders') as connection:
            cursor = connection.cursor()
            
            # Check key fields that should be populated by transformations
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN [group_name] IS NOT NULL THEN 1 END) as has_group_name,
                    COUNT(CASE WHEN [item_name] IS NOT NULL THEN 1 END) as has_item_name,
                    COUNT(CASE WHEN [CUSTOMER NAME] = 'GREYSON' THEN 1 END) as canonical_customer,
                    COUNT(CASE WHEN [sync_state] = 'PENDING' THEN 1 END) as pending_sync
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
            """)
            
            result = cursor.fetchone()
            total, group_names, item_names, canonical, pending = result
            
            print(f"   Total records: {total}")
            print(f"   Has group_name: {group_names} ({group_names/total*100:.1f}%)")
            print(f"   Has item_name: {item_names} ({item_names/total*100:.1f}%)")
            print(f"   Canonical customer (GREYSON): {canonical} ({canonical/total*100:.1f}%)")
            print(f"   Pending sync: {pending}")
            
            # Show sample group_name and item_name values
            cursor.execute("""
                SELECT TOP 3 
                    [CUSTOMER NAME],
                    [group_name],
                    [item_name],
                    [AAG ORDER NUMBER]
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                ORDER BY [AAG ORDER NUMBER]
            """)
            
            samples = cursor.fetchall()
            print(f"\n   Sample transformed data:")
            for customer, group, item, order in samples:
                print(f"     {customer} | {group} | {item} | {order}")
                
    except Exception as e:
        logger.exception(f"Failed to check GREYSON status: {e}")

if __name__ == "__main__":
    result = main()
    if result['success']:
        print(f"\n🚀 Ready for CLI Sync!")
        print(f"   Next: python -m src.pipelines.sync_order_list.cli sync --dry-run")
    else:
        print(f"\n❌ Transformation failed: {result['error']}")
