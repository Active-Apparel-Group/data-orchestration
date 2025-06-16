''' 
Functional Summary:
- Fetches Item IDs from the MON_CustMasterSchedule (via the v_mon_customer_ms_itemIDs.sql view).
- For each Item ID, queries Monday.com (GraphQL API) to fetch all subitems and their details.
- Stores subitem data in an Azure SQL database, linking subitems to their parent MON_CustMasterSchedule items.

Checklist:
- [ ] Load config from config.yaml
- [ ] Query Azure SQL for Item IDs
- [ ] Async fetch subitems from Monday.com for each Item ID
- [ ] Parse and normalize subitem data
- [ ] Store subitem data in Azure SQL, linked to parent Item ID
- [ ] Error handling and logging
'''

# --- Imports ---
import asyncio
import aiohttp
import pyodbc
import pandas as pd
import yaml
import os
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")



# --- Monday.com Async Subitem Fetch ---
API_URL = "https://api.monday.com/v2"
AUTH_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
API_VERSION = "2025-04"
HEADERS = {
    "Content-Type": "application/json",
    "API-Version": API_VERSION,
    "Authorization": f"Bearer {AUTH_KEY or 'YOUR_API_KEY_HERE'}"
}

SUBITEMS_QUERY_TEMPLATE = '''
query {{
  items(ids: {item_id}) {{
    id
    board {{ id }}
    subitems {{
      id
      board {{ id }}
      parent_item {{ id }}
      column_values {{
        id
        value
        text
        type
        __typename
        ... on DropdownValue {{ text }}
        column {{ title }}
        ... on NumbersValue {{ number }}
        column {{ title }}
      }}
    }}
  }}
}}
'''

async def fetch_subitems_for_item(session, item_id):
    query = SUBITEMS_QUERY_TEMPLATE.format(item_id=item_id)
    async with session.post(API_URL, headers=HEADERS, json={"query": query}, ssl=False) as response:
        if response.status == 200:
            return await response.json()
        else:
            text = await response.text()
            print(f"[ERROR] Query failed for Item ID {item_id}: {text}")
            return None

async def fetch_all_subitems(item_ids, concurrency=12):
    """
    Fetch subitems for all item_ids with limited concurrency (default 12).
    This matches the safe concurrency for Monday.com API (see delete script).
    """
    results = {}
    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        async def fetch_with_limit(item_id):
            async with semaphore:
                return item_id, await fetch_subitems_for_item(session, item_id)
        tasks = [fetch_with_limit(item_id) for item_id in item_ids]
        for future in asyncio.as_completed(tasks):
            item_id, result = await future
            results[item_id] = result
    return results

# --- Load config ---
def load_config(config_path=None):
    """Load YAML config from the given path or default location."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

config = load_config()
DB_CONFIG = config['databases']
LOGGING_ENABLED = config.get('settings', {}).get('logging', True)


# --- SQL: Fetch Item IDs ---
def get_item_ids_from_view(return_count_only=False):
    """
    Query the v_mon_customer_ms_itemIDs.sql view in the 'orders' database to get Item IDs and related info.
    If return_count_only is True, returns the record count (int) instead of the DataFrame.
    """
    orders_cfg = DB_CONFIG['orders']
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={orders_cfg['host']},{orders_cfg.get('port', 1433)};"
        f"DATABASE={orders_cfg['database']};"
        f"UID={orders_cfg['username']};PWD={orders_cfg['password']};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    # Read the SQL from the view file
    sql_path = os.path.join(os.path.dirname(__file__), '..', '..', 'views', 'v_mon_customer_ms_itemIDs.sql')
    with open(sql_path, 'r') as f:
        sql_query = f.read()
    if return_count_only:
        count_query = f"SELECT COUNT(*) as record_count FROM ( {sql_query} ) AS subquery"
        with pyodbc.connect(conn_str) as conn:
            result = pd.read_sql(count_query, conn)
        return int(result['record_count'].iloc[0])
    else:
        with pyodbc.connect(conn_str) as conn:
            df = pd.read_sql(sql_query, conn)
        return df


# --- SQL Server Table Management and Upsert (pyodbc only) ---
def table_exists_pyodbc(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?
    """, (table_name,))
    return cursor.fetchone() is not None

def get_existing_columns_pyodbc(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?
    """, (table_name,))
    return [row[0] for row in cursor.fetchall()]

def create_table_pyodbc(conn, table_name, columns):
    col_defs = ", ".join(f"[{col}] NVARCHAR(MAX)" for col in columns)
    sql = f"CREATE TABLE [{table_name}] ({col_defs})"
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()

def add_missing_columns_pyodbc(conn, table_name, missing_columns):
    cursor = conn.cursor()
    for col in missing_columns:
        sql = f"ALTER TABLE [{table_name}] ADD [{col}] NVARCHAR(MAX)"
        cursor.execute(sql)
    conn.commit()

def ensure_table_and_columns(df, table_name, conn_str):
    columns = list(df.columns)
    with pyodbc.connect(conn_str) as conn:
        if not table_exists_pyodbc(conn, table_name):
            create_table_pyodbc(conn, table_name, columns)
            print(f"[INFO] Created table {table_name} with columns: {columns}")
        else:
            existing_cols = get_existing_columns_pyodbc(conn, table_name)
            missing = [col for col in columns if col not in existing_cols]
            if missing:
                add_missing_columns_pyodbc(conn, table_name, missing)
                print(f"[INFO] Added missing columns {missing} to {table_name}")

def upsert_dataframe(df, table_name, conn_str, key_columns):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            # Build WHERE clause for key columns
            where = " AND ".join(f"[{col}] = ?" for col in key_columns)
            delete_sql = f"DELETE FROM [{table_name}] WHERE {where}"
            cursor.execute(delete_sql, tuple(row[col] for col in key_columns))
            # Insert row
            cols = list(df.columns)
            insert_sql = f"INSERT INTO [{table_name}] ({', '.join(f'[{c}]' for c in cols)}) VALUES ({', '.join('?' for _ in cols)})"
            cursor.execute(insert_sql, tuple(row[c] for c in cols))
        conn.commit()
    print(f"[INFO] Upserted {len(df)} rows into {table_name}")
    
# --- Utility: Convert subitems API response to DataFrame ---
def subitems_to_dataframe(item_result):
    """
    Convert Monday.com subitems API response for a single item to a pandas DataFrame.
    """
    if not item_result or 'data' not in item_result or not item_result['data']['items']:
        return pd.DataFrame()
    item = item_result['data']['items'][0]
    subitems = item.get('subitems', [])
    records = []
    for sub in subitems:
        record = {
            'parent_item_id': item['id'],
            'subitem_id': sub['id'],
            'subitem_board_id': sub['board']['id'],
        }
        # Flatten column values
        for col in sub.get('column_values', []):
            col_title = col['column']['title']
            value = col.get('number')
            if value is None:
                value = col.get('text')
            if value is None:
                value = col.get('value')
            record[col_title] = value
        records.append(record)
    return pd.DataFrame(records)

# --- Safe Upsert with MERGE (only update specified columns) ---
def upsert_dataframe_merge(df, table_name, conn_str, key_columns, update_columns):
    """
    Upsert DataFrame rows into SQL Server table using MERGE.
    Only updates columns in update_columns, preserving all other data.
    """
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            # Build source values and column lists
            all_cols = key_columns + update_columns
            source_values = ', '.join(['?'] * len(all_cols))
            source_cols = ', '.join(f'[{col}]' for col in all_cols)
            # Build ON clause
            on_clause = ' AND '.join([f'target.[{col}] = source.[{col}]' for col in key_columns])
            # Build UPDATE clause
            update_clause = ', '.join([f'target.[{col}] = source.[{col}]' for col in update_columns])
            # Build INSERT columns/values
            insert_cols = ', '.join(f'[{col}]' for col in all_cols)
            insert_vals = ', '.join(f'source.[{col}]' for col in all_cols)
            # MERGE SQL
            merge_sql = f"""
                MERGE INTO [{table_name}] AS target
                USING (SELECT {source_values}) AS source ({source_cols})
                ON {on_clause}
                WHEN MATCHED THEN
                    UPDATE SET {update_clause}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols}) VALUES ({insert_vals});
            """
            # Prepare values in order: key_columns + update_columns
            values = [row[col] for col in key_columns + update_columns]
            cursor.execute(merge_sql, values)
        conn.commit()
    print(f"[INFO] Upserted {len(df)} rows into {table_name} (MERGE, safe update)")

# --- Test: Run record count query ---

# --- Main async entrypoint: test async fetch ---

if __name__ == "__main__":
    try:
        count = get_item_ids_from_view(return_count_only=True)
        print(f"[TEST] Record count from v_mon_customer_ms_itemIDs view: {count}")
        df = get_item_ids_from_view()
        item_ids = df['Item ID'].dropna().astype(str).tolist()
        print(f"[INFO] Fetching subitems for {len(item_ids)} Item IDs (first 3 shown): {item_ids[:3]}")

        # Check API key
        if not AUTH_KEY or AUTH_KEY == 'YOUR_API_KEY_HERE':
            print("[ERROR] Monday.com API key is missing or not set. Please set AUTH_KEY or the MONDAY_API_KEY environment variable.")
            exit(1)

        # Print the actual query for the first item for debugging
        if item_ids:
            test_query = SUBITEMS_QUERY_TEMPLATE.format(item_id=item_ids[0])
            print(f"[DEBUG] Example Monday.com GraphQL query for Item ID {item_ids[0]}:\n{test_query}")

        # Fetch all item IDs with safe concurrency (12)
        async def main_async():
            results = await fetch_all_subitems(item_ids, concurrency=12)
            for item_id, result in results.items():
                if result and 'data' in result:
                    subitems = result['data']['items'][0].get('subitems', [])
                    print(f"[RESULT] Item ID {item_id}: {len(subitems)} subitems fetched.")
                    # Summarize in DataFrame for review
                    df_sub = subitems_to_dataframe(result)
                    print(f"[DATAFRAME] Subitems DataFrame for Item ID {item_id}:")
                    # Show all columns and rows in the DataFrame output (temporary for development)
                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.width', 2000)
                    pd.set_option('display.max_colwidth', None)
                    print(df_sub)
                    # --- Integration: Ensure table and upsert data ---
                    conn_str = (
                        "DRIVER={SQL Server};"
                        f"SERVER={DB_CONFIG['orders']['host']},{DB_CONFIG['orders'].get('port', 1433)};"
                        f"DATABASE={DB_CONFIG['orders']['database']};"
                        f"UID={DB_CONFIG['orders']['username']};PWD={DB_CONFIG['orders']['password']};"
                        "Encrypt=no;TrustServerCertificate=yes;"
                    )
                    table_name = 'MON_CustMasterSchedule_Subitems'
                    key_columns = ['subitem_id']
                    if not df_sub.empty:
                        ensure_table_and_columns(df_sub, table_name, conn_str)
                        upsert_dataframe(df_sub, table_name, conn_str, key_columns)
                else:
                    print(f"[RESULT] Item ID {item_id}: No data or error. Response: {result}")
        asyncio.run(main_async())
    except Exception as e:
        print(f"[ERROR] Failed to fetch record count or run async test: {e}")

# --- Async Monday.com fetch ---
# TODO: Implement async GraphQL queries to Monday.com for subitems per Item ID

# --- Parse and store subitem data ---
# TODO: Normalize and store subitem data in Azure SQL, linked to parent Item ID

# --- Main async entrypoint ---
# TODO: Implement main() and asyncio.run(main())
