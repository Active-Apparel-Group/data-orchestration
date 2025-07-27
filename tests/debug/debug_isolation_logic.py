#!/usr/bin/env python3
"""
Debug Isolation Query Logic - Check why no records are being deleted
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
    print("🔍 Debug Isolation Query Logic...")
    
    # Config
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Get the same conditions as the test
        limit_customers = ['ACTIVELY BLACK', 'AESCAPE']
        limit_pos = ['AB0001', '1191']
        
        # Build WHERE clause (same logic as test)
        where_conditions = []
        params = []
        
        customer_conditions = []
        for customer in limit_customers:
            customer_conditions.append("[CUSTOMER NAME] = ?")
            params.append(customer)
        where_conditions.append(f"({' OR '.join(customer_conditions)})")
        
        po_conditions = []
        for po in limit_pos:
            po_conditions.append("[PO NUMBER] = ?")
            params.append(po)
        where_conditions.append(f"({' OR '.join(po_conditions)})")
        
        where_clause = " AND ".join(where_conditions)
        
        print(f"🎯 WHERE clause: {where_clause}")
        print(f"📋 Parameters: {params}")
        
        # Check how many records match
        cursor.execute(f"""
        SELECT COUNT(*) FROM [{config.source_table}] 
        WHERE {where_clause}
        """, params)
        matching = cursor.fetchone()[0]
        print(f"✅ Records matching criteria: {matching}")
        
        # Check what the isolation query would do
        isolation_where = f"""
        ([CUSTOMER NAME] IS NOT NULL AND [PO NUMBER] IS NOT NULL)
        AND NOT ({where_clause})
        """
        
        cursor.execute(f"""
        SELECT COUNT(*) FROM [{config.source_table}] 
        WHERE {isolation_where}
        """, params)
        would_delete = cursor.fetchone()[0]
        print(f"🗑️  Records that WOULD be deleted: {would_delete}")
        
        # Check NULL records
        cursor.execute(f"""
        SELECT COUNT(*) FROM [{config.source_table}] 
        WHERE [CUSTOMER NAME] IS NULL OR [PO NUMBER] IS NULL
        """)
        null_records = cursor.fetchone()[0]
        print(f"❓ Records with NULL customer/PO: {null_records}")
        
        # Show sample data
        cursor.execute(f"""
        SELECT TOP 10 [CUSTOMER NAME], [PO NUMBER]
        FROM [{config.source_table}]
        WHERE [CUSTOMER NAME] IS NOT NULL AND [PO NUMBER] IS NOT NULL
        """)
        
        print(f"\n📋 Sample non-NULL records:")
        for row in cursor.fetchall():
            customer, po = row
            print(f"   Customer: '{customer}', PO: '{po}'")
        
        cursor.close()

if __name__ == "__main__":
    main()
