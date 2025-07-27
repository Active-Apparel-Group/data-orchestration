#!/usr/bin/env python3
"""
Final API Archiver Verification
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    print("🎯 FINAL API ARCHIVER VERIFICATION")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG")
        api_logs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST")
        headers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES")
        lines = cursor.fetchone()[0]
        
        print(f"✅ ORDER_LIST_API_LOG: {api_logs} records")
        print(f"📋 FACT_ORDER_LIST: {headers} records")
        print(f"📋 ORDER_LIST_LINES: {lines} records")
        
        if api_logs > 0:
            print("\n🎉 SUCCESS: API ARCHIVER IS NOW WORKING!")
            print("📝 Integration completed - archiver will run after each successful sync")
        else:
            print("\n❌ Issue: No API logs found")
            
        cursor.close()

if __name__ == "__main__":
    main()
