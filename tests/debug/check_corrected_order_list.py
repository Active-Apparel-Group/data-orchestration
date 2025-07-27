"""
Check ORDER_LIST After Corrected Transform
==========================================

Validate the corrected ORDER_LIST table to check for:
1. NULL values in CUSTOMER NAME column
2. Proper canonical mapping
3. Correct SOURCE_CUSTOMER_NAME values
"""

import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper

def check_corrected_order_list():
    """Check ORDER_LIST table after corrected transform"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("🔍 CHECKING CORRECTED ORDER_LIST TABLE")
    print("=" * 60)
    
    try:
        # 1. Check for NULL CUSTOMER NAME values
        null_check_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN [CUSTOMER NAME] IS NULL THEN 1 END) as null_customer_names,
                COUNT(CASE WHEN [SOURCE_CUSTOMER_NAME] IS NULL THEN 1 END) as null_source_customer_names,
                COUNT(CASE WHEN [CUSTOMER NAME] = '' THEN 1 END) as empty_customer_names,
                COUNT(CASE WHEN [SOURCE_CUSTOMER_NAME] = '' THEN 1 END) as empty_source_customer_names
            FROM [dbo].[ORDER_LIST]
        """
        
        null_df = db.run_query(null_check_query, 'orders')
        
        if not null_df.empty:
            row = null_df.iloc[0]
            total = row['total_records']
            null_customer = row['null_customer_names']
            null_source = row['null_source_customer_names']
            empty_customer = row['empty_customer_names']
            empty_source = row['empty_source_customer_names']
            
            print(f"📊 OVERALL STATISTICS:")
            print(f"   Total Records: {total:,}")
            print(f"   NULL CUSTOMER NAME: {null_customer:,} ({(null_customer/total*100):.2f}%)")
            print(f"   NULL SOURCE_CUSTOMER_NAME: {null_source:,} ({(null_source/total*100):.2f}%)")
            print(f"   Empty CUSTOMER NAME: {empty_customer:,}")
            print(f"   Empty SOURCE_CUSTOMER_NAME: {empty_source:,}")
            print()
            
            if null_customer > 0:
                print(f"❌ ISSUE: {null_customer:,} records have NULL CUSTOMER NAME")
            else:
                print("✅ NO NULL CUSTOMER NAME values found")
            
            if null_source > 0:
                print(f"❌ ISSUE: {null_source:,} records have NULL SOURCE_CUSTOMER_NAME")
            else:
                print("✅ NO NULL SOURCE_CUSTOMER_NAME values found")
        
        print()
        
        # 2. Sample canonical mappings to verify correctness
        sample_query = """
            SELECT TOP 20
                [CUSTOMER NAME],
                [SOURCE_CUSTOMER_NAME],
                [_SOURCE_TABLE],
                COUNT(*) as record_count
            FROM [dbo].[ORDER_LIST]
            WHERE [CUSTOMER NAME] IS NOT NULL AND [SOURCE_CUSTOMER_NAME] IS NOT NULL
            GROUP BY [CUSTOMER NAME], [SOURCE_CUSTOMER_NAME], [_SOURCE_TABLE]
            ORDER BY COUNT(*) DESC
        """
        
        sample_df = db.run_query(sample_query, 'orders')
        
        print("📋 SAMPLE CANONICAL MAPPINGS (Top 20):")
        print("=" * 60)
        if not sample_df.empty:
            for _, row in sample_df.iterrows():
                customer_name = row['CUSTOMER NAME']
                source_name = row['SOURCE_CUSTOMER_NAME']
                source_table = row['_SOURCE_TABLE']
                count = row['record_count']
                
                print(f"   {source_table}:")
                print(f"      CUSTOMER NAME: '{customer_name}'")
                print(f"      SOURCE_CUSTOMER_NAME: '{source_name}'")
                print(f"      Records: {count:,}")
                print()
        
        # 3. Check specific problematic cases (LORNA JANE, RHYTHM, etc.)
        print("🔍 CHECKING PROBLEMATIC CASES:")
        print("=" * 40)
        
        problematic_query = """
            SELECT 
                [CUSTOMER NAME],
                [SOURCE_CUSTOMER_NAME],
                [_SOURCE_TABLE],
                COUNT(*) as record_count
            FROM [dbo].[ORDER_LIST]
            WHERE [_SOURCE_TABLE] IN (
                'xLORNA_JANE_ORDER_LIST_RAW',
                'xRHYTHM_ORDER_LIST_RAW', 
                'xSUN_DAY_RED_ORDER_LIST_RAW',
                'xWHITE_FOX_ORDER_LIST_RAW',
                'xGREYSON_ORDER_LIST_RAW'
            )
            GROUP BY [CUSTOMER NAME], [SOURCE_CUSTOMER_NAME], [_SOURCE_TABLE]
            ORDER BY [_SOURCE_TABLE], COUNT(*) DESC
        """
        
        prob_df = db.run_query(problematic_query, 'orders')
        
        if not prob_df.empty:
            for _, row in prob_df.iterrows():
                customer_name = row['CUSTOMER NAME']
                source_name = row['SOURCE_CUSTOMER_NAME']
                source_table = row['_SOURCE_TABLE']
                count = row['record_count']
                
                print(f"   {source_table}:")
                print(f"      CUSTOMER NAME: '{customer_name}'")
                print(f"      SOURCE_CUSTOMER_NAME: '{source_name}'")
                print(f"      Records: {count:,}")
        else:
            print("   No data found for test cases")
        
        print()
        
        # 4. Verify the logic is correct (no more backwards mapping)
        print("✅ VALIDATION COMPLETE")
        print("Expected Logic (CORRECTED):")
        print("   CUSTOMER NAME = Canonical name (e.g., 'WHITE FOX', 'GREYSON')")
        print("   SOURCE_CUSTOMER_NAME = Table identifier (e.g., 'WHITE FOX', 'GREYSON')")
        print()
        print("If you see NULL values, we need to investigate further!")
        
    except Exception as e:
        logger.error(f"Check failed: {e}")
        print(f"❌ Check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_corrected_order_list()
