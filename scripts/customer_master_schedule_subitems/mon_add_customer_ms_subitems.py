# This script processes customer master schedule data and uploads subitem details to Monday.com.
    # Workflow:
        # 1. Loads database configuration from a YAML file.
        # 2. Connects to a SQL Server database using credentials from the configuration.
        # 3. Retrieves all records from the [MON_CustMasterSchedule] table.
        # 4. For each unique order number:
        #     - Queries the [ORDERS_UNIFIED] table for order details.
        #     - Identifies and unpivots size columns between 'UNIT OF MEASURE' and 'TOTAL QTY'.
        #     - Filters for valid, positive order quantities.
        #     - Merges relevant item/style/color info from the master schedule.
        # 5. Combines all processed rows into a single DataFrame.
        # 6. For each row, uploads a subitem to Monday.com under the corresponding parent item, using the Monday.com API.
        # Key Functions:
        # - `add_subitem_to_monday(parent_item_id, item_name, order_qty)`: Adds a subitem to a Monday.com item with specified details.
        # Configuration:
        # - Expects a `config.yaml` file with database connection details.
        # - Requires a valid Monday.com API key and configuration.
        # Dependencies:
        # - pandas, pyodbc, yaml, tqdm, requests, json, warnings, os
        # Note:
        # - Suppresses pandas UserWarnings.
        # - Prints errors for configuration loading and failed API requests.
#

import pandas as pd
import os
import yaml
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")
from tqdm import tqdm

# Load DB_CONFIG from config.yaml (same as build_customer_mapping_table.py)
try:
    import yaml
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'), 'r') as config_file:
        config = yaml.safe_load(config_file)
        DB_CONFIG = config['databases']
except Exception as e:
    print(f"Error loading configuration: {e}")
    DB_CONFIG = {}

import pyodbc

# Use the 'orders' config
orders_cfg = DB_CONFIG['orders']
conn_str = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={orders_cfg['host']};"
    f"DATABASE={orders_cfg['database']};"
    f"UID={orders_cfg['username']};PWD={orders_cfg['password']};"
    "Encrypt=no;TrustServerCertificate=yes;"
)

query = """
SELECT cms.*
FROM [dbo].[MON_CustMasterSchedule] cms 
where [CUSTOMER] like 'TAYLOR%'
order by [AAG ORDER NUMBER] asc
"""

with pyodbc.connect(conn_str) as conn:

    df = pd.read_sql(query, conn)


# --- Enhanced logic for handling multiple CMS records per AAG ORDER NUMBER ---
order_numbers = df['AAG ORDER NUMBER'].unique()
all_rows = []
error_cms_records = []

for order_num in order_numbers:
    # Get all CMS records for this AAG ORDER NUMBER
    cms_rows = df[df['AAG ORDER NUMBER'] == order_num]
    # Query ORDERS_UNIFIED for this order number
    jo_query = f"""
        SELECT * FROM dbo.ORDERS_UNIFIED WHERE [AAG ORDER NUMBER] = ?
    """
    jo_df = pd.read_sql(jo_query, conn, params=[order_num])
    if jo_df.empty:
        continue
    # For each CMS record (may be >1 for this order number)
    for _, cms_row in cms_rows.iterrows():
        # Step 1: Try to match ORDERS_UNIFIED by PO NUMBER
        po_number = cms_row['PO NUMBER']
        match_df = jo_df[jo_df['PO NUMBER'] == po_number]
        # Step 2: If no match, try CUSTOMER ALT PO
        if match_df.empty and 'CUSTOMER ALT PO' in jo_df.columns:
            match_df = jo_df[jo_df['CUSTOMER ALT PO'] == po_number]
        # Step 3: If still no match, log error and continue
        if match_df.empty:
            error_cms_records.append({
                'AAG ORDER NUMBER': order_num,
                'PO NUMBER': po_number,
                'Error': 'No match in ORDERS_UNIFIED for PO NUMBER or CUSTOMER ALT PO'
            })
            continue
        # For each match in ORDERS_UNIFIED (should usually be one, but handle all)
        for _, order_row in match_df.iterrows():
            # Find size columns between 'UNIT OF MEASURE' and 'TOTAL QTY'
            try:
                start = match_df.columns.get_loc('UNIT OF MEASURE')
                end = match_df.columns.get_loc('TOTAL QTY')
                size_cols = match_df.columns[start+1:end]
            except KeyError:
                error_cms_records.append({
                    'AAG ORDER NUMBER': order_num,
                    'PO NUMBER': po_number,
                    'Error': 'Missing size columns in ORDERS_UNIFIED'
                })
                continue
            # Melt to unpivot size columns
            melted = pd.DataFrame([order_row]).melt(
                id_vars=['AAG ORDER NUMBER', 'UNIT OF MEASURE', 'TOTAL QTY'],
                value_vars=size_cols,
                var_name='SIZE_LABEL',
                value_name='ORDER_QTY'
            )
            # Keep only rows where ORDER_QTY is a number and > 0
            melted = melted[pd.to_numeric(melted['ORDER_QTY'], errors='coerce').notnull()]
            melted = melted[melted['ORDER_QTY'] > 0]
            # Add info from cms for this order
            melted['Item ID'] = cms_row['Item ID']
            melted['STYLE'] = cms_row['STYLE']
            melted['COLOR'] = cms_row['COLOR']
            # Reorder columns
            melted = melted[['Item ID', 'STYLE', 'COLOR', 'AAG ORDER NUMBER', 'UNIT OF MEASURE', 'SIZE_LABEL', 'ORDER_QTY']]
            all_rows.append(melted)

# Combine all results

import requests
import json

# --- Monday.com API config ---
API_URL = "https://api.monday.com/v2"
AUTH_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
API_VERSION = "2025-04"
USER_ID = "31970889" # Chris Kalathas
HEADERS = {
    "Content-Type": "application/json",
    "API-Version": API_VERSION,
    "Authorization": f"Bearer {AUTH_KEY}"
}

def add_subitem_to_monday(parent_item_id, item_name, order_qty):
    column_values = json.dumps({
        "dropdown_mkrak7qp": {"labels": [str(item_name.replace('Size ', ''))]},
        "numeric_mkra7j8e": str(order_qty),
        "numeric_mkraepx7": 0,
        "numeric_mkrapgwv": 0
    })
    mutation = f'''
mutation AddSubitemsMasterSchedule {{
  create_subitem(
    parent_item_id: {parent_item_id},
    item_name: "{item_name}",
    column_values: "{column_values.replace('"', '\\"')}",
    create_labels_if_missing: true
  ) {{
    id
    name
  }}
}}
'''
    data = {'query': mutation}
    # print(f"\n---\nSending to Monday.com API:\nParent ID: {parent_item_id}\nItem Name: {item_name}\nOrder Qty: {order_qty}\nGraphQL Mutation: {mutation}\n---\n")
    response = requests.post(API_URL, headers=HEADERS, json=data, verify=False)
    if response.status_code == 200:
        resp_json = response.json()
        print(f"API Response: {resp_json}\n")
        return resp_json
    else:
        print(f"Failed to add subitem '{item_name}' to parent {parent_item_id}: {response.text}")
        return {"error": response.text}

import pandas as pd

error_records = []
success_count = 0


# --- Summary and API upload as before ---
if all_rows:
    final_df = pd.concat(all_rows, ignore_index=True)
    # Single progress bar for uploading
    with tqdm(total=final_df.shape[0], desc="Uploading to Monday.com") as pbar:
        for idx, row in final_df.iterrows():
            parent_item_id = row['Item ID']
            item_name = f"Size {row['SIZE_LABEL']}"
            order_qty = row['ORDER_QTY']
            resp_json = add_subitem_to_monday(parent_item_id, item_name, order_qty)
            # Error handling: collect error info if present
            if resp_json is not None:
                if 'errors' in resp_json:
                    for err in resp_json['errors']:
                        error_type = err.get('extensions', {}).get('code', 'Unknown')
                        error_msg = err.get('message', '')
                        error_records.append({
                            'row_index': idx,
                            'item_name': item_name,
                            'order_qty': order_qty,
                            'error_type': error_type,
                            'error_message': error_msg
                        })
                else:
                    # If no errors, count as success
                    success_count += 1
            else:
                # If no response, treat as error
                error_records.append({
                    'row_index': idx,
                    'item_name': item_name,
                    'order_qty': order_qty,
                    'error_type': 'NoResponse',
                    'error_message': 'No response from API'
                })
            pbar.update(1)
    print(final_df)
    # Print summary
    total = final_df.shape[0]
    error_count = len(error_records)
    print(f"\nSummary: {success_count} successful, {error_count} errors, {total} total records.")
    # Print error summary DataFrame
    if error_records:
        error_df = pd.DataFrame(error_records)
        summary = error_df.groupby(['error_type', 'error_message']).size().reset_index(name='count')
        print("\nError Summary:")
        print(summary)
    else:
        print("\nNo errors encountered during Monday.com API calls.")
else:
    print("No order subitems found.")

# --- Print CMS matching errors summary ---
if error_cms_records:
    error_cms_df = pd.DataFrame(error_cms_records)
    print("\nCMS Matching Errors Summary:")
    print(error_cms_df.groupby(['AAG ORDER NUMBER', 'PO NUMBER', 'Error']).size().reset_index(name='count'))