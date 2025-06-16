import logging
import argparse
import sys
import os
from pathlib import Path

# Add the src directory to Python path for module imports
script_dir = Path(__file__).parent
src_dir = script_dir.parent
sys.path.insert(0, str(src_dir))

from audit_pipeline.config import load_env, run_sql, load_customer_map
from audit_pipeline.etl import standardize_dataset, handle_master_order_list
from audit_pipeline.matching import match_records
from audit_pipeline.report import write_excel

def main():
    import datetime
    start_time = datetime.datetime.now()
    print(f"[START] Audit process started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    parser = argparse.ArgumentParser(description='Run customer audit with fuzzy matching')
    parser.add_argument('--sample', type=int, help='Sample N rows for quick dev runs (e.g., --sample 1000)')
    args = parser.parse_args()

    logging.basicConfig(filename='audit.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    print("Loading environment variables...")
    load_env()
    print("Loading customer mapping...")
    customer_alias_map = load_customer_map()
    
    print("Running SQL queries for packed, shipped, and master order list...")
    # Run base queries and apply filters in Python
    packed = run_sql('staging/v_packed_products.sql', 'distribution')
    shipped = run_sql('staging/v_shipped.sql', 'wah')
    master = run_sql('staging/v_master_order_list.sql', 'orders')
    
    # Apply filters in Python (more flexible than SQL)
    print("Applying filters...")
    if 'Size' in packed.columns:
        packed = packed[packed['Size'] != 'SMS']
        print(f"Packed data filtered: {len(packed)} rows remaining after removing SMS sizes")
    
    if 'Size' in shipped.columns:
        shipped = shipped[shipped['Size'] != 'SMS']
        print(f"Shipped data filtered: {len(shipped)} rows remaining after removing SMS sizes")
    # Apply sampling if requested
    if args.sample:
        logging.info(f"Sampling {args.sample} rows from each dataset")
        print(f"Sampling {args.sample} rows from each dataset...")
        packed = packed.head(args.sample)
        shipped = shipped.head(args.sample)
        master = master.head(args.sample)

    print("Standardizing datasets...")
    orders_std = handle_master_order_list(master, customer_alias_map)
    packed_std = standardize_dataset(packed, 'PACKED', 'Qty', customer_alias_map)
    shipped_std = standardize_dataset(shipped, 'SHIPPED', 'Qty', customer_alias_map)
    
    # Debug: Check standardized data
    print(f"Standardized data sizes - Orders: {len(orders_std)}, Packed: {len(packed_std)}, Shipped: {len(shipped_std)}")
    if len(orders_std) == 0:
        print("WARNING: Orders dataset is empty after standardization!")
    if len(packed_std) == 0:
        print("WARNING: Packed dataset is empty after standardization!")
    if len(shipped_std) == 0:
        print("WARNING: Shipped dataset is empty after standardization!")

    print("Matching records...")
    results, summary = match_records(packed_std, shipped_std, orders_std)
    
    # Debug: Check results
    print(f"Results shape: {results.shape if results is not None else 'None'}")
    print(f"Summary shape: {summary.shape if summary is not None else 'None'}")
    
    if results is not None and len(results) > 0:
        print(f"Sample of results columns: {list(results.columns)[:10]}")
        print(f"Match type distribution: {results['Match_Type'].value_counts().to_dict() if 'Match_Type' in results.columns else 'No Match_Type column'}")
    else:
        print("WARNING: No results returned from matching process!")

    print("Writing Excel report...")
    

    # Use absolute path for outputs
    output_dir = Path(__file__).parent.parent.parent / 'outputs'
    write_excel(results, summary, outdir=str(output_dir))

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print(f"[END] Audit process finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[DURATION] Total duration: {duration}")

if __name__ == "__main__":
    main()
