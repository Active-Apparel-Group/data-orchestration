#!/usr/bin/env python3
"""
Test fixed batching logic - verify batches contain multiple records per customer
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
    print("🧪 Testing Fixed Batching Logic...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Create sync engine with config path
        engine = SyncEngine(config_path)
        
        # Test the batching logic with sample data
        sample_headers = [
            {'CUSTOMER NAME': 'GREYSON', 'record_uuid': '123-456-789', 'AAG ORDER NUMBER': 'AAG001'},
            {'CUSTOMER NAME': 'GREYSON', 'record_uuid': '123-456-790', 'AAG ORDER NUMBER': 'AAG002'},
            {'CUSTOMER NAME': 'GREYSON', 'record_uuid': '123-456-791', 'AAG ORDER NUMBER': 'AAG003'},
            {'CUSTOMER NAME': 'JOHNNIE O', 'record_uuid': '456-789-123', 'AAG ORDER NUMBER': 'AAG004'},
            {'CUSTOMER NAME': 'JOHNNIE O', 'record_uuid': '456-789-124', 'AAG ORDER NUMBER': 'AAG005'},
        ]
        
        # Test the batching method
        batches = engine._group_by_customer_and_uuid(sample_headers)
        
        print("\n📊 BATCHING TEST RESULTS:")
        for customer, customer_batch in batches.items():
            batch_records = customer_batch["batch"]
            print(f"  {customer}: {len(batch_records)} records in batch")
            for record in batch_records:
                print(f"    - {record['AAG ORDER NUMBER']} ({record['record_uuid']})")
        
        print(f"\n✅ SUCCESS: {len(batches)} customer batches created")
        print(f"   GREYSON batch: {len(batches.get('GREYSON', {}).get('batch', []))} records")
        print(f"   JOHNNIE O batch: {len(batches.get('JOHNNIE O', {}).get('batch', []))} records")
        
        # Verify we have proper batching (multiple records per customer)
        greyson_count = len(batches.get('GREYSON', {}).get('batch', []))
        johnnie_count = len(batches.get('JOHNNIE O', {}).get('batch', []))
        
        if greyson_count == 3 and johnnie_count == 2:
            print("\n🎉 BATCHING FIXED! Multiple records per customer batch!")
        else:
            print(f"\n❌ BATCHING STILL BROKEN: Expected 3 GREYSON, 2 JOHNNIE O")
        
        cursor.close()

if __name__ == "__main__":
    main()
