#!/usr/bin/env python3
"""
CLI Dry Run with Group Name Debugging
====================================
Purpose: Test CLI dry run and debug group_name transformation issues
Location: tests/production_migration/integration/test_cli_dry_run_debug.py
Created: 2025-07-29

This will run a CLI dry run and specifically debug the group_name issue.
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def debug_group_name_transformation():
    """Debug the group_name transformation to identify why it's showing just 'CUSTOMER'"""
    print("🔍 Debug Group Name Transformation")
    print("=" * 50)
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    try:
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Check raw data from database
            print("📋 Checking raw GREYSON data...")
            cursor.execute("""
                SELECT TOP 3
                    [CUSTOMER NAME],
                    [PO NUMBER],
                    [AAG ORDER NUMBER],
                    [sync_state]
                FROM [FACT_ORDER_LIST]
                WHERE [CUSTOMER NAME] LIKE 'GREYSON%' 
                  AND [PO NUMBER] = '4755'
                  AND [sync_state] = 'PENDING'
                ORDER BY [AAG ORDER NUMBER]
            """)
            
            raw_records = cursor.fetchall()
            print(f"Found {len(raw_records)} PENDING GREYSON records")
            
            for record in raw_records:
                customer_name, po_number, aag_order, sync_state = record
                print(f"  Customer: '{customer_name}', PO: '{po_number}', Order: '{aag_order}'")
            
            # Now test the SyncEngine transformation
            print("\n🔄 Testing SyncEngine transformation...")
            engine = SyncEngine(config_path)
            
            # Get pending records through SyncEngine
            pending_records = engine.get_pending_records(limit=3)
            print(f"SyncEngine found {len(pending_records)} pending records")
            
            # Debug each record's transformation
            for i, record in enumerate(pending_records):
                print(f"\n📦 Record {i+1}:")
                print(f"   Raw customer_name: '{record.get('customer_name', 'NOT FOUND')}'")
                
                # Test group name generation
                try:
                    group_name = engine.transformer.generate_group_name(record)
                    print(f"   Generated group_name: '{group_name}'")
                    
                    # Debug the transformation process
                    customer_name = record.get('customer_name', '')
                    print(f"   Customer name for transformation: '{customer_name}'")
                    
                    # Test the specific transformation logic
                    if hasattr(engine.transformer, 'transform_customer_name'):
                        transformed = engine.transformer.transform_customer_name(customer_name)
                        print(f"   Transformed customer name: '{transformed}'")
                    
                except Exception as e:
                    print(f"   ❌ Group name generation failed: {e}")
                    logger.exception(f"Group name generation error for record {i+1}")
            
            return True
            
    except Exception as e:
        logger.exception(f"Debug failed: {e}")
        return False

def run_cli_dry_run():
    """Run CLI dry run to see the actual behavior"""
    print("\n🧪 Running CLI Dry Run")
    print("=" * 50)
    
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    try:
        engine = SyncEngine(config_path)
        
        print("📋 CLI Dry Run Results:")
        result = engine.sync_pending_records(dry_run=True, limit=3)
        
        if result and result.get('success'):
            print(f"✅ Dry run completed successfully!")
            print(f"   Records processed: {result.get('records_processed', 0)}")
            print(f"   Groups to create: {len(result.get('groups_to_create', []))}")
            print(f"   Items to create: {len(result.get('items_to_create', []))}")
            
            # Debug group creation details
            groups = result.get('groups_to_create', [])
            for group in groups:
                print(f"   📁 Group: '{group.get('name', 'NO NAME')}'")
                
            # Debug item creation details
            items = result.get('items_to_create', [])
            for item in items[:3]:  # Show first 3 items
                print(f"   📄 Item: '{item.get('name', 'NO NAME')}' -> Group: '{item.get('group_name', 'NO GROUP')}'")
                
        else:
            print("❌ Dry run failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        logger.exception(f"CLI dry run failed: {e}")
        return {'success': False, 'error': str(e)}

def main():
    print("🚀 CLI Dry Run with Group Name Debugging")
    print("=" * 60)
    
    # First debug the transformation
    debug_success = debug_group_name_transformation()
    
    if not debug_success:
        print("❌ Debug failed, skipping dry run")
        return {'success': False, 'error': 'Debug failed'}
    
    # Then run the actual dry run
    dry_run_result = run_cli_dry_run()
    
    print("\n📋 Summary:")
    if dry_run_result.get('success'):
        print("✅ CLI dry run completed - check group names above")
    else:
        print("❌ CLI dry run failed")
        print(f"   Error: {dry_run_result.get('error', 'Unknown')}")
    
    return dry_run_result

if __name__ == "__main__":
    result = main()
    if result.get('success'):
        print("\n🎯 Dry run complete - review group_name issues above")
    else:
        print(f"\n🔧 Issues found: {result.get('error', 'Unknown')}")
