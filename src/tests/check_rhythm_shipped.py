#!/usr/bin/env python3
"""
Check RHYTHM shipped data structure for comparison
"""
import sys
import pandas as pd
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from audit_pipeline.config import load_env, run_sql
from audit_pipeline.etl import standardize_dataset
from audit_pipeline.matching import add_match_keys

def check_rhythm_shipped_data():
    print("=== RHYTHM Shipped Data Check ===")
    
    # Load environment
    load_env()
    
    try:
        # Check shipped data for RHYTHM PO 19200
        shipped_query = """
        SELECT *
        FROM shipped 
        WHERE Customer LIKE '%RHYTHM%' AND "Customer PO" = '19200'
        LIMIT 10
        """
        shipped_raw = run_sql(shipped_query)
        
        if len(shipped_raw) > 0:
            print(f"✅ Found {len(shipped_raw)} raw shipped records for RHYTHM PO 19200")
            print("Columns:", list(shipped_raw.columns))
            
            # Check for CLA24SW-BB04-BLK in Style
            if 'Style' in shipped_raw.columns:
                matching_style = shipped_raw[shipped_raw['Style'].str.contains('CLA24SW-BB04-BLK', na=False)]
                print(f"\nRecords with CLA24SW-BB04-BLK in Style: {len(matching_style)}")
                if len(matching_style) > 0:
                    display_cols = ['Customer PO', 'Style', 'Color', 'Size', 'Qty' if 'Qty' in matching_style.columns else 'Customer']
                    available_cols = [col for col in display_cols if col in matching_style.columns]
                    print("Sample matching records:")
                    print(matching_style[available_cols].head())
            
            # Process the shipped data through standardization
            print(f"\nProcessing {len(shipped_raw)} shipped records...")
            shipped_std = standardize_dataset(shipped_raw, 'SHIPPED', 'Qty', customer_alias_map={})
            
            # Filter for PO 19200 again
            rhythm_shipped_19200 = shipped_std[shipped_std['Customer_PO'] == '19200']
            
            if len(rhythm_shipped_19200) > 0:
                print(f"✅ Found {len(rhythm_shipped_19200)} standardized shipped records for PO 19200")
                
                # Add matching keys
                shipped_with_keys = add_match_keys(rhythm_shipped_19200.copy())
                
                print("\nSample standardized shipped records with keys:")
                key_cols = ['Customer_PO', 'Style', 'Color', 'Size', 'exact_key', 'fuzzy_key']
                available_cols = [col for col in key_cols if col in shipped_with_keys.columns]
                print(shipped_with_keys[available_cols].head())
                
                # Show specific CLA24SW-BB04-BLK records
                cla_records = shipped_with_keys[shipped_with_keys['Style'].str.contains('CLA24SW-BB04-BLK', na=False)]
                if len(cla_records) > 0:
                    print(f"\n{len(cla_records)} CLA24SW-BB04-BLK shipped records:")
                    print(cla_records[['Customer_PO', 'Style', 'Color', 'Size', 'exact_key']].head())
                    
                    # Show the exact keys that should be matched
                    print("\nExact keys for CLA24SW-BB04-BLK shipped records:")
                    for key in cla_records['exact_key'].unique():
                        print(f"   {key}")
            
        else:
            print("❌ No shipped records found for RHYTHM PO 19200")
            
            # Check what RHYTHM shipped data exists
            all_rhythm_shipped = run_sql("SELECT DISTINCT \"Customer PO\", Customer FROM shipped WHERE Customer LIKE '%RHYTHM%' LIMIT 10")
            print(f"\nFound {len(all_rhythm_shipped)} total RHYTHM shipped records with POs:")
            print(all_rhythm_shipped)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_rhythm_shipped_data()
