#!/usr/bin/env python3
"""
SQL View Debugging Test - Debug Phase 0B SQL Operations Issues
============================================================
Purpose: Debug the date conversion error in v_order_list_nulls_to_delete view
Pattern: EXACT pattern from imports.guidance.instructions.md - PROVEN WORKING PATTERN

ERROR TO DEBUG:
('22007', '[22007] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Conversion failed when converting date and/or time from character string. (241) (SQLExecDirectW)')
"""

import sys
from pathlib import Path
import pandas as pd

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    """Debug SQL view issues causing date conversion errors"""
    try:
        logger.info("🔧 Starting SQL View Debugging Test...")
        
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Database connection using config.db_key
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Test 1: Check if source table has data
            logger.info("🧪 Test 1: Check source table data...")
            cursor.execute(f"SELECT COUNT(*) FROM {config.source_table}")
            total_count = cursor.fetchone()[0]
            logger.info(f"   Total records in {config.source_table}: {total_count}")
            
            # Test 2: Check for GREYSON data specifically
            logger.info("🧪 Test 2: Check GREYSON data...")
            cursor.execute(f"SELECT COUNT(*) FROM {config.source_table} WHERE [CUSTOMER NAME] LIKE '%GREYSON%'")
            greyson_count = cursor.fetchone()[0]
            logger.info(f"   GREYSON records: {greyson_count}")
            
            # Test 3: Check if v_order_list_hash_nulls view exists
            logger.info("🧪 Test 3: Check v_order_list_hash_nulls view...")
            try:
                cursor.execute("SELECT COUNT(*) FROM [v_order_list_hash_nulls]")
                hash_nulls_count = cursor.fetchone()[0]
                logger.info(f"   ✅ v_order_list_hash_nulls exists: {hash_nulls_count} records")
            except Exception as e:
                logger.error(f"   ❌ v_order_list_hash_nulls error: {e}")
                
            # Test 4: Check if v_order_list_nulls_to_delete view exists and works
            logger.info("🧪 Test 4: Check v_order_list_nulls_to_delete view...")
            try:
                cursor.execute("SELECT COUNT(*) FROM [v_order_list_nulls_to_delete]")
                nulls_to_delete_count = cursor.fetchone()[0]
                logger.info(f"   ✅ v_order_list_nulls_to_delete exists: {nulls_to_delete_count} records")
                
                # Get sample records to see the structure
                cursor.execute("SELECT TOP 3 record_uuid, hash_ord_3_10 FROM [v_order_list_nulls_to_delete]")
                sample_records = cursor.fetchall()
                if sample_records:
                    logger.info("   Sample records to delete:")
                    for i, record in enumerate(sample_records):
                        logger.info(f"     {i+1}. UUID: {record[0]}, Hash: {record[1]}")
                        
            except Exception as e:
                logger.error(f"   ❌ v_order_list_nulls_to_delete error: {e}")
                
                # If the view fails, let's check the underlying hash view in detail
                logger.info("🔍 Debug: Checking v_order_list_hash_nulls structure...")
                try:
                    cursor.execute("SELECT TOP 1 * FROM [v_order_list_hash_nulls]")
                    columns = [description[0] for description in cursor.description]
                    logger.info(f"   Columns in v_order_list_hash_nulls: {columns}")
                    
                    sample_row = cursor.fetchone()
                    if sample_row:
                        logger.info("   Sample row values:")
                        for col, val in zip(columns, sample_row):
                            logger.info(f"     {col}: {val} ({type(val).__name__})")
                            
                except Exception as e2:
                    logger.error(f"   ❌ Error checking hash view structure: {e2}")
            
            # Test 5: Try the actual delete query from 01_delete_null_rows.sql
            logger.info("🧪 Test 5: Test actual delete query (DRY RUN)...")
            try:
                delete_query = f"""
                SELECT record_uuid 
                FROM [v_order_list_nulls_to_delete]
                """
                cursor.execute(delete_query)
                delete_candidates = cursor.fetchall()
                logger.info(f"   ✅ Delete query works: {len(delete_candidates)} records would be deleted")
                
            except Exception as e:
                logger.error(f"   ❌ Delete query error: {e}")
                logger.error("   This is the root cause of the Phase 0B failure!")
            
            # Test 6: Check for date/time columns that might be causing the conversion error
            logger.info("🧪 Test 6: Check for problematic date columns...")
            try:
                # Get column info for the source table
                cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{config.source_table.split('.')[-1]}'
                AND DATA_TYPE IN ('datetime', 'datetime2', 'date', 'time', 'varchar', 'nvarchar', 'char', 'nchar')
                ORDER BY ORDINAL_POSITION
                """)
                
                date_columns = cursor.fetchall()
                logger.info(f"   Found {len(date_columns)} potential date/string columns:")
                for col_name, data_type, nullable in date_columns:
                    logger.info(f"     {col_name}: {data_type} (nullable: {nullable})")
                    
            except Exception as e:
                logger.error(f"   ❌ Column check error: {e}")
            
            # Test 7: Check specific hash values mentioned in the view
            logger.info("🧪 Test 7: Check specific hash values...")
            hash_values = ['A46C3B54F2C9871CD81DAF7A932499C0', '774F655800BE1B7CCDFED8C4E4E697FA']
            for hash_val in hash_values:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [v_order_list_hash_nulls] WHERE [hash_ord_3_10] = ?", (hash_val,))
                    count = cursor.fetchone()[0]
                    logger.info(f"   Hash {hash_val}: {count} records")
                except Exception as e:
                    logger.error(f"   ❌ Hash check error for {hash_val}: {e}")
            
            cursor.close()
            
        logger.info("✅ SQL View Debugging Test completed!")
        
    except Exception as e:
        logger.error(f"❌ SQL debugging test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
