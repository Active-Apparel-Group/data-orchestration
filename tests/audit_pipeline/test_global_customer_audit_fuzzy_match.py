"""
Script: test_global_customer_audit_fuzzy_match.py
Purpose: Audit and match packed, shipped, and order list records by customer for data integrity analysis.

Enhanced Approach:
1. Standardize all datasets to consistent long format with key fields
2. Create canonical customer mapping across all sources
3. Process customers individually with progress tracking
4. Implement tiered matching strategy:
   - Exact matches first (high performance)
   - Fuzzy matching for unmatched records only
   - Weighted scoring based on business importance
4. Include Ordered_Qty for data integrity analysis
5. Generate comprehensive data quality metrics

Key Fields: Customer, Customer_PO, Style, Color, Size
Alternative Fields: Customer_Alt_PO, Pattern_ID (style alternative)

Dependencies: pandas, pyodbc, yaml, fuzzywuzzy, json, threading, os
"""

import pandas as pd
import os
import yaml
from datetime import datetime
from tqdm import tqdm
from fuzzywuzzy import fuzz
import json
import threading
import numpy as np



# --- Config and DB connection logic (reuse from main.py) ---
try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as config_file:
        config = yaml.safe_load(config_file)
        DB_CONFIG = config['databases']
except Exception as e:
    print(f"Error loading configuration: {e}")
    DB_CONFIG = {
        'distribution': {
            'host': '192.168.30.3',
            'port': 1433,
            'database': 'Distribution',
            'username': 'sa',
            'password': 'ls*2013'
        }
    }

import pyodbc

def get_connection(db_key):
    config = DB_CONFIG[db_key.lower()]
    conn_str = f"DRIVER={{SQL Server}};SERVER={config['host']};DATABASE={config['database']};"
    if config.get('trusted_connection', '').lower() in ('yes', 'true', '1'):
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={config['username']};PWD={config['password']};"
    conn_str += "Encrypt=no;TrustServerCertificate=yes;"
    return pyodbc.connect(conn_str)

def run_sql(filename, db_key):
    views_dir = os.path.join(os.path.dirname(__file__), '..', 'views')
    with open(os.path.join(views_dir, filename), "r") as f:
        query = f.read()
    with get_connection(db_key) as conn:
        return pd.read_sql(query, conn)


# --- Data Standardization Functions ---
def standardize_dataset(df, source_type, qty_col='Qty'):
    """
    Standardize dataset to consistent format with core matching fields.
    Returns DataFrame with columns: [Canonical_Customer, Customer, Customer_PO, 
    Customer_Alt_PO, Style, Pattern_ID, Color, Size, Qty, Source_Type]
    """
    # Create base structure
    standardized = df.copy()
    
    # Ensure all required columns exist
    required_cols = ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']
    for col in required_cols:
        if col not in standardized.columns:
            standardized[col] = None
    
    # Handle alternative columns
    if 'Customer_Alt_PO' not in standardized.columns:
        standardized['Customer_Alt_PO'] = None
    if 'Pattern_ID' not in standardized.columns:
        standardized['Pattern_ID'] = None
    
    # Standardize quantity column
    if qty_col in standardized.columns and qty_col != 'Qty':
        standardized['Qty'] = standardized[qty_col]
    elif 'Qty' not in standardized.columns:
        standardized['Qty'] = 1  # Default for records without explicit quantity
    
    # Add source type
    standardized['Source_Type'] = source_type
    
    # Clean and normalize text fields
    text_cols = ['Customer', 'Customer_PO', 'Customer_Alt_PO', 'Style', 'Pattern_ID', 'Color', 'Size']
    for col in text_cols:
        if col in standardized.columns:
            standardized[col] = standardized[col].astype(str).str.strip().str.upper()
            standardized[col] = standardized[col].replace('NAN', None).replace('', None)
    
    # Apply canonical customer mapping
    standardized['Canonical_Customer'] = standardized['Customer'].apply(canonicalize_customer)
    
    return standardized

def create_matching_key(row, include_size=True):
    """Create a standardized matching key from core fields."""
    parts = []
    
    # Customer (canonical)
    if pd.notna(row.get('Canonical_Customer')):
        parts.append(str(row['Canonical_Customer']).strip().upper())
    
    # PO (primary or alt)
    po = row.get('Customer_PO') or row.get('Customer_Alt_PO')
    if pd.notna(po):
        parts.append(str(po).strip().upper())
    
    # Style (primary or pattern)
    style = row.get('Style') or row.get('Pattern_ID')
    if pd.notna(style):
        parts.append(str(style).strip().upper())
    
    # Color
    if pd.notna(row.get('Color')):
        parts.append(str(row['Color']).strip().upper())
    
    # Size (optional)
    if include_size and pd.notna(row.get('Size')):
        parts.append(str(row['Size']).strip().upper())
    
    return '|'.join(parts) if parts else None

# --- Load raw data from all sources ---
print("Loading data from all sources...")
packed_df = run_sql('v_packed_products.sql', 'distribution')
shipped_df = run_sql('v_shipped.sql', 'wah')
master_df = run_sql('v_master_order_list.sql', 'orders')

print(f"Raw data loaded: {len(packed_df)} packed, {len(shipped_df)} shipped, {len(master_df)} orders")

# --- Load canonical customer mapping ---
with open(os.path.join(os.path.dirname(__file__), '..', 'docs', 'customer_mapping.yaml'), 'r') as f:
    customer_map_yaml = yaml.safe_load(f)

def build_customer_alias_map(customer_map_yaml):
    alias_map = {}
    for entry in customer_map_yaml['customers']:
        canonical = entry['canonical']
        for alias in entry.get('aliases', []):
            alias_map[alias.strip().upper()] = canonical
        # Also map canonical to itself
        alias_map[canonical.strip().upper()] = canonical
        # Map packed_products, shipped, master_order_list, mon_customer_ms if present
        for k in ['packed_products', 'shipped', 'master_order_list', 'mon_customer_ms']:
            v = entry.get(k, '')
            if v:
                alias_map[v.strip().upper()] = canonical
    return alias_map

customer_alias_map = build_customer_alias_map(customer_map_yaml)

def canonicalize_customer(name):
    if not isinstance(name, str) or pd.isna(name):
        return None
    return customer_alias_map.get(name.strip().upper(), name.strip().upper())

# --- Filter for 2025 (customer filter removed for full analysis) ---
# customer_filter = 'SPIRITUAL GANGSTER'

def filter_to_customer(df):
    # Customer filter disabled - return all data
    return df
    # # Try Canonical_Customer first, then Customer
    # if 'Canonical_Customer' in df.columns:
    #     return df[df['Canonical_Customer'].str.upper() == customer_filter.upper()]
    # elif 'Customer' in df.columns:
    #     return df[df['Customer'].str.upper() == customer_filter.upper()]
    # return df

if 'Pack_Date' in packed_df.columns:
    packed_df = packed_df[packed_df['Pack_Date'].apply(lambda x: pd.to_datetime(x).year == 2025 if pd.notnull(x) else False)]
if 'Shipped_Date' in shipped_df.columns:
    shipped_df = shipped_df[shipped_df['Shipped_Date'].apply(lambda x: pd.to_datetime(x).year == 2025 if pd.notnull(x) else False)]

# Apply customer filter (disabled - processing all customers)
packed_df = filter_to_customer(packed_df)
shipped_df = filter_to_customer(shipped_df)
master_df = filter_to_customer(master_df)

print(f"Filtered data for ALL CUSTOMERS: {len(packed_df)} packed, {len(shipped_df)} shipped, {len(master_df)} orders")

# --- Sample data for performance (optional) ---
SAMPLE_SIZE = 10000  # Set to None for full dataset, or a number for sampling
if SAMPLE_SIZE and len(master_df) > SAMPLE_SIZE:
    print(f"Sampling {SAMPLE_SIZE} records from {len(master_df)} orders for performance...")
    master_df = master_df.sample(n=SAMPLE_SIZE, random_state=42)
    print(f"Sampled data: {len(packed_df)} packed, {len(shipped_df)} shipped, {len(master_df)} orders")

# --- Standardize datasets ---
print("Standardizing datasets...")
packed_std = standardize_dataset(packed_df, 'PACKED', 'Qty')
shipped_std = standardize_dataset(shipped_df, 'SHIPPED', 'Qty')

# Handle master order list - may need melting for size columns
def handle_master_order_list(df):
    """Handle master order list which may be in wide format with size columns."""
    print(f"Processing order list with columns: {list(df.columns)}")
    
    # Dynamic approach: Find size columns between 'UNIT OF MEASURE' and 'TOTAL QTY' (or 'Qty')
    size_cols = []
    if 'UNIT OF MEASURE' in df.columns:
        try:
            # Find the range of size columns dynamically
            start_idx = df.columns.get_loc('UNIT OF MEASURE')
            
            # Try to find 'TOTAL QTY' first, then 'Qty' as fallback
            end_col = None
            if 'TOTAL QTY' in df.columns:
                end_col = 'TOTAL QTY'
            elif 'Qty' in df.columns:
                end_col = 'Qty'
            
            if end_col:
                end_idx = df.columns.get_loc(end_col)
                size_cols = df.columns[start_idx + 1:end_idx].tolist()
                print(f"Dynamically found size columns between 'UNIT OF MEASURE' and '{end_col}': {size_cols}")
            else:
                print("Warning: Could not find 'TOTAL QTY' or 'Qty' column for size column range detection")
        except KeyError as e:
            print(f"Error finding size column range: {e}")
    
    if size_cols:
        print(f"Found {len(size_cols)} size columns for melting: {size_cols[:10]}{'...' if len(size_cols) > 10 else ''}")
        
        # Core identification columns for melting
        id_vars = ['Customer', 'Customer_PO', 'Customer_Alt_PO', 'Style', 'Color', 'Pattern_ID']
        # Add optional columns if they exist
        optional_vars = ['Season', 'AAG_Season', 'Category', 'ORDER_TYPE', 'DESTINATION', 
                        'DESTINATION_WAREHOUSE', 'Incoterms', 'Shipping_Method']
        id_vars.extend([col for col in optional_vars if col in df.columns])
        
        print(f"Melting with ID vars: {id_vars}")
        print(f"Melting size columns: {len(size_cols)} columns")
        
        # Melt the DataFrame
        df_melted = df.melt(
            id_vars=id_vars,
            value_vars=size_cols,
            var_name='Size',
            value_name='Ordered_Qty'
        )
        
        # Filter out zero/null quantities and convert to numeric (like Monday.com script)
        df_melted['Ordered_Qty'] = pd.to_numeric(df_melted['Ordered_Qty'], errors='coerce')
        # Filter for quantities > 0 (same as Monday.com script)
        df_melted = df_melted[df_melted['Ordered_Qty'] > 0]
        
        print(f"After melting and filtering for quantities > 0: {len(df_melted)} records")
        
        # Standardize the melted data
        df_std = standardize_dataset(df_melted, 'ORDERS', 'Ordered_Qty')
        
    else:
        print("No size columns found using dynamic detection - assuming long format")
        # Assume long format, standardize with existing Qty
        df_std = standardize_dataset(df, 'ORDERS', 'Qty')
        df_std['Ordered_Qty'] = df_std['Qty']
    
    return df_std

orders_std = handle_master_order_list(master_df)

print(f"Standardized datasets: {len(packed_std)} packed, {len(shipped_std)} shipped, {len(orders_std)} orders")

# --- Enhanced Matching Strategy ---
def create_match_keys(df):
    """Create matching keys for exact and fuzzy matching."""
    df = df.copy()
    df['exact_key'] = df.apply(lambda row: create_matching_key(row, include_size=True), axis=1)
    df['fuzzy_key'] = df.apply(lambda row: create_matching_key(row, include_size=False), axis=1)
    return df

def weighted_fuzzy_score(row1, row2, weights=None):
    """Calculate weighted fuzzy match score between two records."""
    if weights is None:
        weights = {'po': 0.3, 'style': 0.3, 'color': 0.2, 'size': 0.2}
    
    scores = {}
    
    # PO Score (try both primary and alt PO)
    po1 = row1.get('Customer_PO') or row1.get('Customer_Alt_PO') or ''
    po2_primary = row2.get('Customer_PO') or ''
    po2_alt = row2.get('Customer_Alt_PO') or ''
    
    po_scores = [
        fuzz.token_sort_ratio(str(po1), str(po2_primary)),
        fuzz.token_sort_ratio(str(po1), str(po2_alt))
    ]
    scores['po'] = max(po_scores)
    
    # Style Score (try both style and pattern)
    style1 = row1.get('Style') or row1.get('Pattern_ID') or ''
    style2_primary = row2.get('Style') or ''
    style2_pattern = row2.get('Pattern_ID') or ''
    
    style_scores = [
        fuzz.token_sort_ratio(str(style1), str(style2_primary)),
        fuzz.token_sort_ratio(str(style1), str(style2_pattern))
    ]
    scores['style'] = max(style_scores)
    
    # Color Score
    color1 = row1.get('Color') or ''
    color2 = row2.get('Color') or ''
    scores['color'] = fuzz.token_sort_ratio(str(color1), str(color2))
    
    # Size Score
    size1 = row1.get('Size') or ''
    size2 = row2.get('Size') or ''
    scores['size'] = fuzz.token_sort_ratio(str(size1), str(size2))
    
    # Calculate weighted score
    total_score = sum(scores[key] * weights[key] for key in weights.keys())
    return total_score, scores

def perform_matching(packed_shipped_df, orders_df, threshold=75):
    """
    Enhanced matching strategy:
    1. Exact matches first (high performance)
    2. Fuzzy matching for unmatched records
    """
    print("Starting enhanced matching process...")
    
    # Prepare data with matching keys
    ps_with_keys = create_match_keys(packed_shipped_df)
    orders_with_keys = create_match_keys(orders_df)
    
    # Create lookup dictionary for orders by exact key
    orders_exact_lookup = {}
    for idx, row in orders_with_keys.iterrows():
        key = row['exact_key']
        if key and key != 'None':
            if key not in orders_exact_lookup:
                orders_exact_lookup[key] = []
            orders_exact_lookup[key].append(row.to_dict())
      # Only show detailed progress for large datasets
    show_progress = len(ps_with_keys) > 1000
    if show_progress:
        print(f"Created exact match lookup with {len(orders_exact_lookup)} unique keys")
    
    results = []
    exact_matches = 0
    fuzzy_matches = 0
    no_matches = 0
    
    for idx, (_, ps_row) in enumerate(ps_with_keys.iterrows()):
        if show_progress and idx % 1000 == 0:
            print(f"Processing record {idx+1}/{len(ps_with_keys)}...")
        
        match_info = {
            'Match_Type': 'NO_MATCH',
            'Match_Score': 0,
            'Match_Score_Breakdown': None,
            'Best_Match_PO': None,
            'Best_Match_Alt_PO': None,
            'Best_Match_Style': None,
            'Best_Match_Pattern_ID': None,
            'Best_Match_Color': None,
            'Best_Match_Size': None,
            'Ordered_Qty': 0,
            'Match_Count': 0
        }
        
        # Try exact match first
        exact_key = ps_row['exact_key']
        if exact_key and exact_key in orders_exact_lookup:
            # Exact match found
            best_order = orders_exact_lookup[exact_key][0]  # Take first if multiple
            match_info.update({
                'Match_Type': 'EXACT',
                'Match_Score': 100,
                'Best_Match_PO': best_order.get('Customer_PO'),
                'Best_Match_Alt_PO': best_order.get('Customer_Alt_PO'),
                'Best_Match_Style': best_order.get('Style'),
                'Best_Match_Pattern_ID': best_order.get('Pattern_ID'),
                'Best_Match_Color': best_order.get('Color'),
                'Best_Match_Size': best_order.get('Size'),
                'Ordered_Qty': best_order.get('Ordered_Qty', 0),
                'Match_Count': len(orders_exact_lookup[exact_key])            })
            exact_matches += 1
        else:
            # Try fuzzy matching - optimize by grouping orders by customer
            customer = ps_row['Canonical_Customer']
            customer_orders = orders_with_keys[orders_with_keys['Canonical_Customer'] == customer]
            
            candidates = []
            for _, order_row in customer_orders.iterrows():
                score, score_breakdown = weighted_fuzzy_score(ps_row, order_row)
                if score >= threshold:
                    candidates.append((order_row, score, score_breakdown))
            
            if candidates:
                # Find best fuzzy match
                best_candidate = max(candidates, key=lambda x: x[1])
                best_order, best_score, score_breakdown = best_candidate
                
                match_info.update({
                    'Match_Type': 'FUZZY',
                    'Match_Score': best_score,
                    'Match_Score_Breakdown': score_breakdown,
                    'Best_Match_PO': best_order.get('Customer_PO'),
                    'Best_Match_Alt_PO': best_order.get('Customer_Alt_PO'),
                    'Best_Match_Style': best_order.get('Style'),
                    'Best_Match_Pattern_ID': best_order.get('Pattern_ID'),
                    'Best_Match_Color': best_order.get('Color'),
                    'Best_Match_Size': best_order.get('Size'),
                    'Ordered_Qty': best_order.get('Ordered_Qty', 0),
                    'Match_Count': len(candidates)
                })
                fuzzy_matches += 1
            else:
                no_matches += 1
        
        # Combine with original row data
        result = {**ps_row.to_dict(), **match_info}
        results.append(result)
    
    print(f"\nMatching summary:")
    print(f"  Exact matches: {exact_matches}")
    print(f"  Fuzzy matches: {fuzzy_matches}")
    print(f"  No matches: {no_matches}")
    print(f"  Total processed: {len(results)}")
    
    return pd.DataFrame(results)

# --- Process customers one by one with progress tracking ---
print("Building distinct list of customers...")

# Get all unique customers from all datasets
all_customers = set()
all_customers.update(packed_std['Canonical_Customer'].dropna().unique())
all_customers.update(shipped_std['Canonical_Customer'].dropna().unique()) 
all_customers.update(orders_std['Canonical_Customer'].dropna().unique())

customer_list = sorted(list(all_customers))
print(f"Found {len(customer_list)} unique customers: {customer_list[:10]}..." if len(customer_list) > 10 else f"Found {len(customer_list)} unique customers: {customer_list}")

# Process each customer individually
all_results = []
customer_summary = []

print("\nProcessing customers individually...")
for customer in tqdm(customer_list, desc="Processing customers"):
    # Filter data for current customer
    customer_packed = packed_std[packed_std['Canonical_Customer'] == customer]
    customer_shipped = shipped_std[shipped_std['Canonical_Customer'] == customer] 
    customer_orders = orders_std[orders_std['Canonical_Customer'] == customer]
    
    if len(customer_packed) == 0 and len(customer_shipped) == 0 and len(customer_orders) == 0:
        continue
        
    # Combine packed and shipped for this customer
    customer_packed_shipped = pd.concat([customer_packed, customer_shipped], ignore_index=True)
    
    if len(customer_packed_shipped) == 0:
        continue
        
    # Aggregate by key fields to avoid duplicate matches
    agg_cols = ['Canonical_Customer', 'Customer', 'Customer_PO', 'Customer_Alt_PO', 'Style', 'Pattern_ID', 'Color', 'Size']
    customer_agg = customer_packed_shipped.groupby(agg_cols, as_index=False).agg({
        'Qty': 'sum',
        'Source_Type': lambda x: ','.join(sorted(set(x)))
    }).reset_index(drop=True)
    
    # Split quantities by source type for analysis
    customer_agg['Packed_Qty'] = customer_agg.apply(
        lambda row: customer_packed_shipped[
            (customer_packed_shipped['Canonical_Customer'] == row['Canonical_Customer']) &
            (customer_packed_shipped['Customer_PO'] == row['Customer_PO']) &
            (customer_packed_shipped['Style'] == row['Style']) &
            (customer_packed_shipped['Color'] == row['Color']) &
            (customer_packed_shipped['Size'] == row['Size']) &
            (customer_packed_shipped['Source_Type'] == 'PACKED')
        ]['Qty'].sum(), axis=1
    )
    
    customer_agg['Shipped_Qty'] = customer_agg.apply(
        lambda row: customer_packed_shipped[
            (customer_packed_shipped['Canonical_Customer'] == row['Canonical_Customer']) &
            (customer_packed_shipped['Customer_PO'] == row['Customer_PO']) &
            (customer_packed_shipped['Style'] == row['Style']) &
            (customer_packed_shipped['Color'] == row['Color']) &
            (customer_packed_shipped['Size'] == row['Size']) &
            (customer_packed_shipped['Source_Type'] == 'SHIPPED')
        ]['Qty'].sum(), axis=1
    )
    
    # Perform matching for this customer
    if len(customer_agg) > 0:
        customer_results = perform_matching(customer_agg, customer_orders, threshold=75)
        all_results.append(customer_results)
        
        # Track customer summary
        customer_summary.append({
            'Customer': customer,
            'Packed_Records': len(customer_packed),
            'Shipped_Records': len(customer_shipped), 
            'Order_Records': len(customer_orders),
            'Combined_Records': len(customer_agg),
            'Packed_Qty': customer_results['Packed_Qty'].sum(),
            'Shipped_Qty': customer_results['Shipped_Qty'].sum(),
            'Ordered_Qty': customer_results['Ordered_Qty'].sum(),
            'Exact_Matches': len(customer_results[customer_results['Match_Type'] == 'EXACT']),
            'Fuzzy_Matches': len(customer_results[customer_results['Match_Type'] == 'FUZZY']),
            'No_Matches': len(customer_results[customer_results['Match_Type'] == 'NO_MATCH'])
        })

# Combine all customer results
if all_results:
    results_df = pd.concat(all_results, ignore_index=True)
    print(f"\nCombined results from {len(all_results)} customers: {len(results_df)} total records")
else:
    print("No results to process")
    exit()

# --- Add data quality metrics ---
print("Adding data quality metrics...")
print("Adding data quality metrics...")
results_df['Qty_Variance'] = results_df['Ordered_Qty'] - (results_df['Packed_Qty'] + results_df['Shipped_Qty'])
results_df['Qty_Variance_Pct'] = np.where(
    results_df['Ordered_Qty'] > 0,
    (results_df['Qty_Variance'] / results_df['Ordered_Qty']) * 100,
    0
)

# Add data quality flags
results_df['Data_Quality_Flag'] = np.where(
    results_df['Match_Type'] == 'EXACT', 'GOOD',
    np.where(
        (results_df['Match_Type'] == 'FUZZY') & (results_df['Match_Score'] >= 90), 'ACCEPTABLE',
        np.where(
            (results_df['Match_Type'] == 'FUZZY') & (results_df['Match_Score'] >= 75), 'QUESTIONABLE',
            'POOR'
        )
    )
)

# --- Enhanced Excel output with data quality insights ---
import xlsxwriter

# Columns to include in Excel output with data integrity focus
excel_keep_cols = [
    'Canonical_Customer', 'Customer', 'Customer_PO', 'Customer_Alt_PO', 'Style', 'Pattern_ID', 'Color', 'Size',
    'Packed_Qty', 'Shipped_Qty', 'Ordered_Qty', 'Qty_Variance', 'Qty_Variance_Pct',
    'Match_Type', 'Match_Score', 'Data_Quality_Flag', 'Match_Count',
    'Best_Match_PO', 'Best_Match_Alt_PO', 'Best_Match_Style', 'Best_Match_Pattern_ID', 
    'Best_Match_Color', 'Best_Match_Size'
]

# Create summary statistics
summary_stats = results_df.groupby('Canonical_Customer').agg({
    'Packed_Qty': 'sum',
    'Shipped_Qty': 'sum', 
    'Ordered_Qty': 'sum',
    'Match_Type': lambda x: (x == 'EXACT').sum(),
    'Data_Quality_Flag': lambda x: (x == 'GOOD').sum()
}).rename(columns={
    'Match_Type': 'Exact_Matches',
    'Data_Quality_Flag': 'Good_Quality_Records'
}).reset_index()

summary_stats['Total_Records'] = results_df.groupby('Canonical_Customer').size().values
summary_stats['Exact_Match_Rate'] = (summary_stats['Exact_Matches'] / summary_stats['Total_Records'] * 100).round(2)
summary_stats['Data_Quality_Rate'] = (summary_stats['Good_Quality_Records'] / summary_stats['Total_Records'] * 100).round(2)

print("\n=== CUSTOMER PROCESSING SUMMARY ===")
customer_summary_df = pd.DataFrame(customer_summary)
if len(customer_summary_df) > 0:
    print(customer_summary_df)
    
print("\n=== DATA INTEGRITY SUMMARY ===")
print(summary_stats)

# Export to Excel
output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
os.makedirs(output_dir, exist_ok=True)
excel_path = os.path.join(output_dir, 'global_customer_audit_fuzzy_match_by_customer.xlsx')

with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
    # Summary tab first
    summary_stats.to_excel(writer, sheet_name='SUMMARY', index=False)
    
    # Customer processing summary tab
    if len(customer_summary_df) > 0:
        customer_summary_df.to_excel(writer, sheet_name='CUSTOMER_PROCESSING', index=False)
    
    # Customer detail tabs
    for cust in results_df['Canonical_Customer'].dropna().unique():
        cust_df = results_df[results_df['Canonical_Customer'] == cust].copy()
        
        # Sort by data quality and match score
        cust_df = cust_df.sort_values(by=['Data_Quality_Flag', 'Match_Score'], ascending=[True, False])
        
        # Only keep the desired columns
        cust_df = cust_df[[col for col in excel_keep_cols if col in cust_df.columns]]
        
        # Create sheet name (max 31 chars)
        sheet_name = str(cust)[:31]
        cust_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Add conditional formatting for data quality
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Define formats
        good_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        acceptable_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
        poor_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        
        # Apply conditional formatting to Data_Quality_Flag column
        if 'Data_Quality_Flag' in cust_df.columns:
            flag_col_idx = cust_df.columns.get_loc('Data_Quality_Flag')
            
            for row_idx, flag in enumerate(cust_df['Data_Quality_Flag'], start=1):
                if flag == 'GOOD':
                    worksheet.write(row_idx, flag_col_idx, flag, good_format)
                elif flag in ['ACCEPTABLE', 'QUESTIONABLE']:
                    worksheet.write(row_idx, flag_col_idx, flag, acceptable_format)
                else:
                    worksheet.write(row_idx, flag_col_idx, flag, poor_format)

print(f"\n✅ Enhanced Excel exported to {excel_path}")
print(f"   - Summary tab with data integrity metrics")
print(f"   - {len(results_df['Canonical_Customer'].dropna().unique())} customer detail tabs")
print(f"   - Color-coded data quality flags")
print(f"   - Ordered_Qty included for variance analysis")

# --- Print sample results for verification ---
print("\n=== SAMPLE RESULTS ===")
sample_results = results_df[['Canonical_Customer', 'Customer_PO', 'Style', 'Color', 'Size', 
                            'Packed_Qty', 'Shipped_Qty', 'Ordered_Qty', 'Match_Type', 'Match_Score', 
                            'Data_Quality_Flag']].head(10)
print(sample_results.to_string(index=False))