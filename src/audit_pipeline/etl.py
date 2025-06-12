import pandas as pd
import logging

def standardize_dataset(df, source_type, qty_col='Qty', customer_alias_map=None):
    """
    Standardize dataset to consistent format with core matching fields.
    """
    standardized = df.copy()
    required_cols = ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']
    for col in required_cols:
        if col not in standardized.columns:
            standardized[col] = None
    for col in ['Customer_Alt_PO', 'Pattern_ID']:
        if col not in standardized.columns:
            standardized[col] = None
    if qty_col in standardized.columns and qty_col != 'Qty':
        standardized['Qty'] = standardized[qty_col]
    elif 'Qty' not in standardized.columns:
        standardized['Qty'] = 1
    standardized['Source_Type'] = source_type
    
    text_cols = ['Customer', 'Customer_PO', 'Customer_Alt_PO', 'Style', 'Pattern_ID', 'Color', 'Size']
    for col in text_cols:
        if col in standardized.columns:
            standardized[col] = standardized[col].astype(str).str.strip().str.upper()
            # Replace various null-like values with actual None
            standardized[col] = standardized[col].replace(['NAN', 'NONE', 'NULL', ''], None)
    if customer_alias_map:
        standardized['Canonical_Customer'] = standardized['Customer'].apply(
            lambda x: customer_alias_map.get(x, x)
        )
    else:
        standardized['Canonical_Customer'] = standardized['Customer']
    return standardized

def handle_master_order_list(df, customer_alias_map):
    """
    Convert wide-format orders to long format, standardize and aggregate result.
    """
    logging.info("Processing master order list for melting")
    size_cols = []
    if 'UNIT OF MEASURE' in df.columns:
        try:
            start_idx = df.columns.get_loc('UNIT OF MEASURE')
            end_col = None
            if 'TOTAL QTY' in df.columns:
                end_col = 'TOTAL QTY'
            elif 'Qty' in df.columns:
                end_col = 'Qty'
            if end_col:
                end_idx = df.columns.get_loc(end_col)
                size_cols = df.columns[start_idx + 1:end_idx].tolist()
        except KeyError:
            pass
    
    if size_cols:
        id_vars = ['Customer', 'Customer_PO', 'Customer_Alt_PO', 'Style', 'Color', 'Pattern_ID']
        df_melted = df.melt(
            id_vars=id_vars,
            value_vars=size_cols,
            var_name='Size',
            value_name='Ordered_Qty'
        )
        df_melted['Ordered_Qty'] = pd.to_numeric(df_melted['Ordered_Qty'], errors='coerce')
        df_melted = df_melted[df_melted['Ordered_Qty'] > 0]
        df_std = standardize_dataset(df_melted, 'ORDERS', 'Ordered_Qty', customer_alias_map)
    else:
        df_std = standardize_dataset(df, 'ORDERS', 'Qty', customer_alias_map)
        df_std['Ordered_Qty'] = df_std['Qty']
      # Aggregate orders by matching fields to prevent duplicate joins
    logging.info(f"Aggregating orders dataset. Pre-aggregation size: {len(df_std)}")
    agg_cols = [
        'Canonical_Customer', 'Customer', 'Customer_PO', 'Customer_Alt_PO',
        'Style', 'Pattern_ID', 'Color', 'Size'
    ]
    
    # Fill None values temporarily for aggregation, then restore them
    df_for_agg = df_std.copy()
    none_replacement = '__TEMP_NONE__'
    for col in agg_cols:
        if col in df_for_agg.columns:
            df_for_agg[col] = df_for_agg[col].fillna(none_replacement)
    
    # Group and sum ordered quantities
    df_aggregated = df_for_agg.groupby(agg_cols, as_index=False, dropna=False).agg({
        'Ordered_Qty': 'sum',
        'Source_Type': 'first'  # Keep source type
    })
    
    # Restore None values
    for col in agg_cols:
        if col in df_aggregated.columns:
            df_aggregated[col] = df_aggregated[col].replace(none_replacement, None)
    
    logging.info(f"Orders aggregation complete. Post-aggregation size: {len(df_aggregated)}")
    logging.info(f"Aggregation removed {len(df_std) - len(df_aggregated)} duplicate order lines")
    
    return df_aggregated

