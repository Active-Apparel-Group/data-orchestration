#!/usr/bin/env python3
"""
GREYSON Data Analysis - Pre-Cleanup Check
==========================================
Purpose: Check GREYSON data BEFORE SQL cleanup to understand why it's being deleted
"""

import sys
from pathlib import Path
import pandas as pd

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 GREYSON DATA PRE-CLEANUP ANALYSIS")
    print("=" * 60)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    print(f"📋 Source table: {config.source_table}")
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print(f"\n📊 GREYSON data analysis (BEFORE any cleanup):")
        
        # Check total GREYSON records
        total_query = f"""
        SELECT COUNT(*) as total_greyson
        FROM {config.source_table}
        WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
        """
        
        cursor.execute(total_query)
        total_greyson = cursor.fetchone()[0]
        print(f"   Total GREYSON records: {total_greyson}")
        
        # Check GREYSON PO 4755 specifically
        po_query = f"""
        SELECT COUNT(*) as greyson_4755
        FROM {config.source_table}
        WHERE [CUSTOMER NAME] LIKE '%GREYSON%' AND [PO NUMBER] = '4755'
        """
        
        cursor.execute(po_query)
        greyson_4755 = cursor.fetchone()[0]
        print(f"   GREYSON PO 4755 records: {greyson_4755}")
        
        # Sample GREYSON data to see field completeness
        if greyson_4755 > 0:
            sample_query = f"""
            SELECT TOP 3 
                [CUSTOMER NAME],
                [PO NUMBER],
                [CUSTOMER STYLE],
                [CUSTOMER COLOUR DESCRIPTION],
                [AAG ORDER NUMBER],
                CASE WHEN [CUSTOMER NAME] IS NULL THEN 'NULL' ELSE 'OK' END as customer_name_status,
                CASE WHEN [PO NUMBER] IS NULL THEN 'NULL' ELSE 'OK' END as po_status,
                CASE WHEN [CUSTOMER STYLE] IS NULL THEN 'NULL' ELSE 'OK' END as style_status,
                CASE WHEN [CUSTOMER COLOUR DESCRIPTION] IS NULL THEN 'NULL' ELSE 'OK' END as color_status,
                CASE WHEN [AAG ORDER NUMBER] IS NULL THEN 'NULL' ELSE 'OK' END as aag_status
            FROM {config.source_table}
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%' AND [PO NUMBER] = '4755'
            """
            
            df = pd.read_sql(sample_query, connection)
            print(f"\n   Sample GREYSON PO 4755 data:")
            for idx, row in df.iterrows():
                print(f"      Record {idx+1}:")
                print(f"        Customer: {row['CUSTOMER NAME']} ({row['customer_name_status']})")
                print(f"        PO: {row['PO NUMBER']} ({row['po_status']})")
                print(f"        Style: {row['CUSTOMER STYLE']} ({row['style_status']})")
                print(f"        Color: {row['CUSTOMER COLOUR DESCRIPTION']} ({row['color_status']})")
                print(f"        AAG Order: {row['AAG ORDER NUMBER']} ({row['aag_status']})")
        
        # Check what the delete criteria would catch
        print(f"\n🔍 Checking NULL field patterns that would trigger deletion:")
        
        null_check_query = f"""
        SELECT 
            COUNT(*) as total_with_nulls,
            COUNT(CASE WHEN [CUSTOMER NAME] IS NULL THEN 1 END) as null_customer,
            COUNT(CASE WHEN [PO NUMBER] IS NULL THEN 1 END) as null_po,
            COUNT(CASE WHEN [AAG ORDER NUMBER] IS NULL THEN 1 END) as null_aag
        FROM {config.source_table}
        WHERE [CUSTOMER NAME] LIKE '%GREYSON%' AND [PO NUMBER] = '4755'
        """
        
        cursor.execute(null_check_query)
        result = cursor.fetchone()
        if result:
            total_nulls, null_customer, null_po, null_aag = result
            print(f"   GREYSON PO 4755 NULL analysis:")
            print(f"     Records with any NULLs: {total_nulls}")
            print(f"     NULL CUSTOMER NAME: {null_customer}")
            print(f"     NULL PO NUMBER: {null_po}")
            print(f"     NULL AAG ORDER NUMBER: {null_aag}")
        
        cursor.close()

if __name__ == "__main__":
    main()
