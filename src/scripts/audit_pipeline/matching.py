import pandas as pd
import numpy as np
import logging
from rapidfuzz import fuzz, process
from tqdm import tqdm
import datetime
from .config import get_customer_matching_config

# Constants for invalid PO values
INVALID_PO_TOKENS = {'', 'NONE', 'NULL', 'NAN', 'N/A'}
TEMP_NONE_REPLACEMENT = '__TEMP_NONE__'

# Default fuzzy matching weights
DEFAULT_FUZZY_WEIGHTS = {'po': 0.3, 'style': 0.3, 'color': 0.2, 'size': 0.2}

# Global cache for customer configurations to prevent repeated YAML loading
_CUSTOMER_CONFIG_CACHE = {}

# Default simple configuration for fallback
DEFAULT_SIMPLE_CONFIG = {
    'style_match_strategy': 'standard',
    'style_field_name': 'Style',
    'exact_match_fields': ['Canonical_Customer', 'Customer_PO', 'Style', 'Color']
}

def get_customer_config_cached(canonical_customer):
    """
    Get customer-specific matching configuration with caching to prevent repeated YAML loading.
    Performance-optimized version that caches results and provides graceful fallback.
    """
    if not canonical_customer:
        return DEFAULT_SIMPLE_CONFIG
        
    if canonical_customer in _CUSTOMER_CONFIG_CACHE:
        return _CUSTOMER_CONFIG_CACHE[canonical_customer]
    
    try:
        config = get_customer_matching_config(canonical_customer)
        _CUSTOMER_CONFIG_CACHE[canonical_customer] = config
        logging.debug(f"Loaded config for customer: {canonical_customer}")
        return config
    except Exception as e:
        # Log warning but don't fail - use fallback
        logging.warning(f"Failed to load config for customer {canonical_customer}: {e}. Using default.")
        _CUSTOMER_CONFIG_CACHE[canonical_customer] = DEFAULT_SIMPLE_CONFIG
        return DEFAULT_SIMPLE_CONFIG

def preload_customer_configs(df):
    """
    Pre-load customer configurations for all unique customers in the dataset.
    This prevents per-row config loading during matching operations.
    """
    unique_customers = df['Canonical_Customer'].dropna().unique()
    logging.info(f"Pre-loading configurations for {len(unique_customers)} unique customers...")
    
    for customer in unique_customers:
        get_customer_config_cached(customer)
    
    logging.info(f"Customer configurations cached: {len(_CUSTOMER_CONFIG_CACHE)} customers")

def is_valid_po_value(value):
    """
    Check if a PO value is valid for matching (not null, empty, or placeholder).
    """
    if pd.isna(value):
        return False
    str_val = str(value).strip().upper()
    return str_val not in INVALID_PO_TOKENS

def is_valid_po_series(series):
    """
    Vectorized version of is_valid_po_value for pandas Series.
    """
    return ~(series.isna() | series.str.strip().str.upper().isin(INVALID_PO_TOKENS))

def get_style_value_and_source(row, canonical_customer):
    """
    Get style value and source column based on customer configuration.
    Returns tuple: (style_value, style_source)
    Performance-optimized version using cached configurations.
    """
    # Check customer-specific config FIRST to determine priority order
    if canonical_customer:
        try:
            customer_config = get_customer_config_cached(canonical_customer)
            
            if customer_config.get('style_match_strategy') == 'alias_related_item':
                # For RHYTHM and similar: prioritize ALIAS/RELATED ITEM first
                # Priority: ALIAS/RELATED ITEM -> Style -> Pattern_ID
                if pd.notna(row.get('ALIAS/RELATED ITEM')) and str(row.get('ALIAS/RELATED ITEM', '')).strip():
                    return str(row['ALIAS/RELATED ITEM']).strip(), 'ALIAS/RELATED ITEM'
                elif pd.notna(row.get('Style')) and str(row.get('Style', '')).strip():
                    return str(row['Style']).strip(), 'Style'
                elif pd.notna(row.get('Pattern_ID')) and str(row.get('Pattern_ID', '')).strip():
                    return str(row['Pattern_ID']).strip(), 'Pattern_ID'
                else:
                    return None, None
            
        except Exception:
            # Fallback to standard logic if config lookup fails
            pass
    
    # Standard logic for 'standard' strategy or fallback
    # Priority: Style -> Pattern_ID
    if pd.notna(row.get('Style')) and str(row.get('Style', '')).strip():
        return str(row['Style']).strip(), 'Style'
    elif pd.notna(row.get('Pattern_ID')) and str(row.get('Pattern_ID', '')).strip():
        return str(row['Pattern_ID']).strip(), 'Pattern_ID'
    
    return None, None

def create_matching_key(row, include_size=True, canonical_customer=None):
    """
    Builds a matching key from the main columns for exact or fuzzy match.
    Updated to handle customer-specific style fields and both PO fields properly for exact matching.
    """
    parts = []
    if pd.notna(row.get('Canonical_Customer')):
        parts.append(str(row['Canonical_Customer']).strip().upper())
    
    # Use Customer_PO if available and valid, otherwise Customer_Alt_PO
    # This ensures we get the most specific PO for matching
    po = None
    if is_valid_po_value(row.get('Customer_PO')):
        po = str(row['Customer_PO']).strip().upper()
    elif is_valid_po_value(row.get('Customer_Alt_PO')):
        po = str(row['Customer_Alt_PO']).strip().upper()
    
    if po:
        parts.append(po)
    
    # Use customer-aware style logic
    customer = canonical_customer or row.get('Canonical_Customer')
    if customer:
        style_value, style_source = get_style_value_and_source(row, customer)
        if style_value:
            parts.append(style_value.upper())
            # Store style source for tracking
            if hasattr(row, 'name') and hasattr(row, 'index'):
                # This is a pandas Series, we can't modify it directly
                pass
    else:
        # Fallback to original logic if no customer available
        style = row.get('Style') or row.get('Pattern_ID')
        if pd.notna(style):
            parts.append(str(style).strip().upper())
    
    if pd.notna(row.get('Color')):
        parts.append(str(row['Color']).strip().upper())
    if include_size and pd.notna(row.get('Size')):
        parts.append(str(row['Size']).strip().upper())
    return '|'.join(parts) if parts else None

def create_alternate_matching_keys(row, include_size=True, canonical_customer=None):
    """
    Create separate matching keys for both PO fields to enable cross-field exact matching.
    Returns tuple of (primary_key, alt_key) where primary uses Customer_PO and alt uses Customer_Alt_PO.
    Updated to support customer-specific style fields.
    """
    base_parts = []
    if pd.notna(row.get('Canonical_Customer')):
        base_parts.append(str(row['Canonical_Customer']).strip().upper())
    
    # Use customer-aware style logic
    customer = canonical_customer or row.get('Canonical_Customer')
    if customer:
        style_value, style_source = get_style_value_and_source(row, customer)
        if style_value:
            base_parts.append(style_value.upper())
    else:
        # Fallback to original logic
        style = row.get('Style') or row.get('Pattern_ID')
        if pd.notna(style):
            base_parts.append(str(style).strip().upper())
    
    if pd.notna(row.get('Color')):
        base_parts.append(str(row['Color']).strip().upper())
    if include_size and pd.notna(row.get('Size')):
        base_parts.append(str(row['Size']).strip().upper())
      # Create key with Customer_PO
    primary_key = None
    if is_valid_po_value(row.get('Customer_PO')):
        primary_parts = base_parts + [str(row['Customer_PO']).strip().upper()]
        primary_key = '|'.join(primary_parts) if primary_parts else None
    
    # Create key with Customer_Alt_PO  
    alt_key = None
    if is_valid_po_value(row.get('Customer_Alt_PO')):
        alt_parts = base_parts + [str(row['Customer_Alt_PO']).strip().upper()]
        alt_key = '|'.join(alt_parts) if alt_parts else None
    
    return primary_key, alt_key

def add_match_keys(df):
    """
    Add 'exact_key' and 'fuzzy_key' columns to the dataframe.
    Performance-optimized version with configuration pre-loading.
    """
    df = df.copy()
    
    # Pre-load customer configurations to prevent per-row YAML loading
    preload_customer_configs(df)
    
    # Generate match keys - now using cached configurations
    df['exact_key'] = df.apply(
        lambda row: create_matching_key(row, include_size=True, canonical_customer=row.get('Canonical_Customer')), 
        axis=1
    )
    df['fuzzy_key'] = df.apply(
        lambda row: create_matching_key(row, include_size=False, canonical_customer=row.get('Canonical_Customer')), 
        axis=1
    )
    return df

def weighted_fuzzy_score(row1, row2, weights=None, canonical_customer=None):
    """
    Calculate a weighted fuzzy match score between two records.
    Updated to support customer-specific style field configurations.
    """
    if weights is None:
        weights = DEFAULT_FUZZY_WEIGHTS
    scores = {}
    
    # PO Score - only use valid PO values for comparison
    po1 = ''
    if is_valid_po_value(row1.get('Customer_PO')):
        po1 = str(row1['Customer_PO']).strip()
    elif is_valid_po_value(row1.get('Customer_Alt_PO')):
        po1 = str(row1['Customer_Alt_PO']).strip()
    
    po2_primary = str(row2.get('Customer_PO', '')).strip() if is_valid_po_value(row2.get('Customer_PO')) else ''
    po2_alt = str(row2.get('Customer_Alt_PO', '')).strip() if is_valid_po_value(row2.get('Customer_Alt_PO')) else ''
    
    # Only calculate score if we have valid PO values to compare
    if po1 and (po2_primary or po2_alt):
        po_scores = []
        if po2_primary:
            po_scores.append(fuzz.token_sort_ratio(po1, po2_primary))
        if po2_alt:
            po_scores.append(fuzz.token_sort_ratio(po1, po2_alt))
        scores['po'] = max(po_scores) if po_scores else 0
    else:
        scores['po'] = 0

    # Style Score - use customer-aware style logic
    customer = canonical_customer or row1.get('Canonical_Customer') or row2.get('Canonical_Customer')
    
    # Get style values using customer-specific logic
    style1_value, style1_source = get_style_value_and_source(row1, customer)
    style2_value, style2_source = get_style_value_and_source(row2, customer)
    
    if style1_value and style2_value:
        scores['style'] = fuzz.token_sort_ratio(str(style1_value), str(style2_value))
    elif style1_value or style2_value:
        # If only one has a style value, try comparing against all available style fields
        # This handles cases where different records use different style field priorities
        style_scores = []
        
        # Row1 style comparisons
        if style1_value:
            for field in ['Style', 'Pattern_ID', 'ALIAS/RELATED ITEM']:
                if pd.notna(row2.get(field)):
                    style_scores.append(fuzz.token_sort_ratio(str(style1_value), str(row2[field])))
        
        # Row2 style comparisons
        if style2_value:
            for field in ['Style', 'Pattern_ID', 'ALIAS/RELATED ITEM']:
                if pd.notna(row1.get(field)):
                    style_scores.append(fuzz.token_sort_ratio(str(style2_value), str(row1[field])))
        
        scores['style'] = max(style_scores) if style_scores else 0
    else:
        scores['style'] = 0

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
    
    # Handle None values in groupby for both dataframes    # Process packed data - only use columns that exist
    packed_for_agg = packed_df.copy()
    packed_agg_cols = [col for col in agg_cols if col in packed_for_agg.columns]
    for col in packed_agg_cols:
        packed_for_agg[col] = packed_for_agg[col].fillna(TEMP_NONE_REPLACEMENT)
    packed_agg = packed_for_agg.groupby(packed_agg_cols, as_index=False, dropna=False)['Qty'].sum().rename(columns={'Qty': 'Packed_Qty'})
    
    # Process shipped data - only use columns that exist
    shipped_for_agg = shipped_df.copy()
    shipped_agg_cols = [col for col in agg_cols if col in shipped_for_agg.columns]
    for col in shipped_agg_cols:
        shipped_for_agg[col] = shipped_for_agg[col].fillna(TEMP_NONE_REPLACEMENT)
    shipped_agg = shipped_for_agg.groupby(shipped_agg_cols, as_index=False, dropna=False)['Qty'].sum().rename(columns={'Qty': 'Shipped_Qty'})
    
    # Use common columns for merging
    common_agg_cols = [col for col in agg_cols if col in packed_for_agg.columns and col in shipped_for_agg.columns]
    
    # Merge the results
    combined = pd.merge(
        packed_agg, shipped_agg, how='outer', on=common_agg_cols
    ).fillna(0)
    
    # Restore None values
    for col in common_agg_cols:
        if col in combined.columns:
            combined[col] = combined[col].replace(TEMP_NONE_REPLACEMENT, None)
    
    combined['Source_Type'] = combined.apply(
        lambda r: ','.join([t for t, q in [('PACKED', r.Packed_Qty), ('SHIPPED', r.Shipped_Qty)] if q > 0]), axis=1
    )
    return combined

def exact_match(combined_df, orders_df):
    """
    Optimized exact matching with cross-field PO support.
    Uses vectorized operations and indexed lookups for better performance.
    """
    logging.info("Performing exact match...")
    
    # Check if combined_df already has match keys, if not add them
    if 'exact_key' not in combined_df.columns:
        combined_with_keys = add_match_keys(combined_df)
    else:
        combined_with_keys = combined_df.copy()
    
    # Orders always need keys added since they come fresh
    orders_with_keys = add_match_keys(orders_df)

    # First, try standard exact match (fastest path)
    merged = pd.merge(
        combined_with_keys, orders_with_keys,
        left_on='exact_key', right_on='exact_key',
        suffixes=('', '_order'),
        how='left', indicator=True
    )

    # Mark initial exact matches
    merged['Match_Type'] = np.where(merged['_merge'] == 'both', 'EXACT', 'NO_MATCH')
    merged['Match_Score'] = np.where(merged['Match_Type'] == 'EXACT', 100, 0)
    merged['Ordered_Qty'] = merged['Ordered_Qty'].fillna(0)
    merged['Best_Match_Field'] = None
    
    # For records that didn't match, try optimized cross-field matching
    unmatched_mask = merged['Match_Type'] == 'NO_MATCH'
    if unmatched_mask.sum() > 0:
        logging.info(f"Attempting optimized cross-field exact matching for {unmatched_mask.sum()} unmatched records")
        
        # Create lookup dictionaries for faster cross-field matching
        order_lookup = {}
        for _, order_row in orders_with_keys.iterrows():
            customer = order_row['Canonical_Customer']
            if customer not in order_lookup:
                order_lookup[customer] = []
            
            # Create both primary and alt keys for this order
            primary_key, alt_key = create_alternate_matching_keys(order_row, include_size=True)
            order_lookup[customer].append({
                'primary_key': primary_key,
                'alt_key': alt_key,
                'row': order_row
            })
        
        # Process unmatched records efficiently
        unmatched_indices = merged[unmatched_mask].index
        for idx in unmatched_indices:
            combined_row = merged.loc[idx]
            customer = combined_row['Canonical_Customer']
            
            if customer not in order_lookup:
                continue
                
            # Get alternate keys for the combined row
            comb_primary_key, comb_alt_key = create_alternate_matching_keys(combined_row, include_size=True)
            
            # Try to find matches using lookup dictionary
            match_found = False
            best_match = None
            match_field = None
            
            for order_info in order_lookup[customer]:
                order_primary_key = order_info['primary_key']
                order_alt_key = order_info['alt_key']
                
                # Check cross-field combinations (prioritize PO matches)
                if comb_primary_key and order_primary_key and comb_primary_key == order_primary_key:
                    match_found = True
                    best_match = order_info['row']
                    match_field = 'PO'
                    break
                elif comb_primary_key and order_alt_key and comb_primary_key == order_alt_key:
                    match_found = True
                    best_match = order_info['row']
                    match_field = 'PO'
                    break
                elif comb_alt_key and order_primary_key and comb_alt_key == order_primary_key:
                    match_found = True
                    best_match = order_info['row']
                    match_field = 'Alt_PO'
                    break
                elif comb_alt_key and order_alt_key and comb_alt_key == order_alt_key:
                    match_found = True
                    best_match = order_info['row']
                    match_field = 'Alt_PO'
                    break
            
            if match_found:
                # Update the merged row with match information
                merged.loc[idx, 'Match_Type'] = 'EXACT'
                merged.loc[idx, 'Match_Score'] = 100
                merged.loc[idx, 'Best_Match_Field'] = match_field
                merged.loc[idx, 'Customer_PO_order'] = best_match['Customer_PO']
                merged.loc[idx, 'Customer_Alt_PO_order'] = best_match['Customer_Alt_PO'] 
                merged.loc[idx, 'Style_order'] = best_match['Style']
                merged.loc[idx, 'Pattern_ID_order'] = best_match['Pattern_ID']
                merged.loc[idx, 'Color_order'] = best_match['Color']
                merged.loc[idx, 'Size_order'] = best_match['Size']
                merged.loc[idx, 'Ordered_Qty'] = best_match['Ordered_Qty']

    merged['Match_Count'] = merged.groupby('exact_key')['exact_key'].transform('count')
    
    # Set best match fields from orders
    merged['Best_Match_PO'] = merged['Customer_PO_order']
    merged['Best_Match_Alt_PO'] = merged['Customer_Alt_PO_order']
    merged['Best_Match_Style'] = merged['Style_order']
    merged['Best_Match_Pattern_ID'] = merged['Pattern_ID_order']
    merged['Best_Match_Color'] = merged['Color_order']
    merged['Best_Match_Size'] = merged['Size_order']
    
    # Vectorized determination of match fields and scores for standard matches
    exact_matches_mask = merged['Match_Type'] == 'EXACT'
    
    # Initialize score columns
    merged['PO_Match_Score'] = 0
    merged['Alt_PO_Match_Score'] = 0
    
    # For cross-field matches, scores are already determined by Best_Match_Field
    cross_field_mask = exact_matches_mask & pd.notna(merged['Best_Match_Field'])
    merged.loc[cross_field_mask & (merged['Best_Match_Field'] == 'PO'), 'PO_Match_Score'] = 100
    merged.loc[cross_field_mask & (merged['Best_Match_Field'] == 'Alt_PO'), 'Alt_PO_Match_Score'] = 100
    
    # For standard exact matches, determine which PO field matched
    standard_exact_mask = exact_matches_mask & pd.isna(merged['Best_Match_Field'])
    if standard_exact_mask.sum() > 0:        # Check PO matches - use is_valid_po_value instead of just pd.notna
        po_match_mask = (
            merged['Customer_PO'].apply(lambda x: is_valid_po_value(x)) & 
            merged['Customer_PO_order'].apply(lambda x: is_valid_po_value(x)) &
            (merged['Customer_PO'].str.strip().str.upper() == merged['Customer_PO_order'].str.strip().str.upper())
        )
        
        # Check Alt_PO matches - use is_valid_po_value instead of just pd.notna
        alt_po_match_mask = (
            merged['Customer_Alt_PO'].apply(lambda x: is_valid_po_value(x)) & 
            merged['Customer_Alt_PO_order'].apply(lambda x: is_valid_po_value(x)) &
            (merged['Customer_Alt_PO'].str.strip().str.upper() == merged['Customer_Alt_PO_order'].str.strip().str.upper())
        )
        
        # Set scores and best match field (prefer PO over Alt_PO)
        merged.loc[standard_exact_mask & po_match_mask, 'PO_Match_Score'] = 100
        merged.loc[standard_exact_mask & po_match_mask, 'Best_Match_Field'] = 'PO'
        
        merged.loc[standard_exact_mask & alt_po_match_mask, 'Alt_PO_Match_Score'] = 100
        merged.loc[standard_exact_mask & alt_po_match_mask & pd.isna(merged['Best_Match_Field']), 'Best_Match_Field'] = 'Alt_PO'

    keep_cols = list(combined_with_keys.columns) + [
        'Ordered_Qty', 'Match_Type', 'Match_Score', 'Match_Count',
        'Best_Match_PO', 'Best_Match_Alt_PO', 'Best_Match_Style',
        'Best_Match_Pattern_ID', 'Best_Match_Color', 'Best_Match_Size',
        'Best_Match_Field', 'PO_Match_Score', 'Alt_PO_Match_Score'
    ]
    results = merged[keep_cols].copy()
    unmatched = results[results['Match_Type'] != 'EXACT'].copy()
    return results, unmatched, orders_with_keys

def fuzzy_match(unmatched_df, orders_with_keys, threshold=75):
    """
    Optimized fuzzy match with cross-field PO support.
    Uses efficient similarity calculation while maintaining enhanced functionality.
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
        orders_rows = customer_orders.reset_index(drop=True)        # Prepare data for efficient cross-field matching - only use valid PO values
        unmatched_po = [str(val).strip() if is_valid_po_value(val) else '' for val in unmatched_rows['Customer_PO']]
        unmatched_alt_po = [str(val).strip() if is_valid_po_value(val) else '' for val in unmatched_rows['Customer_Alt_PO']]
        orders_po = [str(val).strip() if is_valid_po_value(val) else '' for val in orders_rows['Customer_PO']]
        orders_alt_po = [str(val).strip() if is_valid_po_value(val) else '' for val in orders_rows['Customer_Alt_PO']]

        # Create combined PO lists for more efficient cross-field matching
        # Each unmatched record gets compared against all order PO fields
        unmatched_po_combined = unmatched_po + unmatched_alt_po
        orders_po_combined = orders_po + orders_alt_po
          # Single similarity calculation covering all cross-field combinations
        combined_sim = process.cdist(unmatched_po_combined, orders_po_combined, 
                                   scorer=fuzz.token_sort_ratio, dtype=np.uint8)
        
        n_unmatched = len(unmatched_rows)
        n_orders = len(orders_rows)
        
        for i in range(n_unmatched):
            # Extract similarity scores for this unmatched record
            # Unmatched PO vs all order PO fields
            po_vs_all = combined_sim[i, :n_orders * 2]
            # Unmatched Alt_PO vs all order PO fields  
            alt_po_vs_all = combined_sim[i + n_unmatched, :n_orders * 2]
            
            # Only consider scores where we have valid PO values on both sides
            # Check if unmatched record has valid PO values
            unmatched_has_valid_po = unmatched_po[i] != ''
            unmatched_has_valid_alt_po = unmatched_alt_po[i] != ''
            
            # Find best matches for each field, but only if we have valid values to compare
            po_best_score = 0
            alt_po_best_score = 0
            po_best_idx = 0
            alt_po_best_idx = 0
            
            if unmatched_has_valid_po:
                # Filter out scores where order PO fields are empty
                valid_po_mask = np.array([orders_po_combined[j] != '' for j in range(len(orders_po_combined))])[:n_orders * 2]
                if valid_po_mask.any():
                    valid_scores = po_vs_all.copy()
                    valid_scores[~valid_po_mask] = 0
                    po_best_idx = valid_scores.argmax()
                    po_best_score = valid_scores[po_best_idx]
            
            if unmatched_has_valid_alt_po:
                # Filter out scores where order PO fields are empty
                valid_po_mask = np.array([orders_po_combined[j] != '' for j in range(len(orders_po_combined))])[:n_orders * 2]
                if valid_po_mask.any():
                    valid_scores = alt_po_vs_all.copy()
                    valid_scores[~valid_po_mask] = 0
                    alt_po_best_idx = valid_scores.argmax()
                    alt_po_best_score = valid_scores[alt_po_best_idx]
            
            # Determine which field had the better match
            if po_best_score >= alt_po_best_score and po_best_score > 0:
                best_score = po_best_score
                best_field = 'PO'
                # Convert combined index back to order index
                order_idx = po_best_idx // 2
            elif alt_po_best_score > 0:
                best_score = alt_po_best_score
                best_field = 'Alt_PO'
                # Convert combined index back to order index
                order_idx = alt_po_best_idx // 2
            else:
                best_score = 0
                best_field = None
                order_idx = 0

            best_candidate = orders_rows.iloc[order_idx] if best_score >= threshold else None
            unmatched_row_dict = unmatched_rows.iloc[i].to_dict()
            
            if best_candidate is not None:
                result = unmatched_row_dict.copy()
                result.update({
                    'Match_Type': 'FUZZY',
                    'Match_Score': best_score,
                    'PO_Match_Score': po_best_score,
                    'Alt_PO_Match_Score': alt_po_best_score,
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
                    'Match_Score': best_score,
                    'PO_Match_Score': po_best_score,
                    'Alt_PO_Match_Score': alt_po_best_score,
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
    """    # Group by PO, Style, Color (and Alt_PO if that's the matched field)
    group_keys = ['Best_Match_Field', 'Best_Match_PO', 'Best_Match_Alt_PO', 'Style', 'Color']    # Use Best_Match_PO or Best_Match_Alt_PO depending on Best_Match_Field
    df['Group_PO'] = np.where(df['Best_Match_Field'] == 'Alt_PO', df['Best_Match_Alt_PO'], df['Best_Match_PO'])
      # Only include Style_Source in grouping if it exists
    group_cols = ['Group_PO', 'Style', 'Color']
    if 'Style_Source' in df.columns:
        group_cols.append('Style_Source')

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
    
    # Ensure consistent data types for merge columns
    for col in group_cols:
        if col in df.columns and col in grouped.columns:
            df[col] = df[col].astype(str)
            grouped[col] = grouped[col].astype(str)
    
    # Merge back to original df on PO, Style, Color
    df = df.merge(
        grouped[group_cols + ['Qty_Variance', 'Qty_Variance_Pct', 'Data_Quality_Flag']],
        left_on=group_cols,
        right_on=group_cols,
        how='left',
        suffixes=('', '_group')
    )
    return df

def calculate_field_match_statistics(customer_df):
    """
    Calculate detailed field-level matching statistics for a customer.
    Vectorized implementation for better performance.
    """
    total_records = len(customer_df)
    if total_records == 0:
        return {}
    
    # Count exact field matches (only for matched records)
    matched_records = customer_df[customer_df['Match_Type'].isin(['EXACT', 'FUZZY'])]
    
    if len(matched_records) == 0:
        return {
            'Style_Exact_Matches': 0,
            'Color_Exact_Matches': 0,
            'Size_Exact_Matches': 0,
            'PO_Exact_Matches': 0,
            'Style_Match_Pct': 0.0,
            'Color_Match_Pct': 0.0,
            'Size_Match_Pct': 0.0,
            'PO_Match_Pct': 0.0
        }
    
    # Vectorized style matching (check both Style and Pattern_ID)
    # Normalize strings for comparison
    source_style = matched_records['Style'].fillna('').astype(str).str.strip().str.upper()
    source_pattern = matched_records['Pattern_ID'].fillna('').astype(str).str.strip().str.upper()
    match_style = matched_records['Best_Match_Style'].fillna('').astype(str).str.strip().str.upper()
    match_pattern = matched_records['Best_Match_Pattern_ID'].fillna('').astype(str).str.strip().str.upper()
    
    # Style matches if any of these conditions are true:
    # 1. source_style == match_style (and both non-empty)
    # 2. source_pattern == match_pattern (and both non-empty)  
    # 3. source_style == match_pattern (and both non-empty)
    # 4. source_pattern == match_style (and both non-empty)
    style_matches = (
        (source_style.ne('') & match_style.ne('') & source_style.eq(match_style)) |
        (source_pattern.ne('') & match_pattern.ne('') & source_pattern.eq(match_pattern)) |
        (source_style.ne('') & match_pattern.ne('') & source_style.eq(match_pattern)) |
        (source_pattern.ne('') & match_style.ne('') & source_pattern.eq(match_style))
    )
    style_exact_matches = style_matches.sum()
    
    # Vectorized color matching
    source_color = matched_records['Color'].fillna('').astype(str).str.strip().str.upper()
    match_color = matched_records['Best_Match_Color'].fillna('').astype(str).str.strip().str.upper()
    color_matches = source_color.ne('') & match_color.ne('') & source_color.eq(match_color)
    color_exact_matches = color_matches.sum()
    
    # Vectorized size matching
    source_size = matched_records['Size'].fillna('').astype(str).str.strip().str.upper()
    match_size = matched_records['Best_Match_Size'].fillna('').astype(str).str.strip().str.upper()
    size_matches = source_size.ne('') & match_size.ne('') & source_size.eq(match_size)
    size_exact_matches = size_matches.sum()
    
    # Vectorized PO matching (either Customer_PO or Customer_Alt_PO)
    source_po = matched_records['Customer_PO'].fillna('').astype(str).str.strip().str.upper()
    source_alt_po = matched_records['Customer_Alt_PO'].fillna('').astype(str).str.strip().str.upper()
    match_po = matched_records['Best_Match_PO'].fillna('').astype(str).str.strip().str.upper()
    match_alt_po = matched_records['Best_Match_Alt_PO'].fillna('').astype(str).str.strip().str.upper()
    
    # PO matches if:
    # 1. source_po matches either match_po or match_alt_po (and source_po is non-empty)
    # 2. source_alt_po matches either match_po or match_alt_po (and source_alt_po is non-empty)
    po_matches = (
        (source_po.ne('') & ((source_po.eq(match_po)) | (source_po.eq(match_alt_po)))) |
        (source_alt_po.ne('') & ((source_alt_po.eq(match_po)) | (source_alt_po.eq(match_alt_po))))
    )
    po_exact_matches = po_matches.sum()
    
    return {
        'Style_Exact_Matches': int(style_exact_matches),
        'Color_Exact_Matches': int(color_exact_matches),
        'Size_Exact_Matches': int(size_exact_matches),
        'PO_Exact_Matches': int(po_exact_matches),
        'Style_Match_Pct': round((style_exact_matches / total_records) * 100, 2),
        'Color_Match_Pct': round((color_exact_matches / total_records) * 100, 2),
        'Size_Match_Pct': round((size_exact_matches / total_records) * 100, 2),
        'PO_Match_Pct': round((po_exact_matches / total_records) * 100, 2)
    }

def calculate_advanced_insights(customer_df):
    """
    Calculate additional insights for better diagnostics and analysis.
    """
    total_records = len(customer_df)
    if total_records == 0:
        return {}
    
    # Match type distribution
    exact_matches = (customer_df['Match_Type'] == 'EXACT').sum()
    fuzzy_matches = (customer_df['Match_Type'] == 'FUZZY').sum()
    no_matches = (customer_df['Match_Type'] == 'NO_MATCH').sum()
    
    # Quality distribution
    good_quality = (customer_df['Data_Quality_Flag'] == 'GOOD').sum()
    acceptable_quality = (customer_df['Data_Quality_Flag'] == 'ACCEPTABLE').sum()
    questionable_quality = (customer_df['Data_Quality_Flag'] == 'QUESTIONABLE').sum()
    poor_quality = (customer_df['Data_Quality_Flag'] == 'POOR').sum()
    
    # PO field utilization (which PO field is being used for matches)
    primary_po_matches = (customer_df['Best_Match_Field'] == 'PO').sum()
    alt_po_matches = (customer_df['Best_Match_Field'] == 'Alt_PO').sum()
    
    # Quantity analysis
    total_packed = customer_df['Packed_Qty'].sum()
    total_shipped = customer_df['Shipped_Qty'].sum()
    total_ordered = customer_df['Ordered_Qty'].sum()
    
    # Match score analysis (for fuzzy matches)
    fuzzy_records = customer_df[customer_df['Match_Type'] == 'FUZZY']
    avg_fuzzy_score = fuzzy_records['Match_Score'].mean() if len(fuzzy_records) > 0 else 0
    
    # Common issues identification
    missing_orders = (customer_df['Ordered_Qty'] == 0).sum()
    over_shipped = (customer_df['Shipped_Qty'] > customer_df['Ordered_Qty']).sum()
    under_shipped = (
        (customer_df['Ordered_Qty'] > 0) & 
        (customer_df['Shipped_Qty'] < customer_df['Ordered_Qty'])
    ).sum()
    
    return {
        'Fuzzy_Matches': fuzzy_matches,
        'No_Matches': no_matches,
        'Fuzzy_Match_Pct': round((fuzzy_matches / total_records) * 100, 2),
        'No_Match_Pct': round((no_matches / total_records) * 100, 2),
        'Good_Quality_Records': good_quality,
        'Acceptable_Quality': acceptable_quality,
        'Questionable_Quality': questionable_quality,
        'Poor_Quality': poor_quality,
        'Good_Quality_Pct': round((good_quality / total_records) * 100, 2),
        'Primary_PO_Matches': primary_po_matches,
        'Alt_PO_Matches': alt_po_matches,
        'Primary_PO_Match_Pct': round((primary_po_matches / total_records) * 100, 2),
        'Alt_PO_Match_Pct': round((alt_po_matches / total_records) * 100, 2),
        'Total_Packed_Qty': int(total_packed),
        'Total_Shipped_Qty': int(total_shipped),
        'Total_Ordered_Qty': int(total_ordered),
        'Avg_Fuzzy_Match_Score': round(avg_fuzzy_score, 2),
        'Missing_Orders_Count': missing_orders,
        'Over_Shipped_Count': over_shipped,
        'Under_Shipped_Count': under_shipped,
        'Missing_Orders_Pct': round((missing_orders / total_records) * 100, 2),
        'Over_Shipped_Pct': round((over_shipped / total_records) * 100, 2),
        'Under_Shipped_Pct': round((under_shipped / total_records) * 100, 2)
    }

def summarize(results_df):
    """
    Build enhanced summary stats by Canonical_Customer with detailed matching insights.
    """
    summary_list = []
    
    for customer in results_df['Canonical_Customer'].dropna().unique():
        customer_df = results_df[results_df['Canonical_Customer'] == customer]
        total_records = len(customer_df)
        exact_matches = (customer_df['Match_Type'] == 'EXACT').sum()
        
        # Base statistics
        base_stats = {
            'Canonical_Customer': customer,
            'Total_Records': total_records,
            'Exact_Matches': exact_matches,
            'Exact_Match_Rate': round((exact_matches / total_records) * 100, 2),
        }
        
        # Add field-level matching statistics
        field_stats = calculate_field_match_statistics(customer_df)
        
        # Add advanced insights
        advanced_stats = calculate_advanced_insights(customer_df)
        
        # Combine all statistics
        customer_summary = {**base_stats, **field_stats, **advanced_stats}
        summary_list.append(customer_summary)
    
    summary_stats = pd.DataFrame(summary_list)
    
    # Sort by total records descending to show largest customers first
    summary_stats = summary_stats.sort_values('Total_Records', ascending=False)
    
    return summary_stats

def match_records(packed_std, shipped_std, orders_std, threshold=75):
    """
    Orchestrates the matching pipeline: aggregation, exact, then fuzzy, then merge.
    Returns: (results DataFrame, summary DataFrame)
    """
    # Helper function to determine style source - defined early for reuse
    def determine_style_source(row):
        customer = row.get('Canonical_Customer')
        # Use the same logic as get_style_value_and_source, but based on the actual value used for matching
        if customer:
            try:
                config = get_customer_config_cached(customer)
                if config['style_match_strategy'] == 'alias_related_item':
                    if pd.notna(row.get('Style')) and str(row.get('Style', '')).strip():
                        return 'Style'
                    elif pd.notna(row.get('Pattern_ID')) and str(row.get('Pattern_ID', '')).strip():
                        return 'Pattern_ID'
                    elif pd.notna(row.get('ALIAS/RELATED ITEM')) and str(row.get('ALIAS/RELATED ITEM', '')).strip():
                        return 'ALIAS/RELATED ITEM'
                else:
                    if pd.notna(row.get('Style')) and str(row.get('Style', '')).strip():
                        return 'Style'
                    elif pd.notna(row.get('Pattern_ID')) and str(row.get('Pattern_ID', '')).strip():
                        return 'Pattern_ID'
            except Exception:
                # Fallback to standard logic if config fails
                pass
        return None
    
    logging.info(f"Starting match_records with {len(packed_std)} packed, {len(shipped_std)} shipped, {len(orders_std)} orders")
    
    # Debug: Check Customer_Alt_PO presence in input data
    packed_alt_po_count = packed_std['Customer_Alt_PO'].notna().sum()
    shipped_alt_po_count = shipped_std['Customer_Alt_PO'].notna().sum()
    orders_alt_po_count = orders_std['Customer_Alt_PO'].notna().sum()
    logging.info(f"Input data Alt_PO counts - Packed: {packed_alt_po_count}, Shipped: {shipped_alt_po_count}, Orders: {orders_alt_po_count}")
    
    logging.info("Aggregating packed and shipped quantities...")
    combined_df = aggregate_quantities(packed_std, shipped_std)
    logging.info(f"Combined dataset size: {len(combined_df)} records")
      # Debug: Check Customer_Alt_PO preservation after aggregation
    combined_alt_po_count = combined_df['Customer_Alt_PO'].notna().sum()
    logging.info(f"Combined data Alt_PO count after aggregation: {combined_alt_po_count}")
    
    logging.info("Running exact matching pipeline...")
    exact_results, unmatched, orders_with_keys = exact_match(combined_df, orders_std)
    exact_matches = len(exact_results) - len(unmatched)
    logging.info(f"Exact matching complete: {exact_matches} exact matches, {len(unmatched)} unmatched records")
    
    # Debug: Check for duplicate joins by counting records vs unique exact_keys
    if len(exact_results) > 0:
        unique_keys = exact_results['exact_key'].nunique()
        total_records = len(exact_results)
        if total_records > unique_keys:
            duplicate_ratio = (total_records - unique_keys) / total_records * 100
            logging.warning(f"Potential duplicate joins detected: {total_records} records from {unique_keys} unique keys ({duplicate_ratio:.1f}% inflation)")
        else:
            logging.info(f"No duplicate joins detected: {total_records} records from {unique_keys} unique keys")
      # Debug: Check match field distribution in exact results
    if 'Best_Match_Field' in exact_results.columns:
        exact_field_counts = exact_results['Best_Match_Field'].value_counts()
        logging.info(f"Exact match field distribution: {exact_field_counts.to_dict()}")

    if not unmatched.empty:
        logging.info("Running fuzzy matching on unmatched records...")
        fuzzy_results = fuzzy_match(unmatched, orders_with_keys, threshold)
        # Debug: Check match field distribution in fuzzy results
        if 'Best_Match_Field' in fuzzy_results.columns:
            fuzzy_field_counts = fuzzy_results['Best_Match_Field'].value_counts()
            logging.info(f"Fuzzy match field distribution: {fuzzy_field_counts.to_dict()}")
        # Combine exact and fuzzy results
        exact_matched = exact_results[exact_results['Match_Type'] == 'EXACT']
        results_df = pd.concat([exact_matched, fuzzy_results], ignore_index=True)
        logging.info(f"Combined results: {len(exact_matched)} exact + {len(fuzzy_results)} fuzzy = {len(results_df)} total")
    else:
        results_df = exact_results
        logging.info("No unmatched records - using exact results only")

    # Add Style_Source after results_df is created
    if not results_df.empty:
        results_df['Style_Source'] = results_df.apply(determine_style_source, axis=1)
    else:
        results_df = results_df.copy()  # Ensure we have a DataFrame
        results_df['Style_Source'] = []

    # Debug: Check Customer_Alt_PO preservation in final results
    final_alt_po_count = results_df['Customer_Alt_PO'].notna().sum()
    logging.info(f"Final results Alt_PO count: {final_alt_po_count}")
    
    # Debug: Check PO score distributions
    if 'PO_Match_Score' in results_df.columns and 'Alt_PO_Match_Score' in results_df.columns:
        po_scores = results_df['PO_Match_Score'].describe()
        alt_po_scores = results_df['Alt_PO_Match_Score'].describe()
        logging.info(f"PO match score stats: mean={po_scores['mean']:.1f}, max={po_scores['max']}")
        logging.info(f"Alt_PO match score stats: mean={alt_po_scores['mean']:.1f}, max={alt_po_scores['max']}")

    logging.info("Adding data quality metrics and flags...")
    results_df = compute_data_quality_flags(results_df)
    summary_stats = summarize(results_df)
    
    logging.info(f"Match_records completed. Final dataset: {len(results_df)} records")
    return results_df, summary_stats

def create_optimized_summary(results_df):
    """
    Create optimized summary with reduced columns and better naming.
    """
    summary_list = []
    
    for customer in results_df['Canonical_Customer'].dropna().unique():
        customer_df = results_df[results_df['Canonical_Customer'] == customer]
        total_records = len(customer_df)
        
        if total_records == 0:
            continue
            
        # Match type counts
        exact_matches = (customer_df['Match_Type'] == 'EXACT').sum()
        fuzzy_matches = (customer_df['Match_Type'] == 'FUZZY').sum()
        no_matches = (customer_df['Match_Type'] == 'NO_MATCH').sum()
        
        # Quality counts
        good_quality = (customer_df['Data_Quality_Flag'] == 'GOOD').sum()
        
        # Field-level matching (for matched records only)
        matched_records = customer_df[customer_df['Match_Type'].isin(['EXACT', 'FUZZY'])]
        
        # Calculate field matches
        style_matches = 0
        color_matches = 0
        size_matches = 0
        po_matches = 0
        
        for _, row in matched_records.iterrows():
            # Style match
            source_style = str(row.get('Style', '')).strip().upper()
            source_pattern = str(row.get('Pattern_ID', '')).strip().upper()
            match_style = str(row.get('Best_Match_Style', '')).strip().upper()
            match_pattern = str(row.get('Best_Match_Pattern_ID', '')).strip().upper()
            
            if (source_style and match_style and source_style == match_style) or \
               (source_pattern and match_pattern and source_pattern == match_pattern) or \
               (source_style and match_pattern and source_style == match_pattern) or \
               (source_pattern and match_style and source_pattern == match_style):
                style_matches += 1
            
            # Color match
            source_color = str(row.get('Color', '')).strip().upper()
            match_color = str(row.get('Best_Match_Color', '')).strip().upper()
            if source_color and match_color and source_color == match_color:
                color_matches += 1
            
            # Size match
            source_size = str(row.get('Size', '')).strip().upper()
            match_size = str(row.get('Best_Match_Size', '')).strip().upper()
            if source_size and match_size and source_size == match_size:
                size_matches += 1
            
            # PO match
            source_po = str(row.get('Customer_PO', '')).strip().upper()
            source_alt_po = str(row.get('Customer_Alt_PO', '')).strip().upper()
            match_po = str(row.get('Best_Match_PO', '')).strip().upper()
            match_alt_po = str(row.get('Best_Match_Alt_PO', '')).strip().upper()
            
            if (source_po and (source_po == match_po or source_po == match_alt_po)) or \
               (source_alt_po and (source_alt_po == match_po or source_alt_po == match_alt_po)):
                po_matches += 1
        
        # PO field usage
        primary_po_matches = (customer_df['Best_Match_Field'] == 'PO').sum()
        alt_po_matches = (customer_df['Best_Match_Field'] == 'Alt_PO').sum()
        
        # Quantities
        total_packed = customer_df['Packed_Qty'].sum()
        total_shipped = customer_df['Shipped_Qty'].sum()
        total_ordered = customer_df['Ordered_Qty'].sum()
        
        # Issues
        over_shipped = (customer_df['Shipped_Qty'] > customer_df['Ordered_Qty']).sum()
        under_shipped = ((customer_df['Ordered_Qty'] > 0) & 
                        (customer_df['Shipped_Qty'] < customer_df['Ordered_Qty'])).sum()
        missing_orders = (customer_df['Ordered_Qty'] == 0).sum()
        
        # Fuzzy score average
        fuzzy_records = customer_df[customer_df['Match_Type'] == 'FUZZY']
        avg_fuzzy_score = fuzzy_records['Match_Score'].mean() if len(fuzzy_records) > 0 else 0
        
        # Build optimized summary
        summary = {
            'Customer': customer,
            'Records': total_records,
            'Exact_#': exact_matches,
            'Exact_%': round((exact_matches / total_records) * 100, 1),
            'Fuzzy_#': fuzzy_matches,
            'Fuzzy_%': round((fuzzy_matches / total_records) * 100, 1),
            'NoMatch_#': no_matches,
            'NoMatch_%': round((no_matches / total_records) * 100, 1),
            'Style_%': round((style_matches / total_records) * 100, 1),
            'Color_%': round((color_matches / total_records) * 100, 1),
            'Size_%': round((size_matches / total_records) * 100, 1),
            'PO_%': round((po_matches / total_records) * 100, 1),
            'PO_Primary_%': round((primary_po_matches / total_records) * 100, 1),
            'PO_Alt_%': round((alt_po_matches / total_records) * 100, 1),
            'Packed_Qty': int(total_packed),
            'Shipped_Qty': int(total_shipped),
            'Ordered_Qty': int(total_ordered),
            'Over_Ship_%': round((over_shipped / total_records) * 100, 1),
            'Under_Ship_%': round((under_shipped / total_records) * 100, 1),
            'Missing_Ord_%': round((missing_orders / total_records) * 100, 1),
            'Quality_Good_%': round((good_quality / total_records) * 100, 1),
            'Fuzzy_Avg_Score': round(avg_fuzzy_score, 1)
        }
        summary_list.append(summary)
    
    summary_df = pd.DataFrame(summary_list)
    return summary_df.sort_values('Records', ascending=False)

def create_customer_match_analysis(customer_df):
    """
    Create detailed match analysis for a customer.
    """
    analysis_data = []
    
    for match_type in ['EXACT', 'FUZZY', 'NO_MATCH']:
        type_df = customer_df[customer_df['Match_Type'] == match_type]
        if len(type_df) == 0:
            continue
            
        # Calculate field matches for this match type
        style_matches = 0
        color_matches = 0
        size_matches = 0
        po_matches = 0
        
        for _, row in type_df.iterrows():
            # Style match
            source_style = str(row.get('Style', '')).strip().upper()
            source_pattern = str(row.get('Pattern_ID', '')).strip().upper()
            match_style = str(row.get('Best_Match_Style', '')).strip().upper()
            match_pattern = str(row.get('Best_Match_Pattern_ID', '')).strip().upper()
            
            if (source_style and match_style and source_style == match_style) or \
               (source_pattern and match_pattern and source_pattern == match_pattern):
                style_matches += 1
            
            # Similar logic for color, size, PO...
            source_color = str(row.get('Color', '')).strip().upper()
            match_color = str(row.get('Best_Match_Color', '')).strip().upper()
            if source_color and match_color and source_color == match_color:
                color_matches += 1
            
            source_size = str(row.get('Size', '')).strip().upper()
            match_size = str(row.get('Best_Match_Size', '')).strip().upper()
            if source_size and match_size and source_size == match_size:
                size_matches += 1
            
            source_po = str(row.get('Customer_PO', '')).strip().upper()
            source_alt_po = str(row.get('Customer_Alt_PO', '')).strip().upper()
            match_po = str(row.get('Best_Match_PO', '')).strip().upper()
            match_alt_po = str(row.get('Best_Match_Alt_PO', '')).strip().upper()
            
            if (source_po and (source_po == match_po or source_po == match_alt_po)) or \
               (source_alt_po and (source_alt_po == match_po or source_alt_po == match_alt_po)):
                po_matches += 1
        
        total_records = len(type_df)
        avg_score = type_df['Match_Score'].mean() if match_type != 'NO_MATCH' else 0
        
        # Get example POs
        examples = type_df['Customer_PO'].dropna().head(3).tolist()
        if not examples:
            examples = type_df['Customer_Alt_PO'].dropna().head(3).tolist()
        
        analysis_data.append({
            'Match_Type': match_type,
            'Records': total_records,
            'Style_Match_%': round((style_matches / total_records) * 100, 1),
            'Color_Match_%': round((color_matches / total_records) * 100, 1),
            'Size_Match_%': round((size_matches / total_records) * 100, 1),
            'PO_Match_%': round((po_matches / total_records) * 100, 1),
            'Avg_Score': round(avg_score, 1),
            'Examples': ', '.join(str(x) for x in examples[:3])
        })
    
    return pd.DataFrame(analysis_data)

def create_field_issues_analysis(customer_df):
    """
    Create field-level issues analysis for a customer.
    """
    fields_data = []
    
    field_mapping = {
        'Style': ['Style', 'Pattern_ID'],
        'Color': ['Color'],
        'Size': ['Size'],
        'PO': ['Customer_PO'],
        'Alt_PO': ['Customer_Alt_PO']
    }
    
    for field_name, columns in field_mapping.items():
        missing_data = 0
        low_match_records = []
        
        for col in columns:
            if col in customer_df.columns:
                missing_data += customer_df[col].isna().sum()
        
        # Find records with low match rates for this field
        if field_name == 'Style':
            # Check style matches
            for _, row in customer_df.iterrows():
                if row['Match_Type'] in ['EXACT', 'FUZZY']:
                    source_style = str(row.get('Style', '')).strip().upper()
                    source_pattern = str(row.get('Pattern_ID', '')).strip().upper()
                    match_style = str(row.get('Best_Match_Style', '')).strip().upper()
                    match_pattern = str(row.get('Best_Match_Pattern_ID', '')).strip().upper()
                    
                    if not ((source_style and match_style and source_style == match_style) or \
                           (source_pattern and match_pattern and source_pattern == match_pattern)):
                        low_match_records.append(f"{source_style or source_pattern} vs {match_style or match_pattern}")
        
        fields_data.append({
            'Field': field_name,
            'Missing_Data': missing_data,
            'Low_Match_Examples': '; '.join(low_match_records[:3]) if low_match_records else 'None'
        })
    
    return pd.DataFrame(fields_data)

def create_quantity_variance_analysis(customer_df):
    """
    Create quantity variance analysis grouped by PO.
    """
    # Group by PO (use Best_Match_PO or Customer_PO)
    customer_df['Analysis_PO'] = customer_df['Best_Match_PO'].fillna(customer_df['Customer_PO'])
    
    po_analysis = customer_df.groupby('Analysis_PO', dropna=False).agg({
        'Ordered_Qty': 'sum',
        'Packed_Qty': 'sum',
        'Shipped_Qty': 'sum'
    }).reset_index()
    
    po_analysis['Variance'] = po_analysis['Shipped_Qty'] - po_analysis['Ordered_Qty']
    po_analysis['Variance_%'] = np.where(
        po_analysis['Ordered_Qty'] > 0,
        round((po_analysis['Variance'] / po_analysis['Ordered_Qty']) * 100, 1),
        0
    )
    
    # Classify issue type
    def classify_issue(row):
        if row['Variance'] > 0:
            return 'Over_Ship'
        elif row['Variance'] < 0:
            return 'Under_Ship'
        else:
            return 'Balanced'
    
    po_analysis['Issue_Type'] = po_analysis.apply(classify_issue, axis=1)
    
    # Sort by absolute variance
    po_analysis['Abs_Variance_%'] = abs(po_analysis['Variance_%'])
    po_analysis = po_analysis.sort_values('Abs_Variance_%', ascending=False)
    
    return po_analysis[['Analysis_PO', 'Ordered_Qty', 'Packed_Qty', 'Shipped_Qty', 
                      'Variance', 'Variance_%', 'Issue_Type']].head(20)

# Helper functions for field matching
def field_exact_match(field1, field2):
    """
    Helper function to check if two fields match exactly (case-insensitive, whitespace-trimmed).
    Returns True if both fields are non-empty and equal, False otherwise.
    """
    if pd.isna(field1) or pd.isna(field2):
        return False
    str1 = str(field1).strip().upper()
    str2 = str(field2).strip().upper()
    return str1 != '' and str2 != '' and str1 == str2

def vectorized_field_exact_match(series1, series2):
    """
    Vectorized version of field_exact_match for pandas Series.
    """
    norm1 = series1.fillna('').astype(str).str.strip().str.upper()
    norm2 = series2.fillna('').astype(str).str.strip().str.upper()
    return norm1.ne('') & norm2.ne('') & norm1.eq(norm2)

