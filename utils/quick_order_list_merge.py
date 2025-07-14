"""
Quick ORDER_LIST Merge Utility
- Creates dbo.swp_ORDER_LIST_MERGE (all NVARCHAR(MAX))
- Appends all x*_ORDER_LIST tables
- Infers schema and creates dbo.ORDER_LIST with correct types
- Uses schema_helper for type inference
"""
import pandas as pd
import db_helper as db
import logger_helper
import schema_helper

def merge_customer_tables():
    log = logger_helper.get_logger(__name__)
    with db.get_connection("orders") as conn:
        tbls = pd.read_sql(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME LIKE 'x%ORDER_LIST'",
            conn)['TABLE_NAME']
        if tbls.empty:
            log.warning("No customer tables found!")
            return
        # Drop temp if exists
        conn.execute("""
            IF OBJECT_ID('dbo.swp_ORDER_LIST_MERGE','U') IS NOT NULL
                DROP TABLE dbo.swp_ORDER_LIST_MERGE
        """)
        # Use columns from first table
        cols = pd.read_sql(f"SELECT TOP 0 * FROM dbo.[{tbls.iloc[0]}]", conn).columns
        create_sql = "CREATE TABLE dbo.swp_ORDER_LIST_MERGE (" + \
            ", ".join(f'[{c}] NVARCHAR(MAX)' for c in cols) + ")"
        conn.execute(create_sql)
        # Insert all rows from all tables
        for t in tbls:
            conn.execute(f"INSERT INTO dbo.swp_ORDER_LIST_MERGE SELECT * FROM dbo.[{t}]")
            log.info(f"Appended {t}")
        conn.commit()
        # Pull to pandas, infer schema, create final table
        df = pd.read_sql("SELECT * FROM dbo.swp_ORDER_LIST_MERGE", conn)
    col_sql, schema_info = schema_helper.generate_table_schema(df)
    schema_helper.recreate_and_load(df, 'ORDER_LIST', 'orders', col_sql, schema_info)
    log.info("ORDER_LIST merge complete!")
