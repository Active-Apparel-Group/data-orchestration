#!/usr/bin/env python3
"""
Debug script to check actual RHYTHM order data for PO 19200
"""
import sys
import pandas as pd
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from audit_pipeline.config import load_env, run_sql, load_customer_map
from audit_pipeline.etl import handle_master_order_list
from audit_pipeline.matching import add_match_keys

def debug_rhythm_order_data():
    print("=== RHYTHM Order Data Debug for PO 19200 ===")
    
    # Load environment and customer mapping
    load_env()
    customer_alias_map = load_customer_map()
    
    # 1. Check raw master order list data
    print("\n1. Raw Master Order List Data:")
    try:
        # Check what columns exist
        columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'master_order_list'
        ORDER BY ordinal_position
        """
        columns = run_sql(columns_query)
        print("Available columns:")
        for col in columns['column_name']:
            print(f"   - {col}")
        
        # Check RHYTHM data with PO 19200
        rhythm_query = """
        SELECT *
        FROM master_order_list 
        WHERE CUSTOMER LIKE '%RHYTHM%' AND "CUSTOMER PO" = '19200'
        LIMIT 5
        """
        rhythm_raw = run_sql(rhythm_query)
        
        if len(rhythm_raw) > 0:
            print(f"\n✅ Found {len(rhythm_raw)} raw RHYTHM records for PO 19200")
            print("Sample raw data:")
            print(rhythm_raw[['CUSTOMER', 'CUSTOMER PO', 'STYLE', 'ALIAS/RELATED ITEM' if 'ALIAS/RELATED ITEM' in rhythm_raw.columns else 'COLOR']].head())
            
            # Check if ALIAS/RELATED ITEM has CLA24SW-BB04-BLK
            if 'ALIAS/RELATED ITEM' in rhythm_raw.columns:
                alias_with_cla = rhythm_raw[rhythm_raw['ALIAS/RELATED ITEM'].str.contains('CLA24SW-BB04-BLK', na=False)]
                print(f"\nRecords with CLA24SW-BB04-BLK in ALIAS/RELATED ITEM: {len(alias_with_cla)}")
                if len(alias_with_cla) > 0:
                    print(alias_with_cla[['CUSTOMER PO', 'ALIAS/RELATED ITEM', 'COLOR' if 'COLOR' in alias_with_cla.columns else 'STYLE']].head())
            else:
                print("❌ No 'ALIAS/RELATED ITEM' column found in raw data!")
                
        else:
            print("❌ No raw RHYTHM records found for PO 19200")
            
            # Check what POs exist for RHYTHM
            rhythm_pos = run_sql("SELECT DISTINCT \"CUSTOMER PO\", CUSTOMER FROM master_order_list WHERE CUSTOMER LIKE '%RHYTHM%' LIMIT 10")
            print(f"\nFound {len(rhythm_pos)} RHYTHM records with these POs:")
            print(rhythm_pos)
            
    except Exception as e:
        print(f"❌ Error querying raw data: {e}")
    
    # 2. Check processed order data
    print("\n2. Processed Order Data:")
    try:
        # Load and process master order list
        master_raw = run_sql("SELECT * FROM master_order_list WHERE CUSTOMER LIKE '%RHYTHM%'")
        if len(master_raw) > 0:
            print(f"Processing {len(master_raw)} raw RHYTHM records...")
            orders_std = handle_master_order_list(master_raw, customer_alias_map)
            
            # Filter for PO 19200
            rhythm_19200 = orders_std[orders_std['Customer_PO'] == '19200']
            
            if len(rhythm_19200) > 0:
                print(f"✅ Found {len(rhythm_19200)} processed RHYTHM records for PO 19200")
                print("Processed columns:")
                print(list(rhythm_19200.columns))
                
                print("\nSample processed data:")
                display_cols = ['Customer_PO', 'Style', 'ALIAS/RELATED ITEM' if 'ALIAS/RELATED ITEM' in rhythm_19200.columns else 'Pattern_ID', 'Color', 'Size']
                available_cols = [col for col in display_cols if col in rhythm_19200.columns]
                print(rhythm_19200[available_cols].head())
                
                # Check for CLA24SW-BB04-BLK
                if 'ALIAS/RELATED ITEM' in rhythm_19200.columns:
                    matching_alias = rhythm_19200[rhythm_19200['ALIAS/RELATED ITEM'].str.contains('CLA24SW-BB04-BLK', na=False)]
                    print(f"\nProcessed records with CLA24SW-BB04-BLK in ALIAS/RELATED ITEM: {len(matching_alias)}")
                    if len(matching_alias) > 0:
                        print(matching_alias[available_cols].head())
                
                # Check Style field too
                if 'Style' in rhythm_19200.columns:
                    matching_style = rhythm_19200[rhythm_19200['Style'].str.contains('CLA24SW-BB04-BLK', na=False)]
                    print(f"\nProcessed records with CLA24SW-BB04-BLK in Style: {len(matching_style)}")
                    if len(matching_style) > 0:
                        print(matching_style[available_cols].head())
                        
            else:
                print("❌ No processed RHYTHM records found for PO 19200")
                
                # Show what POs we do have
                unique_pos = orders_std['Customer_PO'].unique()
                print(f"Available processed POs: {unique_pos[:10]}")
                
        else:
            print("❌ No raw RHYTHM records found at all")
            
    except Exception as e:
        print(f"❌ Error processing order data: {e}")
    
    # 3. Check matching keys generation
    print("\n3. Matching Keys for Available Data:")
    try:
        if 'rhythm_19200' in locals() and len(rhythm_19200) > 0:
            # Add matching keys
            rhythm_with_keys = add_match_keys(rhythm_19200.copy())
            
            print("Sample records with matching keys:")
            key_cols = ['Customer_PO', 'exact_key', 'fuzzy_key', 'Style', 'ALIAS/RELATED ITEM' if 'ALIAS/RELATED ITEM' in rhythm_with_keys.columns else 'Pattern_ID']
            available_key_cols = [col for col in key_cols if col in rhythm_with_keys.columns]
            print(rhythm_with_keys[available_key_cols].head())
            
        else:
            print("No RHYTHM PO 19200 data available to generate keys")
            
    except Exception as e:
        print(f"❌ Error generating matching keys: {e}")

if __name__ == "__main__":
    debug_rhythm_order_data()
