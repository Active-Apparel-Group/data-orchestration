#!/usr/bin/env python3
"""
Debug SyncEngine Table References - Check what tables SyncEngine is actually using
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
    print("🔍 Debug SyncEngine Table References...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    print(f"📋 Config target_table: {config.target_table}")
    print(f"📋 Config lines_table: {config.lines_table}")
    
    # Create SyncEngine instance
    sync_engine = SyncEngine(config_path)
    
    print(f"🔧 SyncEngine headers_table: {sync_engine.headers_table}")
    print(f"🔧 SyncEngine lines_table: {sync_engine.lines_table}")
    
    # Test getting headers
    print("\n🧪 Testing _get_pending_headers()...")
    try:
        headers = sync_engine._get_pending_headers()
        print(f"📊 Retrieved {len(headers)} headers")
        if headers:
            print(f"📝 First header keys: {list(headers[0].keys())}")
            print(f"📝 First header group_name: {headers[0].get('group_name')}")
            print(f"📝 First header customer: {headers[0].get('CUSTOMER NAME')}")
    except Exception as e:
        print(f"❌ Error getting headers: {e}")

if __name__ == "__main__":
    main()
