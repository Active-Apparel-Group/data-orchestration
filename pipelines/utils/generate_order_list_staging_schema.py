"""
Script: generate_order_list_staging_schema.py
Purpose: Use SQLTestHelper to extract ORDER_LIST DDL and generate ORDER_LIST_STAGING schema
Location: dev/order-staging/generate_order_list_staging_schema.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))
import db_helper as db
import logger_helper
from sql_test_helper import SQLTestHelper
import pandas as pd

def main():
    logger = logger_helper.get_logger(__name__)
    tester = SQLTestHelper(database_name='orders')
    
    # Query column info for ORDER_LIST
    ddl_query = '''
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ORDER_LIST'
    ORDER BY ORDINAL_POSITION
    '''
    result = tester.test_query(
        query_name='Get ORDER_LIST schema',
        sql_query=ddl_query
    )
    if not result['success']:
        logger.error(f"Failed to get ORDER_LIST schema: {result['errors']}")
        return
    # Instead of data_sample, re-run the query directly to get all columns
    with db.get_connection('orders') as conn:
        df = pd.read_sql(ddl_query, conn)
    if df.empty:
        logger.error("No columns found for ORDER_LIST.")
        return
    # Build CREATE TABLE statement
    lines = ["CREATE TABLE dbo.ORDER_LIST_STAGING ("]
    for _, row in df.iterrows():
        col = row['COLUMN_NAME']
        dtype = row['DATA_TYPE']
        maxlen = row['CHARACTER_MAXIMUM_LENGTH']
        prec = row['NUMERIC_PRECISION']
        scale = row['NUMERIC_SCALE']
        nullable = row['IS_NULLABLE']
        if dtype in ('nvarchar', 'varchar', 'char', 'nchar') and maxlen:
            type_str = f"{dtype.upper()}({int(maxlen)})"
        elif dtype in ('decimal', 'numeric') and prec:
            type_str = f"{dtype.upper()}({int(prec)},{int(scale) if scale else 0})"
        else:
            type_str = dtype.upper()
        null_str = "NULL" if nullable == "YES" else "NOT NULL"
        lines.append(f"    [{col}] {type_str} {null_str},")
    lines.append("    [RAW_SOURCE_TABLE] NVARCHAR(128) NULL,")
    lines.append("    [RAW_SOURCE_FILE] NVARCHAR(256) NULL")
    lines.append(")\n;")
    schema_sql = "\n".join(lines)
    # Write to file
    out_path = Path("sql/schemas/order_list_staging_schema.sql")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("-- Auto-generated ORDER_LIST_STAGING schema (matches ORDER_LIST)\n")
        f.write(schema_sql)
    logger.info(f"ORDER_LIST_STAGING schema written to {out_path}")

if __name__ == "__main__":
    main()
