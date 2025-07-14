

### '''
## Functional Summary:
## - Connects subitem data to orders_shipped and orders_packed tables/views for downstream reporting.
## - Supports updating Monday.com subitems via the GraphQL API.
## - Uses async HTTP requests for efficient data retrieval from Monday.com.
## - Configuration for Monday.com API and Azure SQL is loaded from config.yaml.
## - Designed for robust error handling and logging.
## 
## Checklist:
## - [ ] Load config from config.yaml
## - [ ] Relate subitem table to MON_CustMasterSchedule, orders_shipped, and orders_packed
## - [ ] Provide function to update Monday.com subitems via GraphQL API
## - [ ] Implement async HTTP requests for Monday.com updates
## - [ ] Error handling and logging
## - [ ] Add summary and error report
### '''

# --- Imports ---
import asyncio
import aiohttp
import pyodbc
import pandas as pd
import yaml
import os
import json
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")


# --- Load config ---
def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

config = load_config()
DB_CONFIG = config['databases']


# --- Load DataFrames from SQL Views ---
def load_sql_view(view_filename, db_key):
    db_cfg = DB_CONFIG[db_key]
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={db_cfg['host']},{db_cfg.get('port', 1433)};"
        f"DATABASE={db_cfg['database']};"
        f"UID={db_cfg['username']};PWD={db_cfg['password']};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    sql_path = os.path.join(os.path.dirname(__file__), '..', '..', 'views', view_filename)
    with open(sql_path, 'r') as f:
        sql_query = f.read()
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(sql_query, conn)
    return df



######################################################################
# --- Helper Functions (must be defined before main) ---
######################################################################

# --- Customer Mapping Loader ---
def load_customer_mapping(mapping_path=None):
    """Load customer mapping YAML and build alias-to-canonical dict."""
    if mapping_path is None:
        mapping_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'customer_mapping.yaml')
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = yaml.safe_load(f)
    alias_to_canonical = {}
    for entry in mapping['customers']:
        canonical = entry['canonical'].strip().upper()
        for alias in entry.get('aliases', []):
            alias_to_canonical[alias.strip().upper()] = canonical
    return alias_to_canonical

# --- Apply customer mapping to DataFrame column ---
def map_customers(df, col, alias_to_canonical, new_col='Customer_Canonical'):
    """Map customer names in df[col] to canonical using alias_to_canonical."""
    def map_func(val):
        key = normalize_str(val)
        return alias_to_canonical.get(key, key)
    df[new_col] = df[col].apply(map_func)
    # Optionally log unmapped
    unmapped = set(df[col].apply(normalize_str)) - set(alias_to_canonical.keys())
    if unmapped:
        print(f"[WARN] Unmapped customer names in column '{col}': {sorted(unmapped)}")
    return df

# --- Data Normalization Helper ---
def normalize_str(s):
    if pd.isna(s):
        return ''
    return str(s).strip().upper()

# --- Aggregate shipped quantities ---
def aggregate_packed(df_packed):
    for col in ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']:
        if col in df_packed.columns:
            df_packed[col] = df_packed[col].apply(normalize_str)
    df_agg = (
        df_packed
        .groupby(['Customer', 'Customer_PO', 'Style', 'Color', 'Size'], as_index=False)
        .agg({'Qty': 'sum'})
        .rename(columns={'Qty': 'Qty_Packed'})
    )
    df_agg['Qty_Packed'] = df_agg['Qty_Packed'].round(0).astype(int)
    return df_agg

# --- Aggregate shipped by CUSTOMER + PO + STYLE + COLOR + SIZE ---
def aggregate_shipped(df_shipped):
    # Normalize join columns
    for col in ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']:
        if col in df_shipped.columns:
            df_shipped[col] = df_shipped[col].apply(normalize_str)
    df_agg = (
        df_shipped
        .groupby(['Customer', 'Customer_PO', 'Style', 'Color', 'Size'], as_index=False)
        .agg({'Qty': 'sum'})
        .rename(columns={'Qty': 'Qty_Shipped'})
    )
    # Round Qty_Shipped to int, no decimals
    df_agg['Qty_Shipped'] = df_agg['Qty_Shipped'].round(0).astype(int)
    return df_agg



# --- Monday.com API Settings (shared conventions) ---
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"
AUTH_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
# Use the same environment variable or config for the API key
# AUTH_KEY = os.environ.get("MONDAY_API_KEY") or config.get('monday', {}).get('api_key')
HEADERS = {
    "Content-Type": "application/json",
    "API-Version": API_VERSION,
    "Authorization": f"Bearer {AUTH_KEY}"
}

# --- Monday.com column ID reference (for subitems) ---
# "dropdown_mkrak7qp"   # Size (Dropdown)
# "numeric_mkra7j8e"    # Order Qty
# "numeric_mkrapgwv"    # Shipped Qty
# "numeric_mkraepx7"    # Packed Qty
# "numeric_mkrbgdat"    # Cut Qty
# "numeric_mkrc5ryb"    # Sew Qty
# "numeric_mkrc7jfj"    # Finishing Qty
# "numeric_mkrcq53k"    # Received not Shipped Qty
# "color_mkrbezbh"      # ORDER LINE STATUS
# "pulse_id_mkrag4a3"   # Item ID

import math

def build_monday_update_mutation(subitem_id, board_id, shipped_qty=None, packed_qty=None):
    """
    Build a GraphQL mutation for Monday.com to update subitem columns.
    Only include columns you want to update.
    """
    column_values = {}
    if shipped_qty is not None and not (isinstance(shipped_qty, float) and math.isnan(shipped_qty)):
        column_values["numeric_mkrapgwv"] = str(int(shipped_qty))
    if packed_qty is not None and not (isinstance(packed_qty, float) and math.isnan(packed_qty)):
        column_values["numeric_mkraepx7"] = str(int(packed_qty))
    # Add more columns as needed

    mutation = {
        "query": f'''
            mutation {{
              change_multiple_column_values(
                item_id: {subitem_id},
                board_id: {board_id},
                column_values: "{json.dumps(column_values).replace('"', '\\"')}"
              ) {{
                id
              }}
            }}
        '''
    }
    return mutation

async def update_monday_subitem(session, subitem_id, board_id, shipped_qty=None, packed_qty=None):
    mutation = build_monday_update_mutation(subitem_id, board_id, shipped_qty, packed_qty)
    async with session.post(API_URL, headers=HEADERS, json=mutation, ssl=False) as resp:
        result = await resp.json()
        return result

async def update_all_subitems(df):
    async with aiohttp.ClientSession() as session:
        for _, row in df.iterrows():
            subitem_id = row['subitem_id']
            board_id = row['subitem_board_id']
            shipped_qty = row.get('Qty_Shipped')
            packed_qty = row.get('Qty_Packed')
            result = await update_monday_subitem(session, subitem_id, board_id, shipped_qty=shipped_qty, packed_qty=packed_qty)
            print(f"Updated subitem {subitem_id}: {result}")

# --- Main async entrypoint ---
async def main():
    """
    Main async workflow:
    - Loads subitems, shipped, and packed data from SQL views
    - Aggregates shipped and packed quantities
    - Merges dataframes for update
    - Updates Monday.com subitems via async GraphQL API
    """
    print("[INFO] Loading DataFrames from SQL views...")
    df_subitems = load_sql_view('v_mon_customer_ms_subitems.sql', 'orders')
    df_shipped = load_sql_view('v_shipped.sql', 'wah')
    df_packed = load_sql_view('v_packed_products.sql', 'distribution')

    print("[INFO] Subitems DataFrame loaded:")
    print(df_subitems.head())
    print("[INFO] Shipped DataFrame loaded:")
    print(df_shipped.head())
    print("[INFO] Packed DataFrame loaded:")
    print(df_packed.head())

    # --- Load and apply customer mapping ---
    print("[INFO] Loading customer mapping from customer_mapping.yaml ...")
    alias_to_canonical = load_customer_mapping()
    # Map customers in all DataFrames (column names may differ)
    if 'CUSTOMER' in df_subitems.columns:
        df_subitems = map_customers(df_subitems, 'CUSTOMER', alias_to_canonical)
    if 'Customer' in df_shipped.columns:
        df_shipped = map_customers(df_shipped, 'Customer', alias_to_canonical)
    if 'Customer' in df_packed.columns:
        df_packed = map_customers(df_packed, 'Customer', alias_to_canonical)

    # Use canonical for all downstream processing
    # Rename canonical columns for join/agg
    if 'Customer_Canonical' in df_subitems.columns:
        df_subitems['CUSTOMER'] = df_subitems['Customer_Canonical']
    if 'Customer_Canonical' in df_shipped.columns:
        df_shipped['Customer'] = df_shipped['Customer_Canonical']
    if 'Customer_Canonical' in df_packed.columns:
        df_packed['Customer'] = df_packed['Customer_Canonical']


    print("[INFO] Aggregating shipped quantities...")
    df_shipped_agg = aggregate_shipped(df_shipped)
    print(df_shipped_agg.head())

    print("[INFO] Aggregating packed quantities...")
    df_packed_agg = aggregate_packed(df_packed)
    print(df_packed_agg.head())

    print("[INFO] Merging shipped data into subitems DataFrame...")
    df_merged = pd.merge(
        df_subitems,
        df_shipped_agg,
        left_on=['CUSTOMER', 'PO NUMBER', 'Style', 'COLOR', 'Size'],
        right_on=['Customer', 'Customer_PO', 'Style', 'Color', 'Size'],
        how='left',
        suffixes=('', '_shipped')
    )
    print(df_merged.head())

    print("[INFO] Merging packed data into main DataFrame...")
    df_merged = pd.merge(
        df_merged,
        df_packed_agg,
        left_on=['CUSTOMER', 'PO NUMBER', 'Style', 'COLOR', 'Size'],
        right_on=['Customer', 'Customer_PO', 'Style', 'Color', 'Size'],
        how='left',
        suffixes=('', '_packed')
    )
    print(df_merged.head())

    print("[INFO] Updating Monday.com subitems...")
    await update_all_subitems(df_merged)


# --- Script entrypoint ---
if __name__ == "__main__":
    asyncio.run(main())

# --- Data Normalization Helper ---
def normalize_str(s):
    if pd.isna(s):
        return ''
    return str(s).strip().upper()

# --- Aggregate shipped quantities ---
def aggregate_packed(df_packed):
    for col in ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']:
        if col in df_packed.columns:
            df_packed[col] = df_packed[col].apply(normalize_str)
    df_agg = (
        df_packed
        .groupby(['Customer', 'Customer_PO', 'Style', 'Color', 'Size'], as_index=False)
        .agg({'Qty': 'sum'})
        .rename(columns={'Qty': 'Qty_Packed'})
    )
    df_agg['Qty_Packed'] = df_agg['Qty_Packed'].round(0).astype(int)
    return df_agg

# --- Aggregate shipped by CUSTOMER + PO + STYLE + COLOR + SIZE ---
def aggregate_shipped(df_shipped):
    # Normalize join columns
    for col in ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']:
        if col in df_shipped.columns:
            df_shipped[col] = df_shipped[col].apply(normalize_str)
    df_agg = (
        df_shipped
        .groupby(['Customer', 'Customer_PO', 'Style', 'Color', 'Size'], as_index=False)
        .agg({'Qty': 'sum'})
        .rename(columns={'Qty': 'Qty_Shipped'})
    )
    # Round Qty_Shipped to int, no decimals
    df_agg['Qty_Shipped'] = df_agg['Qty_Shipped'].round(0).astype(int)
    return df_agg

# --- Join to subitems df on CUSTOMER + STYLE + COLOR + SIZE ---
def join_subitems_shipped(df_subitems, df_shipped_agg):
    # Normalize join columns in subitems
    for col, canon in zip(['CUSTOMER', 'PO NUMBER', 'Style', 'COLOR', 'Size'],
                          ['Customer', 'Customer_PO', 'Style', 'Color', 'Size']):
        if col in df_subitems.columns:
            df_subitems[col] = df_subitems[col].apply(normalize_str)
    df_merged = pd.merge(
        df_subitems,
        df_shipped_agg,
        left_on=['CUSTOMER', 'PO NUMBER', 'Style', 'COLOR', 'Size'],
        right_on=['Customer', 'Customer_PO', 'Style', 'Color', 'Size'],
        how='left'
    )
    return df_merged



# --- Monday.com subitem update ---
# TODO: Implement async update of Monday.com subitems via GraphQL API

# --- Main async entrypoint ---
# TODO: Implement main() and asyncio.run(main())
