#!/usr/bin/env python3
"""
Verify the data types in the production database
"""
import sys
sys.path.insert(0, r'C:\Users\AUKALATC01\GitHub\data-orchestration\data-orchestration\utils')
import db_helper as db

def verify_database_types():
    # First, check what columns exist
    columns_query = """
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'MON_Customer_Master_Schedule'
    ORDER BY ORDINAL_POSITION
    """
    
    columns_result = db.run_query(columns_query, 'orders')
    print('Columns in MON_Customer_Master_Schedule table:')
    for _, row in columns_result.iterrows():
        print(f'  {row["COLUMN_NAME"]} ({row["DATA_TYPE"]})')
    
    print('\n' + '='*50)
    
    # Then get sample data from key columns
    result = db.run_query('SELECT TOP 3 [Item ID], [CUSTOMER PRICE], [FINAL FOB (USD)] FROM MON_Customer_Master_Schedule', 'orders')
    print('Sample data from production table:')
    
    for i, (_, row) in enumerate(result.iterrows()):
        print(f'Record {i+1}:')
        print(f'  Item ID: {row["Item ID"]} (type: {type(row["Item ID"])})')
        print(f'  Customer Price: {row["CUSTOMER PRICE"]} (type: {type(row["CUSTOMER PRICE"])})')
        print(f'  Final FOB: {row["FINAL FOB (USD)"]} (type: {type(row["FINAL FOB (USD)"])})')
        print('---')

if __name__ == "__main__":
    verify_database_types()
