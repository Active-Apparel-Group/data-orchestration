"""
Incremental Real Data Ingest Test for ORDER_LIST
--------------------------------------------------
- Loads real data from a real x-prefixed ORDER_LIST table (e.g., xGREYSON_ORDER_LIST)
- Incrementally adds columns, attempts insert into a test table
- Stops on first SQL insert failure, prints failing value, column, and transformation logic
- Designed to debug SQL Server numeric/decimal conversion errors
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Standard import pattern

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))


# Add repo root to sys.path for all sibling folders (utils, scripts, etc.)
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root))
import db_helper as db
import logger_helper
from scripts.ingest import OrderListIngest

logger = logger_helper.get_logger(__name__)

def get_real_table_name():
    # Use the first x-prefixed ORDER_LIST table for GREYSON
    sql = """
    SELECT TOP 1 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME LIKE 'x%_ORDER_LIST%' AND TABLE_NAME != 'ORDER_LIST'
    ORDER BY TABLE_NAME
    """
    with db.get_connection('orders') as conn:
        df = pd.read_sql(sql, conn)
        if df.empty:
            raise Exception("No x-prefixed ORDER_LIST tables found!")
        return df.iloc[0,0]

def main():
    logger.info("Starting incremental real data ingest test...")
    ingest = OrderListIngest(dry_run=True)
    table_name = get_real_table_name()
    logger.info(f"Using table: {table_name}")

    # Load real data
    with db.get_connection('orders') as conn:
        df = pd.read_sql(f"SELECT TOP 100 * FROM [{table_name}]", conn)
    if df.empty:
        logger.error("Source table is empty!")
        return
    logger.info(f"Loaded {len(df)} rows from {table_name}")

    # Analyze columns and mapping
    schema_info = ingest.analyze_source_columns(table_name)
    column_mapping, _ = ingest.map_source_columns(df.columns.tolist())

    # Prepare test table (drop/create)
    test_table = "ORDER_LIST_INGEST_TEST"
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        cursor.execute(f"IF OBJECT_ID('{test_table}', 'U') IS NOT NULL DROP TABLE {test_table}")
        # Create with same schema as ORDER_LIST
        cursor.execute(f"SELECT TOP 0 * INTO {test_table} FROM ORDER_LIST")
        conn.commit()
    logger.info(f"Prepared test table: {test_table}")

    # Incrementally add columns and test insert
    all_cols = list(column_mapping.keys())
    for i in range(1, len(all_cols)+1):
        test_cols = all_cols[:i]
        logger.info(f"\nTesting with columns: {test_cols}")
        # Transform data
        transformed = ingest.transform_data_types(df[test_cols].copy(), {k: column_mapping[k] for k in test_cols}, schema_info)
        # Prepare for insert
        target_df = pd.DataFrame()
        for source_col in test_cols:
            target_col = column_mapping[source_col]
            target_df[target_col] = transformed[source_col]
        # Add required metadata columns
        target_df['CUSTOMER NAME'] = table_name.replace('_ORDER_LIST', '').replace('ORDER_LIST_', '').lstrip('x')
        target_df['_SOURCE_TABLE'] = table_name
        target_df['_INGESTED_AT'] = datetime.now()
        # Remove temp cols for insert
        insert_df = target_df.drop(columns=['_SOURCE_TABLE', '_INGESTED_AT'], errors='ignore')
        insert_df = ingest.convert_pandas_na_to_none(insert_df)
        # Try insert
        try:
            with db.get_connection('orders') as conn:
                cursor = conn.cursor()
                columns = ', '.join([f'[{col}]' for col in insert_df.columns])
                placeholders = ', '.join(['?' for _ in insert_df.columns])
                sql = f"INSERT INTO [{test_table}] ({columns}) VALUES ({placeholders})"
                for idx, row in insert_df.iterrows():
                    try:
                        cursor.execute(sql, tuple(row.values))
                    except Exception as row_error:
                        logger.error(f"FAILED on column set: {test_cols}")
                        logger.error(f"Row index: {idx}")
                        logger.error(f"Row data: {row.to_dict()}")
                        logger.error(f"Error: {row_error}")
                        logger.error(f"Transformation logic: {ingest.transform_data_types.__code__}")
                        logger.error(f"Stopping test on first failure.")
                        return
                conn.commit()
            logger.info(f"✅ Insert succeeded for columns: {test_cols}")
        except Exception as batch_error:
            logger.error(f"Batch insert failed for columns: {test_cols}")
            logger.error(f"Error: {batch_error}")
            return
    logger.info("All columns inserted successfully!")

if __name__ == "__main__":
    main()
