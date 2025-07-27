"""
Test Canonical Customer Mapping Coverage
========================================

Validate that every distinct CUSTOMER NAME from RAW tables has a proper canonical mapping.
This test checks for gaps in our canonical customer YAML configuration.
"""

import sys
from pathlib import Path
import pandas as pd

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
from canonical_customer_manager import canonicalize_customer

def test_canonical_mapping_coverage():
    """Test that all RAW table customer names have canonical mappings"""
    
    logger = logger_helper.get_logger(__name__)
    
    print("\n" + "="*80)
    print("🧪 CANONICAL CUSTOMER MAPPING COVERAGE TEST")
    print("="*80)
    
    # Get all distinct customer names from RAW tables
    print("📊 Collecting all distinct customer names from RAW tables...")
    
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
        
        print(f"Found {len(raw_tables_df)} RAW tables")
        
        # Collect ALL distinct customer names
        all_customer_names = set()
        customer_name_details = []
        
        for idx, row in raw_tables_df.iterrows():
            table_name = row['TABLE_NAME']
            
            # Get distinct customer names from this table
            customer_query = f"""
                SELECT DISTINCT [CUSTOMER NAME] as customer_name
                FROM [dbo].[{table_name}]
                WHERE [CUSTOMER NAME] IS NOT NULL
                AND LTRIM(RTRIM([CUSTOMER NAME])) != ''
            """
            
            try:
                customer_df = db.run_query(customer_query, 'orders')
                
                for _, cust_row in customer_df.iterrows():
                    customer_name = cust_row['customer_name']
                    all_customer_names.add(customer_name)
                    customer_name_details.append({
                        'table_name': table_name,
                        'customer_name': customer_name
                    })
                    
            except Exception as e:
                print(f"❌ Error reading {table_name}: {e}")
        
        print(f"📋 Found {len(all_customer_names)} distinct customer names across all RAW tables")
        print()
        
        # Test canonical mapping for each customer name
        print("🧪 Testing canonical mappings for all customer names...")
        print("-" * 60)
        
        mapping_results = []
        successful_mappings = 0
        failed_mappings = 0
        
        for customer_name in sorted(all_customer_names):
            try:
                # Test canonical mapping
                canonical_name = canonicalize_customer(customer_name, 'master_order_list')
                
                # Check if mapping was successful (not just returning the original)
                mapping_successful = canonical_name != customer_name or customer_name in ['EQUINOX', 'RHONE', 'NOBULL']  # Some may legitimately map to themselves
                
                if canonical_name and canonical_name.strip():
                    print(f"✅ '{customer_name}' → '{canonical_name}'")
                    mapping_results.append({
                        'customer_name': customer_name,
                        'canonical_name': canonical_name,
                        'mapping_status': 'SUCCESS',
                        'is_identical': customer_name == canonical_name
                    })
                    successful_mappings += 1
                else:
                    print(f"❌ '{customer_name}' → EMPTY/NULL")
                    mapping_results.append({
                        'customer_name': customer_name,
                        'canonical_name': canonical_name,
                        'mapping_status': 'EMPTY_RESULT',
                        'is_identical': False
                    })
                    failed_mappings += 1
                    
            except Exception as e:
                print(f"❌ '{customer_name}' → ERROR: {e}")
                mapping_results.append({
                    'customer_name': customer_name,
                    'canonical_name': None,
                    'mapping_status': 'ERROR',
                    'error': str(e),
                    'is_identical': False
                })
                failed_mappings += 1
        
        print()
        print("="*80)
        print("📊 MAPPING COVERAGE SUMMARY")
        print("="*80)
        print(f"✅ Successful Mappings: {successful_mappings}")
        print(f"❌ Failed Mappings: {failed_mappings}")
        print(f"📈 Success Rate: {(successful_mappings / len(all_customer_names) * 100):.1f}%")
        print()
        
        # Show failed mappings in detail
        if failed_mappings > 0:
            print("🚨 FAILED MAPPINGS DETAIL:")
            print("-" * 40)
            
            failed_results = [r for r in mapping_results if r['mapping_status'] != 'SUCCESS']
            
            for result in failed_results:
                customer_name = result['customer_name']
                status = result['mapping_status']
                
                if status == 'ERROR':
                    error = result.get('error', 'Unknown error')
                    print(f"❌ '{customer_name}': {error}")
                elif status == 'EMPTY_RESULT':
                    print(f"❌ '{customer_name}': Returns empty/null canonical name")
            
            print()
            print("💡 RECOMMENDED ACTIONS:")
            print("1. Add missing customer mappings to canonical_customers.yaml")
            print("2. Check for typos or special characters in customer names")
            print("3. Verify canonical customer manager is loading YAML correctly")
        
        # Show identical mappings (might be legitimate)
        identical_mappings = [r for r in mapping_results if r.get('is_identical', False) and r['mapping_status'] == 'SUCCESS']
        if identical_mappings:
            print(f"ℹ️  IDENTICAL MAPPINGS ({len(identical_mappings)}):")
            print("   (These customers map to themselves - verify if intentional)")
            for result in identical_mappings:
                print(f"   • '{result['customer_name']}'")
        
        # Test specific ORDER_LIST blank issue
        print()
        print("="*80)
        print("🔍 CHECKING ORDER_LIST TABLE FOR BLANK CUSTOMER NAMES")
        print("="*80)
        
        blank_check_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN [CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = '' THEN 1 END) as blank_customer_names,
                COUNT(CASE WHEN [SOURCE_CUSTOMER_NAME] IS NULL OR LTRIM(RTRIM([SOURCE_CUSTOMER_NAME])) = '' THEN 1 END) as blank_source_names
            FROM [dbo].[ORDER_LIST]
        """
        
        try:
            blank_df = db.run_query(blank_check_query, 'orders')
            
            if not blank_df.empty:
                total = blank_df.iloc[0]['total_records']
                blank_customers = blank_df.iloc[0]['blank_customer_names']
                blank_sources = blank_df.iloc[0]['blank_source_names']
                
                print(f"📊 ORDER_LIST Analysis:")
                print(f"   Total Records: {total:,}")
                print(f"   Blank CUSTOMER NAME: {blank_customers:,} ({(blank_customers/total*100):.1f}%)")
                print(f"   Blank SOURCE_CUSTOMER_NAME: {blank_sources:,} ({(blank_sources/total*100):.1f}%)")
                
                if blank_customers > 0:
                    print(f"\n🚨 FOUND {blank_customers:,} BLANK CUSTOMER NAMES IN ORDER_LIST!")
                    print("   This confirms there are mapping issues in the transform logic.")
                    
                    # Sample blank records
                    sample_query = """
                        SELECT TOP 10 
                            [AAG ORDER NUMBER],
                            [CUSTOMER NAME],
                            [SOURCE_CUSTOMER_NAME],
                            [_SOURCE_TABLE]
                        FROM [dbo].[ORDER_LIST]
                        WHERE [CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = ''
                    """
                    
                    sample_df = db.run_query(sample_query, 'orders')
                    if not sample_df.empty:
                        print("\n📋 SAMPLE BLANK RECORDS:")
                        print(sample_df.to_string(index=False))
                
                else:
                    print("\n✅ No blank customer names found in ORDER_LIST")
            
        except Exception as e:
            print(f"❌ Error checking ORDER_LIST: {e}")
        
        print("\n" + "="*80)
        print("✅ CANONICAL MAPPING COVERAGE TEST COMPLETE")
        print("="*80)
        
        return {
            'total_customer_names': len(all_customer_names),
            'successful_mappings': successful_mappings,
            'failed_mappings': failed_mappings,
            'success_rate': successful_mappings / len(all_customer_names) * 100,
            'mapping_results': mapping_results
        }
        
    except Exception as e:
        logger.error(f"Coverage test failed: {e}")
        print(f"❌ Coverage test failed: {e}")
        return None

if __name__ == "__main__":
    test_canonical_mapping_coverage()
