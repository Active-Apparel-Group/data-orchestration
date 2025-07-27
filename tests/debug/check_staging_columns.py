"""
Quick column check for staging tables
Purpose: Identify actual column names in staging tables
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root for imports
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

def check_staging_columns():
    """Check actual column names in staging tables"""
    
    with db.get_connection('orders') as conn:
        print("🔍 STG_MON_CustMasterSchedule_Subitems Columns:")
        columns_sql = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
        ORDER BY ORDINAL_POSITION
        """
        columns_df = pd.read_sql(columns_sql, conn)
        
        for _, row in columns_df.iterrows():
            print(f"   - {row['COLUMN_NAME']} ({row['DATA_TYPE']})")
        
        print(f"\n📊 Total columns: {len(columns_df)}")
        
        # Check if table has any data
        count_sql = "SELECT COUNT(*) as total_count FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]"
        count_df = pd.read_sql(count_sql, conn)
        print(f"📋 Total records in table: {count_df.iloc[0]['total_count']}")

if __name__ == "__main__":
    check_staging_columns()
