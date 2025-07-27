"""
Debug: RAW Table Customer Name Consistency Check
Purpose: Verify each _RAW table contains only one distinct CUSTOMER NAME value
Author: Data Engineering Team  
Date: July 18, 2025

Key Checks:
- Distinct CUSTOMER NAME values per RAW table
- Canonical mapping for each customer name
- Data consistency validation
"""
import sys
from pathlib import Path
import pandas as pd

# --- repo utils path setup ----------------------------------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import utilities
import db_helper as db
import logger_helper
from canonical_customer_manager import canonicalize_customer

def check_raw_table_customer_consistency():
    """Check each RAW table for customer name consistency"""
    logger = logger_helper.get_logger(__name__)
    
    print("\n" + "="*80)
    print("🔍 RAW TABLE CUSTOMER NAME CONSISTENCY CHECK")
    print("="*80)
    
    # Get all RAW tables
    raw_tables_query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
        ORDER BY TABLE_NAME
    """
    
    try:
        raw_tables_df = db.run_query(raw_tables_query, 'orders')
        
        if raw_tables_df.empty:
            print("❌ No RAW tables found!")
            return
        
        print(f"📊 Found {len(raw_tables_df)} RAW tables")
        print()
        
        overall_summary = []
        issues_found = []
        
        # Check each RAW table
        for idx, row in raw_tables_df.iterrows():
            table_name = row['TABLE_NAME']
            customer_code = table_name.replace('_ORDER_LIST_RAW', '').replace('x', '')
            
            print(f"📋 TABLE {idx+1}/{len(raw_tables_df)}: {table_name}")
            print(f"   Customer Code: {customer_code}")
            
            # Get distinct CUSTOMER NAME values from this table
            customer_query = f"""
                SELECT 
                    [CUSTOMER NAME],
                    COUNT(*) as record_count
                FROM [dbo].[{table_name}]
                WHERE [CUSTOMER NAME] IS NOT NULL
                GROUP BY [CUSTOMER NAME]
                ORDER BY COUNT(*) DESC
            """
            
            try:
                customer_df = db.run_query(customer_query, 'orders')
                
                if customer_df.empty:
                    print("   ⚠️  No CUSTOMER NAME data found")
                    issues_found.append(f"{table_name}: No customer data")
                    continue
                
                distinct_customers = len(customer_df)
                total_records = customer_df['record_count'].sum()
                
                print(f"   📈 Total Records: {total_records:,}")
                print(f"   🎯 Distinct Customer Names: {distinct_customers}")
                
                # Show all customer names in this table
                print("   📝 Customer Names Found:")
                for _, cust_row in customer_df.iterrows():
                    customer_name = cust_row['CUSTOMER NAME']
                    count = cust_row['record_count']
                    
                    # Get canonical mapping
                    canonical_name = canonicalize_customer(customer_name, 'master_order_list')
                    
                    print(f"      '{customer_name}' → '{canonical_name}' ({count:,} records)")
                
                # Check for consistency issues
                if distinct_customers > 1:
                    print(f"   ❌ INCONSISTENCY: {distinct_customers} different customer names in one table!")
                    issues_found.append(f"{table_name}: {distinct_customers} different names")
                else:
                    print("   ✅ CONSISTENT: Single customer name")
                
                # Store summary
                primary_customer = customer_df.iloc[0]['CUSTOMER NAME']
                canonical_customer = canonicalize_customer(primary_customer, 'master_order_list')
                
                overall_summary.append({
                    'table_name': table_name,
                    'customer_code': customer_code,
                    'raw_customer_name': primary_customer,
                    'canonical_customer_name': canonical_customer,
                    'distinct_names': distinct_customers,
                    'total_records': total_records,
                    'is_consistent': distinct_customers == 1
                })
                
            except Exception as e:
                print(f"   ❌ Error checking {table_name}: {e}")
                issues_found.append(f"{table_name}: Query error - {e}")
            
            print()
        
        # Overall Summary
        print("="*80)
        print("📊 OVERALL SUMMARY")
        print("="*80)
        
        if overall_summary:
            summary_df = pd.DataFrame(overall_summary)
            
            consistent_tables = summary_df[summary_df['is_consistent']].shape[0]
            inconsistent_tables = summary_df[~summary_df['is_consistent']].shape[0]
            
            print(f"✅ Consistent Tables: {consistent_tables}")
            print(f"❌ Inconsistent Tables: {inconsistent_tables}")
            print(f"📈 Total Records Across All Tables: {summary_df['total_records'].sum():,}")
            print()
            
            # Show canonical mapping summary
            print("🗂️  CANONICAL MAPPING SUMMARY:")
            canonical_groups = summary_df.groupby('canonical_customer_name').agg({
                'table_name': 'count',
                'total_records': 'sum',
                'raw_customer_name': lambda x: list(set(x))
            }).sort_values('total_records', ascending=False)
            
            for canonical_name, group in canonical_groups.iterrows():
                table_count = group['table_name']
                total_records = group['total_records']
                raw_names = group['raw_customer_name']
                
                print(f"   📋 '{canonical_name}':")
                print(f"      Tables: {table_count}")
                print(f"      Records: {total_records:,}")
                print(f"      Raw Names: {raw_names}")
            
            # Show any inconsistent tables in detail
            if inconsistent_tables > 0:
                print("\n❌ INCONSISTENT TABLES DETAIL:")
                inconsistent_df = summary_df[~summary_df['is_consistent']]
                for _, row in inconsistent_df.iterrows():
                    print(f"   {row['table_name']}: {row['distinct_names']} different names")
        
        # Show issues
        if issues_found:
            print("\n🚨 ISSUES FOUND:")
            for issue in issues_found:
                print(f"   ❌ {issue}")
        else:
            print("\n✅ NO MAJOR ISSUES FOUND")
        
        print("\n" + "="*80)
        print("✅ RAW TABLE CUSTOMER CONSISTENCY CHECK COMPLETE")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Overall check failed: {e}")
        print(f"❌ Overall check failed: {e}")

if __name__ == "__main__":
    check_raw_table_customer_consistency()
