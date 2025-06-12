import pandas as pd
import numpy as np
import logging
from rapidfuzz import fuzz, process
from tqdm import tqdm
import datetime

def create_matching_key(row, include_size=True):
    """
    Builds a matching key from the main columns for exact or fuzzy match.
    """
    parts = []
    if pd.notna(row.get('Canonical_Customer')):
        parts.append(str(row['Canonical_Customer']).strip().upper())
    po = row.get('Customer_PO') or row.get('Customer_Alt_PO')
    if pd.notna(po):
        parts.append(str(po).strip().upper())
    style = row.get('Style') or row.get('Pattern_ID')
    if pd.notna(style):
        parts.append(str(style).strip().upper())
    if pd.notna(row.get('Color')):
        parts.append(str(row['Color']).strip().upper())
    if include_size and pd.notna(row.get('Size')):
        parts.append(str(row['Size']).strip().upper())
    return '|'.join(parts) if parts else None

def add_match_keys(df):
    """
    Add 'exact_key' and 'fuzzy_key' columns to the dataframe.
    """
    df = df.copy()
    df['exact_key'] = df.apply(lambda row: create_matching_key(row, include_size=True), axis=1)
    df['fuzzy_key'] = df.apply(lambda row: create_matching_key(row, include_size=False), axis=1)
    return df

def weighted_fuzzy_score(row1, row2, weights=None):
    """
    Calculate a weighted fuzzy match score between two records.
    """
    if weights is None:
        weights = {'po': 0.3, 'style': 0.3, 'color': 0.2, 'size': 0.2}
    scores = {}

    # PO Score
    po1 = row1.get('Customer_PO') or row1.get('Customer_Alt_PO') or ''
    po2_primary = row2.get('Customer_PO') or ''
    po2_alt = row2.get('Customer_Alt_PO') or ''
    po_scores = [
        fuzz.token_sort_ratio(str(po1), str(po2_primary)),
        fuzz.token_sort_ratio(str(po1), str(po2_alt))
    ]
    scores['po'] = max(po_scores)

    # Style Score
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

    total_score = sum(scores[key] * weights[key] for key in weights)
    return total_score, scores

def aggregate_quantities(packed_df, shipped_df):
    """
    Combine packed and shipped data, sum by all match keys.
    """
    agg_cols = [
        'Canonical_Customer', 'Customer', 'Customer_PO', 'Customer_Alt_PO',
        'Style', 'Pattern_ID', 'Color', 'Size'
    ]
    packed_agg = packed_df.groupby(agg_cols, as_index=False)['Qty'].sum().rename(columns={'Qty': 'Packed_Qty'})
    shipped_agg = shipped_df.groupby(agg_cols, as_index=False)['Qty'].sum().rename(columns={'Qty': 'Shipped_Qty'})
    combined = pd.merge(
        packed_agg, shipped_agg, how='outer', on=agg_cols
    ).fillna(0)
    combined['Source_Type'] = combined.apply(
        lambda r: ','.join([t for t, q in [('PACKED', r.Packed_Qty), ('SHIPPED', r.Shipped_Qty)] if q > 0]), axis=1
    )
    return combined

def exact_match(combined_df, orders_df):
    """
    Perform vectorised exact matching between packed/shipped and orders.
    """
    logging.info("Performing exact match...")
    combined_with_keys = add_match_keys(combined_df)
    orders_with_keys = add_match_keys(orders_df)

    merged = pd.merge(
        combined_with_keys, orders_with_keys,
        left_on='exact_key', right_on='exact_key',
        suffixes=('', '_order'),
        how='left', indicator=True
    )

    # Mark exact matches
    merged['Match_Type'] = np.where(merged['_merge'] == 'both', 'EXACT', 'NO_MATCH')
    merged['Match_Score'] = np.where(merged['Match_Type'] == 'EXACT', 100, 0)
    merged['Ordered_Qty'] = merged['Ordered_Qty'].fillna(0)
    merged['Match_Count'] = merged.groupby('exact_key')['exact_key'].transform('count')
    merged['Best_Match_PO'] = merged['Customer_PO_order']
    merged['Best_Match_Alt_PO'] = merged['Customer_Alt_PO_order']
    merged['Best_Match_Style'] = merged['Style_order']
    merged['Best_Match_Pattern_ID'] = merged['Pattern_ID_order']
    merged['Best_Match_Color'] = merged['Color_order']
    merged['Best_Match_Size'] = merged['Size_order']

    keep_cols = list(combined_with_keys.columns) + [
        'Ordered_Qty', 'Match_Type', 'Match_Score', 'Match_Count',
        'Best_Match_PO', 'Best_Match_Alt_PO', 'Best_Match_Style',
        'Best_Match_Pattern_ID', 'Best_Match_Color', 'Best_Match_Size'
    ]
    results = merged[keep_cols].copy()
    unmatched = results[results['Match_Type'] != 'EXACT'].copy()
    return results, unmatched, orders_with_keys

def fuzzy_match(unmatched_df, orders_with_keys, threshold=75):
    """
    Fuzzy match only unmatched records, optimized with customer grouping.
    """
    logging.info(f"Performing fuzzy match on {len(unmatched_df)} unmatched records...")
    
    if unmatched_df.empty:
        return pd.DataFrame()
    
    results = []
    customers = unmatched_df['Canonical_Customer'].unique()
    for customer in customers:
        customer_unmatched = unmatched_df[unmatched_df['Canonical_Customer'] == customer]
        customer_orders = orders_with_keys[orders_with_keys['Canonical_Customer'] == customer]
        if customer_orders.empty:
            for idx, unmatched_row in customer_unmatched.iterrows():
                result = unmatched_row.to_dict()
                result.update({
                    'Match_Type': 'NO_MATCH',
                    'Match_Score': 0,
                    'PO_Match_Score': 0,
                    'Alt_PO_Match_Score': 0,
                    'Best_Match_Field': None,
                    'Best_Match_PO': None,
                    'Best_Match_Alt_PO': None,
                    'Best_Match_Style': None,
                    'Best_Match_Pattern_ID': None,
                    'Best_Match_Color': None,
                    'Best_Match_Size': None,
                    'Ordered_Qty': 0,
                    'Match_Count': 0
                })
                results.append(result)
            continue

        unmatched_rows = customer_unmatched.reset_index(drop=True)
        orders_rows = customer_orders.reset_index(drop=True)

        # Prepare lists for cdist
        unmatched_po = unmatched_rows['Customer_PO'].fillna('').astype(str).tolist()
        unmatched_alt_po = unmatched_rows['Customer_Alt_PO'].fillna('').astype(str).tolist()
        orders_po = orders_rows['Customer_PO'].fillna('').astype(str).tolist()
        orders_alt_po = orders_rows['Customer_Alt_PO'].fillna('').astype(str).tolist()

        # Vectorized similarity for PO and Alt_PO
        po_sim = process.cdist(unmatched_po, orders_po, scorer=fuzz.token_sort_ratio, dtype=np.uint8)
        alt_po_sim = process.cdist(unmatched_alt_po, orders_alt_po, scorer=fuzz.token_sort_ratio, dtype=np.uint8)

        for i in range(len(unmatched_rows)):
            best_po_idx = po_sim[i].argmax()
            best_alt_po_idx = alt_po_sim[i].argmax()
            best_po_score = po_sim[i, best_po_idx]
            best_alt_po_score = alt_po_sim[i, best_alt_po_idx]

            if best_po_score >= best_alt_po_score:
                best_score = best_po_score
                best_field = 'PO'
                best_idx = best_po_idx
            else:
                best_score = best_alt_po_score
                best_field = 'Alt_PO'
                best_idx = best_alt_po_idx

            best_candidate = orders_rows.iloc[best_idx] if best_score >= threshold else None
            unmatched_row_dict = unmatched_rows.iloc[i].to_dict()
            if best_candidate is not None:
                result = unmatched_row_dict.copy()
                result.update({
                    'Match_Type': 'FUZZY',
                    'Match_Score': best_score,
                    'PO_Match_Score': best_po_score,
                    'Alt_PO_Match_Score': best_alt_po_score,
                    'Best_Match_Field': best_field,
                    'Best_Match_PO': best_candidate.get('Customer_PO'),
                    'Best_Match_Alt_PO': best_candidate.get('Customer_Alt_PO'),
                    'Best_Match_Style': best_candidate.get('Style'),
                    'Best_Match_Pattern_ID': best_candidate.get('Pattern_ID'),
                    'Best_Match_Color': best_candidate.get('Color'),
                    'Best_Match_Size': best_candidate.get('Size'),
                    'Ordered_Qty': best_candidate.get('Ordered_Qty', 0),
                    'Match_Count': 1
                })
            else:
                result = unmatched_row_dict.copy()
                result.update({
                    'Match_Type': 'NO_MATCH',
                    'Match_Score': max(best_po_score, best_alt_po_score),
                    'PO_Match_Score': best_po_score,
                    'Alt_PO_Match_Score': best_alt_po_score,
                    'Best_Match_Field': None,
                    'Best_Match_PO': None,
                    'Best_Match_Alt_PO': None,
                    'Best_Match_Style': None,
                    'Best_Match_Pattern_ID': None,
                    'Best_Match_Color': None,
                    'Best_Match_Size': None,
                    'Ordered_Qty': 0,
                    'Match_Count': 0
                })
            results.append(result)
    logging.info(f"Fuzzy matching completed. Processed {len(results)} records.")
    return pd.DataFrame(results)

def compute_data_quality_flags(df):
    """
    Add data quality metrics and flags to the results DataFrame.
    """
    # Group by PO, Style, Color (and Alt_PO if that's the matched field)
    group_keys = ['Best_Match_Field', 'Best_Match_PO', 'Best_Match_Alt_PO', 'Style', 'Color']
    # Use Best_Match_PO or Best_Match_Alt_PO depending on Best_Match_Field
    df['Group_PO'] = np.where(df['Best_Match_Field'] == 'Alt_PO', df['Best_Match_Alt_PO'], df['Best_Match_PO'])
    group_cols = ['Group_PO', 'Style', 'Color']
    grouped = df.groupby(group_cols, dropna=False).agg({
        'Packed_Qty': 'sum',
        'Shipped_Qty': 'sum',
        'Ordered_Qty': 'sum',
        'Match_Type': 'first',
        'Match_Score': 'max',
    }).reset_index()
    grouped['Qty_Variance'] = grouped['Ordered_Qty'] - (grouped['Packed_Qty'] + grouped['Shipped_Qty'])
    grouped['Qty_Variance_Pct'] = np.where(
        grouped['Ordered_Qty'] > 0,
        (grouped['Qty_Variance'] / grouped['Ordered_Qty']) * 100,
        0
    )
    def quality_flag(row):
        if row['Match_Type'] == 'EXACT' and abs(row['Qty_Variance_Pct']) <= 5:
            return 'GOOD'
        elif row['Match_Type'] == 'FUZZY' and row['Match_Score'] >= 90 and abs(row['Qty_Variance_Pct']) <= 5:
            return 'ACCEPTABLE'
        elif row['Match_Type'] == 'FUZZY' and row['Match_Score'] >= 75 and abs(row['Qty_Variance_Pct']) <= 5:
            return 'QUESTIONABLE'
        else:
            return 'POOR'
    grouped['Data_Quality_Flag'] = grouped.apply(quality_flag, axis=1)
    # Merge back to original df on PO, Style, Color
    df = df.merge(
        grouped[group_cols + ['Qty_Variance', 'Qty_Variance_Pct', 'Data_Quality_Flag']],
        left_on=group_cols,
        right_on=group_cols,
        how='left',
        suffixes=('', '_group')
    )
    return df

def summarize(results_df):
    """
    Build summary stats by Canonical_Customer.
    """
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
    return summary_stats

def match_records(packed_std, shipped_std, orders_std, threshold=75):
    """
    Orchestrates the matching pipeline: aggregation, exact, then fuzzy, then merge.
    Returns: (results DataFrame, summary DataFrame)
    """
    logging.info(f"Starting match_records with {len(packed_std)} packed, {len(shipped_std)} shipped, {len(orders_std)} orders")
    
    logging.info("Aggregating packed and shipped quantities...")
    combined_df = aggregate_quantities(packed_std, shipped_std)
    logging.info(f"Combined dataset size: {len(combined_df)} records")
    
    logging.info("Running exact matching pipeline...")
    exact_results, unmatched, orders_with_keys = exact_match(combined_df, orders_std)
    exact_matches = len(exact_results) - len(unmatched)
    logging.info(f"Exact matching complete: {exact_matches} exact matches, {len(unmatched)} unmatched records")

    if not unmatched.empty:
        logging.info("Running fuzzy matching on unmatched records...")
        fuzzy_results = fuzzy_match(unmatched, orders_with_keys, threshold)
        
        # Combine exact and fuzzy results
        exact_matched = exact_results[exact_results['Match_Type'] == 'EXACT']
        results_df = pd.concat([exact_matched, fuzzy_results], ignore_index=True)
        logging.info(f"Combined results: {len(exact_matched)} exact + {len(fuzzy_results)} fuzzy = {len(results_df)} total")
    else:
        results_df = exact_results
        logging.info("No unmatched records - using exact results only")

    logging.info("Adding data quality metrics and flags...")
    results_df = compute_data_quality_flags(results_df)
    summary_stats = summarize(results_df)
    
    logging.info(f"Match_records completed. Final dataset: {len(results_df)} records")
    return results_df, summary_stats

