#!/usr/bin/env python3
"""
Diagnostic: Sync Engine Group Assignment Analysis
Test the exact group assignment logic used by sync_engine.py
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from pipelines.sync_order_list.config_parser import DeltaSyncConfig
from pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def main():
    print("🔍 Sync Engine Group Assignment Diagnostic...")
    
    # Initialize sync engine exactly like production CLI
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    sync_engine = SyncEngine(config_path, environment="production")
    
    # Get pending headers exactly like sync engine does
    print("\n📋 Step 1: Getting pending headers from sync engine...")
    pending_headers = sync_engine._get_pending_headers(limit=10)
    
    print(f"Found {len(pending_headers)} pending headers")
    
    # Test group name extraction for each header
    print("\n🎯 Step 2: Testing group name extraction for each header...")
    group_assignments = {}
    
    for i, header in enumerate(pending_headers[:5]):  # Test first 5
        print(f"\n--- Header {i+1} ---")
        print(f"AAG ORDER NUMBER: {header.get('AAG ORDER NUMBER')}")
        print(f"CUSTOMER NAME: {header.get('CUSTOMER NAME')}")
        print(f"group_name (from DB): {header.get('group_name')}")
        
        # Test the sync engine's group assignment logic
        assigned_group = sync_engine._get_group_name_from_header(header)
        print(f"Assigned group (sync engine): {assigned_group}")
        
        # Track group assignments
        if assigned_group not in group_assignments:
            group_assignments[assigned_group] = []
        group_assignments[assigned_group].append(header.get('AAG ORDER NUMBER'))
        
        print(f"✅ Header processed")
    
    # Analyze group distribution
    print(f"\n📊 Step 3: Group assignment distribution...")
    print(f"Total unique groups assigned: {len(group_assignments)}")
    
    for group_name, orders in group_assignments.items():
        print(f"  - '{group_name}': {len(orders)} orders")
        if len(orders) <= 3:
            print(f"    Orders: {', '.join(orders)}")
        else:
            print(f"    Sample orders: {', '.join(orders[:3])}...")
    
    # Check if all records are going to the same group
    if len(group_assignments) == 1:
        print("\n❌ PROBLEM IDENTIFIED: All records are being assigned to the same group!")
        single_group = list(group_assignments.keys())[0]
        print(f"All records assigned to: '{single_group}'")
    else:
        print(f"\n✅ Group assignment working correctly: {len(group_assignments)} different groups")

if __name__ == "__main__":
    main()
