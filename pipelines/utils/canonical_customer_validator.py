"""
Canonical Customer Validator Utility
Purpose: Validate customer name mappings against YAML configuration
Location: utils/canonical_customer_validator.py

Utility for validating that all customer names from source systems 
have proper canonical mappings defined in canonical_customers.yaml
"""
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List

# Standard import pattern for pipelines
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper

def validate_canonical_mapping_coverage(db_key: str = 'orders', source_table_pattern: str = 'x%_ORDER_LIST_RAW') -> Dict[str, Any]:
    """
    Validate that all customer names from source tables have canonical mappings
    
    Args:
        db_key: Database connection key
        source_table_pattern: SQL pattern to match source tables
        
    Returns:
        Dictionary with validation results and statistics
    """
    logger = logger_helper.get_logger(__name__)
    
    print("\n" + "="*80)
    print("🧪 CANONICAL CUSTOMER MAPPING COVERAGE VALIDATION")
    print("="*80)
    
    # Import canonical customer manager
    try:
        sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
        from canonical_customer_manager import canonicalize_customer
    except ImportError as e:
        print(f"❌ Failed to import canonical customer manager: {e}")
        return {'success': False, 'error': str(e)}
    
    # Get all source tables
    print(f"📊 Collecting customer names from tables matching: {source_table_pattern}")
    
    tables_query = f"""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME LIKE '{source_table_pattern}'
        ORDER BY TABLE_NAME
    """
    
    try:
        tables_df = db.run_query(tables_query, db_key)
        
        if tables_df.empty:
            print("❌ No source tables found!")
            return {'success': False, 'error': 'No source tables found'}
        
        print(f"Found {len(tables_df)} source tables")
        
        # Collect all distinct customer names
        all_customer_names = set()
        customer_details = []
        
        for _, row in tables_df.iterrows():
            table_name = row['TABLE_NAME']
            
            customer_query = f"""
                SELECT DISTINCT [CUSTOMER NAME] as customer_name
                FROM [dbo].[{table_name}]
                WHERE [CUSTOMER NAME] IS NOT NULL
                AND LTRIM(RTRIM([CUSTOMER NAME])) != ''
            """
            
            try:
                customer_df = db.run_query(customer_query, db_key)
                
                for _, cust_row in customer_df.iterrows():
                    customer_name = cust_row['customer_name']
                    all_customer_names.add(customer_name)
                    customer_details.append({
                        'table_name': table_name,
                        'customer_name': customer_name
                    })
                    
            except Exception as e:
                print(f"❌ Error reading {table_name}: {e}")
        
        print(f"📋 Found {len(all_customer_names)} distinct customer names")
        print()
        
        # Test canonical mappings
        print("🧪 Validating canonical mappings...")
        print("-" * 60)
        
        mapping_results = []
        successful_mappings = 0
        failed_mappings = 0
        
        for customer_name in sorted(all_customer_names):
            try:
                canonical_name = canonicalize_customer(customer_name, 'master_order_list')
                
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
        
        # Generate summary
        success_rate = (successful_mappings / len(all_customer_names) * 100) if all_customer_names else 0
        
        print()
        print("="*80)
        print("📊 VALIDATION SUMMARY")
        print("="*80)
        print(f"✅ Successful Mappings: {successful_mappings}")
        print(f"❌ Failed Mappings: {failed_mappings}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Show failed mappings
        failed_results = [r for r in mapping_results if r['mapping_status'] != 'SUCCESS']
        if failed_results:
            print(f"\n🚨 FAILED MAPPINGS ({len(failed_results)}):")
            for result in failed_results:
                customer_name = result['customer_name']
                status = result['mapping_status']
                if status == 'ERROR':
                    error = result.get('error', 'Unknown error')
                    print(f"   ❌ '{customer_name}': {error}")
                else:
                    print(f"   ❌ '{customer_name}': {status}")
        
        # Show identical mappings
        identical_mappings = [r for r in mapping_results if r.get('is_identical', False) and r['mapping_status'] == 'SUCCESS']
        if identical_mappings:
            print(f"\nℹ️  IDENTICAL MAPPINGS ({len(identical_mappings)}):")
            for result in identical_mappings:
                print(f"   • '{result['customer_name']}'")
        
        return {
            'success': True,
            'total_customer_names': len(all_customer_names),
            'successful_mappings': successful_mappings,
            'failed_mappings': failed_mappings,
            'success_rate': success_rate,
            'mapping_results': mapping_results,
            'failed_customers': [r['customer_name'] for r in failed_results],
            'identical_mappings': [r['customer_name'] for r in identical_mappings]
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        return {'success': False, 'error': str(e)}


def validate_order_list_customer_completeness(db_key: str = 'orders') -> Dict[str, Any]:
    """
    Check ORDER_LIST table for blank customer names
    
    Args:
        db_key: Database connection key
        
    Returns:
        Dictionary with completeness analysis
    """
    print("\n" + "="*80)
    print("🔍 ORDER_LIST CUSTOMER COMPLETENESS CHECK")
    print("="*80)
    
    blank_check_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN [CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = '' THEN 1 END) as blank_customer_names,
            COUNT(CASE WHEN [SOURCE_CUSTOMER_NAME] IS NULL OR LTRIM(RTRIM([SOURCE_CUSTOMER_NAME])) = '' THEN 1 END) as blank_source_names
        FROM [dbo].[ORDER_LIST]
    """
    
    try:
        result_df = db.run_query(blank_check_query, db_key)
        
        if result_df.empty:
            return {'success': False, 'error': 'No data in ORDER_LIST table'}
        
        total = result_df.iloc[0]['total_records']
        blank_customers = result_df.iloc[0]['blank_customer_names']
        blank_sources = result_df.iloc[0]['blank_source_names']
        
        print(f"📊 ORDER_LIST Analysis:")
        print(f"   Total Records: {total:,}")
        print(f"   Blank CUSTOMER NAME: {blank_customers:,} ({(blank_customers/total*100):.1f}%)")
        print(f"   Blank SOURCE_CUSTOMER_NAME: {blank_sources:,} ({(blank_sources/total*100):.1f}%)")
        
        completeness_rate = ((total - blank_customers) / total * 100) if total > 0 else 0
        
        if blank_customers > 0:
            print(f"\n🚨 FOUND {blank_customers:,} BLANK CUSTOMER NAMES!")
            
            # Get sample blank records
            sample_query = """
                SELECT TOP 10 
                    [AAG ORDER NUMBER],
                    [CUSTOMER NAME],
                    [SOURCE_CUSTOMER_NAME],
                    [_SOURCE_TABLE]
                FROM [dbo].[ORDER_LIST]
                WHERE [CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = ''
            """
            
            sample_df = db.run_query(sample_query, db_key)
            if not sample_df.empty:
                print("\n📋 SAMPLE BLANK RECORDS:")
                print(sample_df.to_string(index=False))
        else:
            print("\n✅ No blank customer names found")
        
        return {
            'success': True,
            'total_records': total,
            'blank_customer_names': blank_customers,
            'blank_source_names': blank_sources,
            'customer_completeness_rate': completeness_rate,
            'has_blank_customers': blank_customers > 0
        }
        
    except Exception as e:
        print(f"❌ Error checking ORDER_LIST: {e}")
        return {'success': False, 'error': str(e)}


def run_complete_validation(db_key: str = 'orders') -> Dict[str, Any]:
    """
    Run complete canonical customer validation
    
    Args:
        db_key: Database connection key
        
    Returns:
        Complete validation results
    """
    print("🚀 STARTING COMPLETE CANONICAL CUSTOMER VALIDATION")
    
    # Run mapping coverage validation
    coverage_results = validate_canonical_mapping_coverage(db_key)
    
    # Run ORDER_LIST completeness check
    completeness_results = validate_order_list_customer_completeness(db_key)
    
    # Generate final report
    print("\n" + "="*80)
    print("✅ COMPLETE VALIDATION FINISHED")
    print("="*80)
    
    return {
        'coverage_validation': coverage_results,
        'completeness_validation': completeness_results,
        'overall_success': coverage_results.get('success', False) and completeness_results.get('success', False)
    }


if __name__ == "__main__":
    # Run complete validation when executed directly
    results = run_complete_validation()
    
    if results['overall_success']:
        print("✅ All validations passed!")
        exit(0)
    else:
        print("❌ Some validations failed!")
        exit(1)
