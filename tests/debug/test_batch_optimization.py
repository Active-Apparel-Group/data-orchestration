#!/usr/bin/env python3
"""
Test Batch Optimization - Identify and fix true batching performance issue
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 BATCH OPTIMIZATION ANALYSIS...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Analyze BORN PRIMITIVE batch structure
        query = """
        SELECT 
            [CUSTOMER NAME],
            record_uuid,
            COUNT(*) as record_count,
            MIN([PO NUMBER]) as min_po,
            MAX([PO NUMBER]) as max_po
        FROM [FACT_ORDER_LIST]
        WHERE [CUSTOMER NAME] = 'BORN PRIMITIVE'
        GROUP BY [CUSTOMER NAME], record_uuid
        ORDER BY record_uuid
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"\n📊 BORN PRIMITIVE Batch Analysis:")
        print(f"   Total unique record_uuids: {len(results)}")
        
        total_records = 0
        for row in results:
            customer, record_uuid, count, min_po, max_po = row
            total_records += count
            print(f"   UUID {record_uuid}: {count} records (PO {min_po}-{max_po})")
        
        print(f"\n🔍 PERFORMANCE ISSUE IDENTIFIED:")
        print(f"   Current approach: {len(results)} separate API calls")
        print(f"   Total records: {total_records}")
        print(f"   Could be: 1 batch API call with {total_records} items")
        print(f"   Performance loss: {len(results)}x more API calls than needed!")
        
        # Simulate optimal batching (Monday.com limit: 50 items per batch)
        optimal_batches = (total_records + 49) // 50  # Round up
        print(f"\n✅ OPTIMAL BATCHING:")
        print(f"   Optimal batches needed: {optimal_batches}")
        print(f"   Current API calls: {len(results)}")
        print(f"   Performance improvement: {len(results) / optimal_batches:.1f}x faster")
        
        cursor.close()

if __name__ == "__main__":
    main()
