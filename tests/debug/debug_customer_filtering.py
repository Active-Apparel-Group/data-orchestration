"""
Debug Script: Customer Filtering Analysis
=========================================

Test script to debug customer filtering for order processing.
Analyzes customer data and specifically checks for GREYSON with PO 4755.

Location: tests/debug/debug_customer_filtering.py
"""

import sys
from pathlib import Path

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

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper
import pandas as pd

def debug_customer_filtering():
    """Debug customer filtering and analyze GREYSON PO 4755 data"""
    
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting customer filtering debug analysis")
    
    print("🔍 CUSTOMER FILTERING DEBUG ANALYSIS")
    print("=" * 50)
    
    try:
        with db.get_connection('ORDERS') as conn:
            # First, see all customers and their record counts
            logger.info("Querying customer summary data")
            
            df1 = pd.read_sql("""
            SELECT 
                [CUSTOMER NAME],
                COUNT(*) as total_records,
                COUNT(CASE WHEN [PO NUMBER] = '4755' THEN 1 END) as po_4755_records
            FROM [dbo].[ORDERS_UNIFIED]
            WHERE [CUSTOMER NAME] IS NOT NULL
            GROUP BY [CUSTOMER NAME]
            ORDER BY total_records DESC
            """, conn)
            
            print("\n📊 ALL CUSTOMERS IN ORDERS_UNIFIED:")
            print("-" * 60)
            print(df1.to_string())
            print()
            
            # Specifically check for GREYSON with PO 4755
            logger.info("Querying GREYSON PO 4755 specific data")
            
            df2 = pd.read_sql("""
            SELECT TOP 5
                [CUSTOMER NAME],
                [PO NUMBER],
                [AAG ORDER NUMBER],
                [CUSTOMER STYLE],
                [CUSTOMER COLOUR DESCRIPTION]
            FROM [dbo].[ORDERS_UNIFIED]
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                AND [PO NUMBER] = '4755'
            """, conn)
            
            print("🎯 GREYSON RECORDS WITH PO 4755:")
            print("-" * 40)
            if not df2.empty:
                print(df2.to_string())
            else:
                print("❌ No records found for GREYSON with PO 4755")
            print()
            
            # Check exact customer name variations
            logger.info("Analyzing customer name variations")
            
            df3 = pd.read_sql("""
            SELECT DISTINCT [CUSTOMER NAME]
            FROM [dbo].[ORDERS_UNIFIED]
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
            """, conn)
            
            print("🏷️  ALL GREYSON CUSTOMER NAME VARIATIONS:")
            print("-" * 45)
            for name in df3['CUSTOMER NAME']:
                print(f"  '{name}'")
            
            # Additional analysis - check PO number patterns
            df4 = pd.read_sql("""
            SELECT DISTINCT [PO NUMBER]
            FROM [dbo].[ORDERS_UNIFIED]
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                AND [PO NUMBER] IS NOT NULL
            ORDER BY [PO NUMBER]
            """, conn)
            
            print(f"\n📋 ALL PO NUMBERS FOR GREYSON CUSTOMERS:")
            print("-" * 45)
            for po in df4['PO NUMBER']:
                print(f"  '{po}'")
            
            logger.info("Customer filtering debug analysis completed")
            
    except Exception as e:
        logger.error(f"Debug analysis failed: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_customer_filtering()
