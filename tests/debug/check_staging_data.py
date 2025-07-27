#!/usr/bin/env python3
"""
Check staging table data to see what's actually there
"""
import sys
from pathlib import Path

# Add utils to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import pandas as pd

def main():
    # Check what's actually in the staging table
    query = """
    SELECT TOP 5 
        stg_id, 
        [CUSTOMER], 
        [AAG ORDER NUMBER], 
        [STYLE], 
        [COLOR], 
        [DELIVERY TERMS],
        [PATTERN ID],
        [TRIM STATUS],
        [PACKED QTY],
        [NOTES],
        stg_status,
        stg_monday_item_id,
        LEN(stg_api_payload) as payload_length
    FROM [dbo].[STG_MON_CustMasterSchedule] 
    ORDER BY stg_created_date DESC
    """

    try:
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
            print("STAGING TABLE DATA:")
            print("===================")
            for col in df.columns:
                if len(df) > 0:
                    val = df[col].iloc[0]
                    print(f"  {col}: {val}")
                else:
                    print(f"  {col}: No data")
            
            print(f"\nTotal rows: {len(df)}")
            
            if len(df) > 0:
                print(f"\nStatus analysis:")
                print(f"  Latest stg_status: {df['stg_status'].iloc[0]}")
                print(f"  Latest stg_monday_item_id: {df['stg_monday_item_id'].iloc[0]}")
                print(f"  Payload length: {df['payload_length'].iloc[0]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
