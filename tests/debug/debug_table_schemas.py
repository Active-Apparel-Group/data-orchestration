"""
Debug Script: Table Schema Validation
=====================================

Script to check table schemas and column structure.
Validates ORDERS_UNIFIED and ORDERS_UNIFIED_SNAPSHOT table structure.

Location: tests/debug/debug_table_schemas.py
"""

import sys
from pathlib import Path

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper
import pandas as pd

def debug_table_schemas():
    """Debug and validate table schemas"""
    
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting table schema validation")
    
    print("🔍 TABLE SCHEMA VALIDATION")
    print("=" * 40)
    
    try:
        with db.get_connection('dms') as conn:
            
            # Check ORDERS_UNIFIED structure
            logger.info("Checking ORDERS_UNIFIED schema")
            print("\n📊 ORDERS_UNIFIED TABLE ANALYSIS:")
            print("-" * 45)
            
            df1 = pd.read_sql("""
            SELECT TOP 1 * FROM [dbo].[ORDERS_UNIFIED]
            """, conn)
            
            print('Column count:', len(df1.columns))
            print('Columns:')
            for i, col in enumerate(df1.columns, 1):
                print(f"  {i:3d}. {col}")
            print()
            
            # Check if record_uuid exists
            if 'record_uuid' in df1.columns:
                print('✅ record_uuid column exists in ORDERS_UNIFIED')
            else:
                print('❌ record_uuid column missing in ORDERS_UNIFIED')
            print()
            
            # Get total record count
            count_df = pd.read_sql("SELECT COUNT(*) as cnt FROM [dbo].[ORDERS_UNIFIED]", conn)
            print(f'📈 ORDERS_UNIFIED record count: {count_df.iloc[0]["cnt"]:,}')
            print()
            
            # Check ORDERS_UNIFIED_SNAPSHOT structure
            logger.info("Checking ORDERS_UNIFIED_SNAPSHOT schema")
            print("📊 ORDERS_UNIFIED_SNAPSHOT TABLE ANALYSIS:")
            print("-" * 45)
            
            try:
                df2 = pd.read_sql("""
                SELECT TOP 1 * FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]
                """, conn)
                
                print('Column count:', len(df2.columns))
                print('Columns:')
                for i, col in enumerate(df2.columns, 1):
                    print(f"  {i:3d}. {col}")
                print()
                
                if 'record_uuid' in df2.columns:
                    print('✅ record_uuid column exists in ORDERS_UNIFIED_SNAPSHOT')
                else:
                    print('❌ record_uuid column missing in ORDERS_UNIFIED_SNAPSHOT')
                
                # Check record count
                count_df = pd.read_sql("SELECT COUNT(*) as cnt FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]", conn)
                record_count = count_df.iloc[0]["cnt"]
                print(f'📈 ORDERS_UNIFIED_SNAPSHOT record count: {record_count:,}')
                
                if record_count == 0:
                    print("ℹ️  Empty snapshot table - this is expected for new record detection")
                
            except Exception as e:
                print(f'❌ Error accessing ORDERS_UNIFIED_SNAPSHOT: {e}')
                logger.error(f"ORDERS_UNIFIED_SNAPSHOT access failed: {e}")
            
            # Check for other key columns
            print("\n🔍 KEY COLUMN VALIDATION:")
            print("-" * 25)
            
            key_columns = [
                'CUSTOMER NAME',
                'AAG ORDER NUMBER', 
                'CUSTOMER STYLE',
                'CUSTOMER COLOUR DESCRIPTION',
                'PO NUMBER',
                'TOTAL QTY'
            ]
            
            for col in key_columns:
                if col in df1.columns:
                    print(f"✅ {col}")
                else:
                    print(f"❌ {col} - MISSING")
            
            logger.info("Table schema validation completed")
            
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_table_schemas()
