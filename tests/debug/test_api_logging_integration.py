#!/usr/bin/env python3
"""
Test the API logging integration in sync_engine.py
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
    print("🧪 Testing API Logging Integration...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    
    try:
        # Initialize sync engine
        sync_engine = SyncEngine(config_path, environment="development")
        print("✅ SyncEngine initialized successfully")
        
        # Test the new API logging capture method
        test_request_data = [{"test": "request", "operation": "create_items"}]
        test_response_data = {"success": True, "monday_ids": ["12345"], "test": "response"}
        
        api_logging_data = sync_engine._capture_api_logging_data(
            "create_items", 
            test_request_data, 
            test_response_data
        )
        
        print("\n📝 API Logging Data Captured:")
        for key, value in api_logging_data.items():
            if 'payload' in key:
                print(f"  {key}: {value[:100]}..." if len(str(value)) > 100 else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
        
        # Check if new columns exist in database
        with db.get_connection(sync_engine.db_key) as connection:
            cursor = connection.cursor()
            
            # Check FACT_ORDER_LIST columns
            query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'FACT_ORDER_LIST' 
            AND COLUMN_NAME LIKE 'api_%'
            ORDER BY COLUMN_NAME
            """
            cursor.execute(query)
            api_columns = [row[0] for row in cursor.fetchall()]
            
            print(f"\n📊 API columns in FACT_ORDER_LIST: {len(api_columns)}")
            for col in api_columns:
                print(f"  ✅ {col}")
            
            cursor.close()
        
        print("\n🎉 API logging integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
