#!/usr/bin/env python3
"""
Debug Source Table Isolation - Check NULL values in customer/PO columns
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
    print("🔍 Debug Source Table Isolation - NULL Values Check...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check total records
        cursor.execute(f"SELECT COUNT(*) FROM [{config.source_table}]")
        total_records = cursor.fetchone()[0]
        print(f"📊 Total records in {config.source_table}: {total_records}")
        
        # Check NULL customer names
        cursor.execute(f"SELECT COUNT(*) FROM [{config.source_table}] WHERE [CUSTOMER NAME] IS NULL")
        null_customers = cursor.fetchone()[0]
        print(f"❌ Records with NULL [CUSTOMER NAME]: {null_customers}")
        
        # Check NULL PO numbers
        cursor.execute(f"SELECT COUNT(*) FROM [{config.source_table}] WHERE [PO NUMBER] IS NULL")
        null_pos = cursor.fetchone()[0]
        print(f"❌ Records with NULL [PO NUMBER]: {null_pos}")
        
        # Check records with either NULL
        cursor.execute(f"""
        SELECT COUNT(*) FROM [{config.source_table}] 
        WHERE [CUSTOMER NAME] IS NULL OR [PO NUMBER] IS NULL
        """)
        any_null = cursor.fetchone()[0]
        print(f"❌ Records with NULL customer OR PO: {any_null}")
        
        # Check target customers/POs
        target_customers = ['ACTIVELY BLACK', 'AESCAPE']
        target_pos = ['AB0001', '1191']
        
        # Build the isolation WHERE clause (same as E2E test)
        customer_clause = " OR ".join([f"[CUSTOMER NAME] = '{customer}'" for customer in target_customers])
        po_clause = " OR ".join([f"[PO NUMBER] = '{po}'" for po in target_pos])
        where_clause = f"({customer_clause}) AND ({po_clause})"
        
        print(f"\n🎯 Isolation WHERE clause:")
        print(f"   {where_clause}")
        
        # Check how many records match the criteria
        cursor.execute(f"""
        SELECT COUNT(*) FROM [{config.source_table}] 
        WHERE {where_clause}
        """)
        matching_records = cursor.fetchone()[0]
        print(f"✅ Records matching criteria: {matching_records}")
        
        # Check how many would be DELETED (NOT matching)
        cursor.execute(f"""
        SELECT COUNT(*) FROM [{config.source_table}] 
        WHERE NOT ({where_clause})
        """)
        would_delete = cursor.fetchone()[0]
        print(f"🗑️  Records that would be DELETED: {would_delete}")
        
        # Show some sample non-matching records
        cursor.execute(f"""
        SELECT TOP 5 [CUSTOMER NAME], [PO NUMBER]
        FROM [{config.source_table}] 
        WHERE NOT ({where_clause})
        """)
        
        print(f"\n📋 Sample records that would be deleted:")
        for row in cursor.fetchall():
            customer, po = row
            print(f"   Customer: '{customer}', PO: '{po}'")
        
        cursor.close()

if __name__ == "__main__":
    main()
