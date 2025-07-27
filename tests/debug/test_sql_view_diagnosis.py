#!/usr/bin/env python3
"""
SQL View Diagnosis - Test v_order_list_hash_nulls and v_order_list_nulls_to_delete
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🧪 SQL View Diagnosis - Testing v_order_list_hash_nulls and v_order_list_nulls_to_delete")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print(f"\n1. 🔍 Testing base table: {config.source_table}")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {config.source_table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ Base table accessible: {count:,} total records")
        except Exception as e:
            print(f"   ❌ Base table error: {e}")
            return
        
        print(f"\n2. 🔍 Testing GREYSON data in base table...")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {config.source_table} WHERE [CUSTOMER NAME] LIKE '%GREYSON%'")
            greyson_count = cursor.fetchone()[0]
            print(f"   ✅ GREYSON records found: {greyson_count:,}")
            
            if greyson_count > 0:
                cursor.execute(f"""
                SELECT TOP 3 
                    [CUSTOMER NAME], [PO NUMBER], [CUSTOMER STYLE], [CUSTOMER COLOUR DESCRIPTION]
                FROM {config.source_table} 
                WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                """)
                samples = cursor.fetchall()
                print("   Sample GREYSON records:")
                for i, row in enumerate(samples):
                    print(f"     {i+1}. Customer: {row[0]}, PO: {row[1]}, Style: {row[2]}, Color: {row[3]}")
                    
        except Exception as e:
            print(f"   ❌ GREYSON query error: {e}")
        
        print(f"\n3. 🔍 Testing date columns in base table...")
        try:
            # Check for date columns that might have conversion issues
            cursor.execute(f"""
            SELECT TOP 5
                [CUSTOMER NAME], [PO NUMBER],
                [CREATED_AT], [UPDATED_AT], [LastSyncTimestamp]
            FROM {config.source_table}
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
            """)
            date_samples = cursor.fetchall()
            print("   ✅ Date columns accessible:")
            for i, row in enumerate(date_samples):
                print(f"     {i+1}. Customer: {row[0]}, PO: {row[1]}")
                print(f"        CREATED_AT: {row[2]}, UPDATED_AT: {row[3]}, LastSync: {row[4]}")
                
        except Exception as e:
            print(f"   ⚠️  Date column query error: {e}")
            # Try without date columns
            print("   🔧 Trying without problematic date columns...")
            try:
                cursor.execute(f"""
                SELECT TOP 3
                    [CUSTOMER NAME], [PO NUMBER], [CUSTOMER STYLE]
                FROM {config.source_table}
                WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                """)
                basic_samples = cursor.fetchall()
                print(f"   ✅ Basic columns work: {len(basic_samples)} samples")
            except Exception as e2:
                print(f"   ❌ Even basic columns fail: {e2}")
        
        print(f"\n4. 🔍 Testing v_order_list_hash_nulls view...")
        try:
            cursor.execute("SELECT COUNT(*) FROM [v_order_list_hash_nulls]")
            hash_count = cursor.fetchone()[0]
            print(f"   ✅ Hash view accessible: {hash_count:,} records")
            
            # Test the hash calculation specifically
            cursor.execute("""
            SELECT TOP 3 
                [CUSTOMER NAME], [PO NUMBER], [hash_ord_3_10]
            FROM [v_order_list_hash_nulls]
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
            """)
            hash_samples = cursor.fetchall()
            print("   Sample hash records:")
            for i, row in enumerate(hash_samples):
                print(f"     {i+1}. Customer: {row[0]}, PO: {row[1]}, Hash: {row[2]}")
                
        except Exception as e:
            print(f"   ❌ Hash view error: {e}")
            print("   🔧 This is likely the source of the date conversion error!")
            
            # Try to isolate the problematic column
            print("   🔍 Testing hash calculation components...")
            try:
                cursor.execute(f"""
                SELECT TOP 3
                    [PLANNED DELIVERY METHOD],
                    [CUSTOMER STYLE], 
                    [PO NUMBER],
                    [CUSTOMER ALT PO],
                    [AAG SEASON],
                    [CUSTOMER SEASON],
                    [CUSTOMER COLOUR DESCRIPTION],
                    [TOTAL QTY]
                FROM {config.source_table}
                WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                """)
                hash_components = cursor.fetchall()
                print(f"   ✅ Hash components accessible: {len(hash_components)} samples")
                for i, row in enumerate(hash_components):
                    print(f"     {i+1}. Delivery: {row[0]}, Style: {row[1]}, PO: {row[2]}")
                    print(f"        Alt PO: {row[3]}, AAG Season: {row[4]}, Cust Season: {row[5]}")
                    print(f"        Color: {row[6]}, Total QTY: {row[7]}")
                    
            except Exception as e2:
                print(f"   ❌ Hash components error: {e2}")
        
        print(f"\n5. 🔍 Testing v_order_list_nulls_to_delete view...")
        try:
            cursor.execute("SELECT COUNT(*) FROM [v_order_list_nulls_to_delete]")
            delete_count = cursor.fetchone()[0]
            print(f"   ✅ Delete view accessible: {delete_count:,} records to delete")
            
            if delete_count > 0:
                cursor.execute("""
                SELECT TOP 3 
                    record_uuid, [CUSTOMER NAME], [PO NUMBER], [hash_ord_3_10]
                FROM [v_order_list_nulls_to_delete]
                """)
                delete_samples = cursor.fetchall()
                print("   Sample records to delete:")
                for i, row in enumerate(delete_samples):
                    print(f"     {i+1}. UUID: {row[0]}, Customer: {row[1]}, PO: {row[2]}, Hash: {row[3]}")
                    
        except Exception as e:
            print(f"   ❌ Delete view error: {e}")
        
        print(f"\n6. 🔍 Testing specific hash values...")
        target_hashes = ['A46C3B54F2C9871CD81DAF7A932499C0', '774F655800BE1B7CCDFED8C4E4E697FA']
        for hash_val in target_hashes:
            try:
                cursor.execute(f"""
                SELECT COUNT(*) FROM {config.source_table}
                WHERE CONVERT(VARCHAR(32), HASHBYTES('MD5',
                    CONCAT(
                        COALESCE([PLANNED DELIVERY METHOD], ''),
                        COALESCE([CUSTOMER STYLE], ''),
                        COALESCE([PO NUMBER], ''),
                        COALESCE([CUSTOMER ALT PO], ''),
                        COALESCE([AAG SEASON], ''),
                        COALESCE([CUSTOMER SEASON], ''),
                        COALESCE([CUSTOMER COLOUR DESCRIPTION], ''),
                        COALESCE([TOTAL QTY], 0) 
                    )
                ), 2) = ?
                """, (hash_val,))
                hash_count = cursor.fetchone()[0]
                print(f"   Hash {hash_val}: {hash_count:,} records")
                
            except Exception as e:
                print(f"   ❌ Hash {hash_val} error: {e}")
        
        cursor.close()

if __name__ == "__main__":
    main()
