#!/usr/bin/env python3
"""
Final Validation - Test SyncEngine group name processing without fallback
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def main():
    print("🎯 Final Validation - SyncEngine Group Name Processing...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    sync_engine = SyncEngine(config_path)
    
    # Get pending headers
    headers = sync_engine._get_pending_headers()
    print(f"📊 Retrieved {len(headers)} pending headers")
    
    # Test group name extraction
    group_names = set()
    for header in headers:
        group_name = sync_engine._get_group_name_from_header(header)
        group_names.add(group_name)
    
    print(f"\n🏷️  Unique Group Names Extracted:")
    for group_name in sorted(group_names):
        print(f"   • {group_name}")
    
    # Check for any fallback behavior (should NOT see customer names only)
    customer_only_names = {'ACTIVELY BLACK', 'AESCAPE'}
    fallback_names = group_names.intersection(customer_only_names)
    
    if fallback_names:
        print(f"\n❌ FALLBACK DETECTED: {fallback_names}")
        print("   These should be customer+season format, not customer only!")
    else:
        print(f"\n✅ NO FALLBACK DETECTED!")
        print("   All group names use proper customer+season format")
    
    # Validate format
    valid_formats = all(
        ' ' in name and len(name.split()) >= 2 
        for name in group_names if name
    )
    
    if valid_formats:
        print("✅ All group names follow customer+season format")
    else:
        print("❌ Some group names don't follow expected format")
    
    print(f"\n🎯 RESULT: SyncEngine group name processing is {'✅ WORKING' if not fallback_names and valid_formats else '❌ BROKEN'}")

if __name__ == "__main__":
    main()
