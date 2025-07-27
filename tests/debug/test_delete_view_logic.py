#!/usr/bin/env python3
"""
Check the v_order_list_nulls_to_delete view logic
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

def main():
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)

    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("🔍 Debugging v_order_list_nulls_to_delete view...")
        
        # Check total records in source table  
        cursor.execute(f"SELECT COUNT(*) FROM {config.source_table}")
        total_source = cursor.fetchone()[0]
        print(f"Total records in source table: {total_source:,}")
        
        # Check total records that would be deleted
        try:
            cursor.execute("SELECT COUNT(*) FROM [v_order_list_nulls_to_delete]")
            total_to_delete = cursor.fetchone()[0]
            print(f"Records marked for deletion: {total_to_delete:,}")
            
            if total_to_delete == total_source:
                print("🚨 ERROR: ALL records are marked for deletion!")
                print("This suggests the view logic is wrong.")
                
                # Check the hash distribution
                print("\\n🔍 Checking hash values...")
                cursor.execute("""
                SELECT [hash_ord_3_10], COUNT(*) as count
                FROM [v_order_list_hash_nulls] 
                GROUP BY [hash_ord_3_10]
                ORDER BY COUNT(*) DESC
                """)
                hash_results = cursor.fetchall()
                
                print(f"Total unique hash values: {len(hash_results)}")
                print("Top 10 hash distributions:")
                for i, (hash_val, count) in enumerate(hash_results[:10]):
                    marker = "🚨" if hash_val in ['A46C3B54F2C9871CD81DAF7A932499C0', '774F655800BE1B7CCDFED8C4E4E697FA'] else "  "
                    print(f"{marker} {i+1}. {hash_val}: {count:,} records")
                
                # Check if there are records with the target hashes
                target_hashes = ['A46C3B54F2C9871CD81DAF7A932499C0', '774F655800BE1B7CCDFED8C4E4E697FA']
                for target_hash in target_hashes:
                    cursor.execute("""
                    SELECT COUNT(*) FROM [v_order_list_hash_nulls]
                    WHERE [hash_ord_3_10] = ?
                    """, (target_hash,))
                    target_count = cursor.fetchone()[0]
                    print(f"\\nRecords with hash {target_hash}: {target_count:,}")
                    
                    if target_count > 0:
                        cursor.execute(f"""
                        SELECT TOP 3 [CUSTOMER NAME], [PO NUMBER], [CUSTOMER STYLE]
                        FROM [v_order_list_hash_nulls]
                        WHERE [hash_ord_3_10] = ?
                        """, (target_hash,))
                        samples = cursor.fetchall()
                        print(f"Sample records with this hash:")
                        for j, row in enumerate(samples):
                            print(f"  {j+1}. Customer: {row[0]}, PO: {row[1]}, Style: {row[2]}")
            
        except Exception as e:
            print(f"❌ Error checking delete view: {e}")
        
        cursor.close()

if __name__ == "__main__":
    main()
