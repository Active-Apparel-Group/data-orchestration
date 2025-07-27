#!/usr/bin/env python3
"""
Debug GREYSON Data Check - Find actual GREYSON data and column names
"""

import sys
from pathlib import Path
import pandas as pd

# EXACT WORKING IMPORT PATTERN
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 DEBUG: GREYSON Data Check")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        
        # Check available columns in source table
        print(f"\n📋 Checking columns in {config.source_table}:")
        columns_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{config.source_table.split('.')[-1]}'
        ORDER BY ORDINAL_POSITION
        """
        columns_df = pd.read_sql(columns_query, connection)
        
        # Look for key columns we need
        key_patterns = ['CUSTOMER', 'PO', 'STYLE', 'COLOR', 'COLOUR']
        for pattern in key_patterns:
            matching_cols = columns_df[columns_df['COLUMN_NAME'].str.contains(pattern, na=False)]
            if not matching_cols.empty:
                print(f"\n   📍 Columns containing '{pattern}':")
                for _, col in matching_cols.iterrows():
                    print(f"     • {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
        
        # Check for any GREYSON data
        print(f"\n🔍 Searching for any GREYSON data in {config.source_table}:")
        
        # First, let's see if there's any customer data at all
        customer_check_query = f"""
        SELECT TOP 10 *
        FROM {config.source_table}
        WHERE [CUSTOMER NAME] LIKE '%GREY%'
        """
        
        try:
            greyson_data = pd.read_sql(customer_check_query, connection)
            if not greyson_data.empty:
                print(f"   ✅ Found {len(greyson_data)} GREYSON-like records")
                print("   Sample data:")
                for idx, row in greyson_data.head(3).iterrows():
                    customer_name = row.get('CUSTOMER NAME', 'Unknown')
                    po_number = row.get('PO NUMBER', 'Unknown')
                    print(f"     {idx+1}. Customer: '{customer_name}', PO: '{po_number}'")
            else:
                print("   ❌ No GREYSON-like data found with [CUSTOMER NAME] LIKE '%GREY%'")
        except Exception as e:
            print(f"   ❌ Error checking GREYSON data: {e}")
        
        # Try a broader search for any customers
        print(f"\n🔍 Sample customer data from {config.source_table}:")
        try:
            sample_customers_query = f"""
            SELECT TOP 10 [CUSTOMER NAME], [PO NUMBER], COUNT(*) as record_count
            FROM {config.source_table}
            GROUP BY [CUSTOMER NAME], [PO NUMBER]
            ORDER BY record_count DESC
            """
            sample_customers = pd.read_sql(sample_customers_query, connection)
            
            if not sample_customers.empty:
                print("   📊 Top customers by record count:")
                for idx, row in sample_customers.head(5).iterrows():
                    customer = row.get('CUSTOMER NAME', 'Unknown')
                    po = row.get('PO NUMBER', 'Unknown')
                    count = row.get('record_count', 0)
                    print(f"     {idx+1}. '{customer}' PO '{po}': {count} records")
            else:
                print("   ❌ No customer data found at all")
                
        except Exception as e:
            print(f"   ❌ Error checking sample customers: {e}")
        
        # Check total record count
        try:
            total_query = f"SELECT COUNT(*) as total_records FROM {config.source_table}"
            total_df = pd.read_sql(total_query, connection)
            total_records = total_df.iloc[0]['total_records'] if not total_df.empty else 0
            print(f"\n📊 Total records in {config.source_table}: {total_records}")
        except Exception as e:
            print(f"   ❌ Error checking total records: {e}")

if __name__ == "__main__":
    main()
