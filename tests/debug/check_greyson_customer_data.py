"""
Debug Script: Check GREYSON Customer Data in ORDERS_UNIFIED
Purpose: Investigate the exact customer names and data structure for GREYSON
"""
import sys
from pathlib import Path
import pandas as pd

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

# Import from utils/
import db_helper as db
import logger_helper

def main():
    """Main function to check GREYSON customer data"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting GREYSON customer data investigation")
    
    try:
        # Use appropriate database from config.yaml
        with db.get_connection('orders') as conn:
            
            # 1. Check all customers that contain GREYSON
            print("=" * 60)
            print("1. CHECKING ALL CUSTOMERS CONTAINING 'GREYSON'")
            print("=" * 60)
            
            sql1 = """
            SELECT DISTINCT CUSTOMER 
            FROM ORDERS_UNIFIED 
            WHERE CUSTOMER LIKE '%GREYSON%'
            ORDER BY CUSTOMER
            """
            df1 = pd.read_sql(sql1, conn)
            print(f"Found {len(df1)} unique GREYSON customers:")
            for customer in df1['CUSTOMER'].tolist():
                print(f"  - '{customer}'")
            
            # 2. Check specific record counts
            print("\n" + "=" * 60)
            print("2. RECORD COUNTS BY GREYSON CUSTOMER")
            print("=" * 60)
            
            sql2 = """
            SELECT CUSTOMER, COUNT(*) as record_count
            FROM ORDERS_UNIFIED 
            WHERE CUSTOMER LIKE '%GREYSON%'
            GROUP BY CUSTOMER
            ORDER BY record_count DESC
            """
            df2 = pd.read_sql(sql2, conn)
            print("Record counts:")
            for _, row in df2.iterrows():
                print(f"  - {row['CUSTOMER']}: {row['record_count']} records")
            
            # 3. Check for PO 4755 specifically
            print("\n" + "=" * 60)
            print("3. CHECKING FOR PO 4755 IN GREYSON DATA")
            print("=" * 60)
            
            sql3 = """
            SELECT CUSTOMER, PO_NUMBER, COUNT(*) as record_count
            FROM ORDERS_UNIFIED 
            WHERE CUSTOMER LIKE '%GREYSON%' 
            AND PO_NUMBER LIKE '%4755%'
            GROUP BY CUSTOMER, PO_NUMBER
            ORDER BY record_count DESC
            """
            df3 = pd.read_sql(sql3, conn)
            
            if len(df3) > 0:
                print("Found PO 4755 records:")
                for _, row in df3.iterrows():
                    print(f"  - Customer: '{row['CUSTOMER']}', PO: '{row['PO_NUMBER']}', Records: {row['record_count']}")
            else:
                print("No records found for PO 4755 in GREYSON data")
            
            # 4. Sample data structure
            print("\n" + "=" * 60)
            print("4. SAMPLE DATA STRUCTURE (First GREYSON Record)")
            print("=" * 60)
            
            sql4 = """
            SELECT TOP 1 * 
            FROM ORDERS_UNIFIED 
            WHERE CUSTOMER LIKE '%GREYSON%'
            """
            df4 = pd.read_sql(sql4, conn)
            
            if len(df4) > 0:
                print("Sample record columns and values:")
                for col in df4.columns:
                    value = df4.iloc[0][col]
                    print(f"  - {col}: '{value}'")
            else:
                print("No GREYSON records found")
            
            # 5. Check all unique PO numbers for GREYSON
            print("\n" + "=" * 60)
            print("5. ALL UNIQUE PO NUMBERS FOR GREYSON")
            print("=" * 60)
            
            sql5 = """
            SELECT DISTINCT PO_NUMBER, COUNT(*) as record_count
            FROM ORDERS_UNIFIED 
            WHERE CUSTOMER LIKE '%GREYSON%'
            GROUP BY PO_NUMBER
            ORDER BY record_count DESC
            """
            df5 = pd.read_sql(sql5, conn)
            
            print(f"Found {len(df5)} unique PO numbers for GREYSON:")
            for _, row in df5.iterrows():
                print(f"  - PO: '{row['PO_NUMBER']}' ({row['record_count']} records)")
                
        logger.info("GREYSON customer data investigation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in GREYSON customer data investigation: {str(e)}")
        print(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
