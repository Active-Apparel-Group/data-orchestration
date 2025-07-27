"""
Isolated Subitem Milestone Test
Purpose: Test ONLY the subitem processing milestone with quantitative validation
Location: tests/debug/test_subitem_milestone_isolated.py
"""
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, Any

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

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper

# Configure logging
logger = logger_helper.get_logger(__name__)

class SubitemMilestoneTest:
    """
    Isolated test for subitem processing milestone
    Focus: Quantitative validation of data flow
    """
    
    def __init__(self):
        self.test_results = {}
        
    def test_source_data_analysis(self) -> Dict[str, Any]:
        """
        Step 1: Analyze source data for GREYSON PO 4755
        Quantitative Focus: How many orders, how many expected subitems
        """
        print("🔍 STEP 1: SOURCE DATA ANALYSIS")
        print("-" * 40)
        
        try:
            with db.get_connection('orders') as conn:
                # Get GREYSON orders
                source_sql = """
                SELECT 
                    [AAG ORDER NUMBER],
                    [CUSTOMER NAME],
                    [PO NUMBER],
                    [CUSTOMER STYLE],
                    [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] as [COLOR],
                    [TOTAL QTY]
                FROM [dbo].[ORDERS_UNIFIED]
                WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                AND [PO NUMBER] = '4755'
                """
                source_df = pd.read_sql(source_sql, conn)
                
                # Detect size columns (same logic as integration_monday.py)
                size_columns_sql = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ORDERS_UNIFIED'
                AND ORDINAL_POSITION > (
                    SELECT ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'ORDERS_UNIFIED' AND COLUMN_NAME = 'UNIT OF MEASURE'
                )
                AND ORDINAL_POSITION < (
                    SELECT ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'ORDERS_UNIFIED' AND COLUMN_NAME = 'TOTAL QTY'
                )
                ORDER BY ORDINAL_POSITION
                """
                size_columns_df = pd.read_sql(size_columns_sql, conn)
                size_columns = size_columns_df['COLUMN_NAME'].tolist()
                
                # Calculate expected subitems by checking non-zero size values
                expected_subitems = 0
                if not source_df.empty and size_columns:
                    # Get the actual size data
                    size_data_sql = f"""
                    SELECT {', '.join([f'[{col}]' for col in size_columns])}
                    FROM [dbo].[ORDERS_UNIFIED]
                    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                    AND [PO NUMBER] = '4755'
                    """
                    size_data_df = pd.read_sql(size_data_sql, conn)
                    
                    # Count non-zero values across all size columns
                    for col in size_columns:
                        if col in size_data_df.columns:
                            non_zero_count = (pd.to_numeric(size_data_df[col], errors='coerce') > 0).sum()
                            expected_subitems += non_zero_count
            
            result = {
                'success': True,
                'total_orders': len(source_df),
                'size_columns_detected': len(size_columns),
                'expected_subitems': expected_subitems,
                'sample_orders': source_df.head(3).to_dict('records') if not source_df.empty else [],
                'size_columns_sample': size_columns[:10]
            }
            
            print(f"   📋 Total GREYSON PO 4755 orders: {result['total_orders']}")
            print(f"   📏 Size columns detected: {result['size_columns_detected']}")
            print(f"   🎯 Expected subitems: {result['expected_subitems']}")
            print(f"   📊 Success: {'✅ PASSED' if result['total_orders'] > 0 else '❌ FAILED'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Source data analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_staging_table_status(self) -> Dict[str, Any]:
        """
        Step 2: Check staging table current status
        Quantitative Focus: How many records are actually in staging
        """
        print("\n🔍 STEP 2: STAGING TABLE STATUS")
        print("-" * 40)
        
        try:
            with db.get_connection('orders') as conn:
                # Check main staging table
                main_staging_sql = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN stg_status = 'API_SUCCESS' THEN 1 END) as successful_records,
                    COUNT(CASE WHEN stg_monday_item_id IS NOT NULL THEN 1 END) as records_with_monday_id
                FROM [dbo].[STG_MON_CustMasterSchedule]
                WHERE [CUSTOMER] LIKE '%GREYSON%'
                """
                main_staging = pd.read_sql(main_staging_sql, conn)
                
                # Check subitem staging table
                subitem_staging_sql = """
                SELECT 
                    COUNT(*) as total_subitems,
                    COUNT(CASE WHEN stg_status = 'API_SUCCESS' THEN 1 END) as successful_subitems,
                    COUNT(DISTINCT [Size]) as unique_sizes,
                    SUM(CAST(ISNULL([ORDER_QTY], 0) AS DECIMAL)) as total_quantity
                FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
                WHERE [CUSTOMER] LIKE '%GREYSON%'
                """
                subitem_staging = pd.read_sql(subitem_staging_sql, conn)
                
                # Check for any recent batch activity
                batch_activity_sql = """
                SELECT TOP 5
                    batch_id,
                    customer_name,
                    status,
                    total_records,
                    successful_records,
                    start_time
                FROM [dbo].[MON_BatchProcessing]
                WHERE customer_name LIKE '%GREYSON%'
                ORDER BY start_time DESC
                """
                batch_activity = pd.read_sql(batch_activity_sql, conn)
            
            # Helper function to safely convert to int
            def safe_int(value, default=0):
                return int(value) if value is not None else default
            
            result = {
                'success': True,
                'main_staging': {
                    'total_records': safe_int(main_staging.iloc[0]['total_records'] if not main_staging.empty else 0),
                    'successful_records': safe_int(main_staging.iloc[0]['successful_records'] if not main_staging.empty else 0),
                    'records_with_monday_id': safe_int(main_staging.iloc[0]['records_with_monday_id'] if not main_staging.empty else 0)
                },
                'subitem_staging': {
                    'total_subitems': safe_int(subitem_staging.iloc[0]['total_subitems'] if not subitem_staging.empty else 0),
                    'successful_subitems': safe_int(subitem_staging.iloc[0]['successful_subitems'] if not subitem_staging.empty else 0),
                    'unique_sizes': safe_int(subitem_staging.iloc[0]['unique_sizes'] if not subitem_staging.empty else 0),
                    'total_quantity': safe_int(subitem_staging.iloc[0]['total_quantity'] if not subitem_staging.empty else 0)
                },
                'recent_batches': batch_activity.to_dict('records') if not batch_activity.empty else []
            }
            
            print(f"   📋 Main staging records: {result['main_staging']['total_records']}")
            print(f"   📏 Subitem staging records: {result['subitem_staging']['total_subitems']}")
            print(f"   🔢 Unique sizes in staging: {result['subitem_staging']['unique_sizes']}")
            print(f"   📦 Total quantity in staging: {result['subitem_staging']['total_quantity']}")
            print(f"   🕒 Recent batches: {len(result['recent_batches'])}")
            
            staging_has_data = result['subitem_staging']['total_subitems'] > 0
            print(f"   📊 Staging validation: {'✅ HAS DATA' if staging_has_data else '❌ NO DATA'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Staging table analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_uuid_table_status(self) -> Dict[str, Any]:
        """
        Step 3: Check UUID table and change detection
        Quantitative Focus: Why is change detection failing
        """
        print("\n🔍 STEP 3: UUID TABLE ANALYSIS")
        print("-" * 40)
        
        try:
            with db.get_connection('orders') as conn:
                # Check if ORDERS_UNIFIED_SNAPSHOT exists
                table_exists_sql = """
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = 'ORDERS_UNIFIED_SNAPSHOT'
                """
                table_exists = pd.read_sql(table_exists_sql, conn)
                
                if table_exists.iloc[0]['table_exists'] > 0:
                    # Table exists, check columns
                    columns_sql = """
                    SELECT COLUMN_NAME, DATA_TYPE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'ORDERS_UNIFIED_SNAPSHOT'
                    AND COLUMN_NAME LIKE '%uuid%'
                    ORDER BY ORDINAL_POSITION
                    """
                    columns_df = pd.read_sql(columns_sql, conn)
                    
                    # Check record count
                    count_sql = "SELECT COUNT(*) as total_records FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]"
                    count_df = pd.read_sql(count_sql, conn)
                    
                    result = {
                        'success': True,
                        'table_exists': True,
                        'uuid_columns': columns_df.to_dict('records'),
                        'total_records': int(count_df.iloc[0]['total_records']),
                        'has_uuid_columns': len(columns_df) > 0
                    }
                else:
                    result = {
                        'success': True,
                        'table_exists': False,
                        'uuid_columns': [],
                        'total_records': 0,
                        'has_uuid_columns': False
                    }
            
            print(f"   📋 ORDERS_UNIFIED_SNAPSHOT exists: {'✅ YES' if result['table_exists'] else '❌ NO'}")
            print(f"   🔑 UUID columns found: {len(result['uuid_columns'])}")
            print(f"   📊 Total records: {result['total_records']}")
            print(f"   🎯 Change detection ready: {'✅ YES' if result['has_uuid_columns'] else '❌ NO - Missing UUID columns'}")
            
            return result
            
        except Exception as e:
            logger.error(f"UUID table analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_api_integration_capability(self) -> Dict[str, Any]:
        """
        Step 4: Test Monday.com API integration capability
        Quantitative Focus: Can we actually make API calls
        """
        print("\n🔍 STEP 4: API INTEGRATION TEST")
        print("-" * 40)
        
        try:
            # Import Monday.com client
            sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))
            from integration_monday import MondayIntegrationClient
            
            # Test API connection
            client = MondayIntegrationClient()
            success, message = client.test_connection()
            
            result = {
                'success': success,
                'connection_message': message,
                'client_initialized': True
            }
            
            print(f"   🔗 Monday.com client initialized: ✅ YES")
            print(f"   🌐 API connection test: {'✅ PASSED' if success else '❌ FAILED'}")
            print(f"   📝 Connection message: {message}")
            
            return result
            
        except Exception as e:
            logger.error(f"API integration test failed: {e}")
            return {
                'success': False, 
                'error': str(e),
                'client_initialized': False
            }
    
    def run_isolated_subitem_test(self) -> Dict[str, Any]:
        """Run complete isolated subitem milestone test"""
        print("=" * 80)
        print("🧪 ISOLATED SUBITEM MILESTONE TEST")
        print("=" * 80)
        
        # Step 1: Source data analysis
        self.test_results['source_analysis'] = self.test_source_data_analysis()
        
        # Step 2: Staging table status
        self.test_results['staging_status'] = self.test_staging_table_status()
        
        # Step 3: UUID table analysis
        self.test_results['uuid_analysis'] = self.test_uuid_table_status()
        
        # Step 4: API integration capability
        self.test_results['api_capability'] = self.test_api_integration_capability()
        
        # Final analysis
        print("\n" + "=" * 80)
        print("📊 ISOLATED TEST SUMMARY")
        print("=" * 80)
        
        issues_found = []
        
        # Check each component
        source_ok = self.test_results['source_analysis'].get('success') and self.test_results['source_analysis'].get('total_orders', 0) > 0
        staging_ok = self.test_results['staging_status'].get('success') and self.test_results['staging_status'].get('subitem_staging', {}).get('total_subitems', 0) > 0
        uuid_ok = self.test_results['uuid_analysis'].get('success') and self.test_results['uuid_analysis'].get('has_uuid_columns', False)
        api_ok = self.test_results['api_capability'].get('success', False)
        
        print(f"Source Data: {'✅ GOOD' if source_ok else '❌ ISSUE'}")
        if not source_ok:
            issues_found.append("No source data or detection failed")
            
        print(f"Staging Data: {'✅ GOOD' if staging_ok else '❌ ISSUE'}")
        if not staging_ok:
            issues_found.append("No data in staging tables - batch processor not populating staging")
            
        print(f"UUID/Change Detection: {'✅ GOOD' if uuid_ok else '❌ ISSUE'}")
        if not uuid_ok:
            issues_found.append("ORDERS_UNIFIED_SNAPSHOT missing or no UUID columns")
            
        print(f"API Integration: {'✅ GOOD' if api_ok else '❌ ISSUE'}")
        if not api_ok:
            issues_found.append("Monday.com API connection or client issues")
        
        print(f"\n🎯 CRITICAL ISSUES FOUND: {len(issues_found)}")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        
        return {
            'overall_success': len(issues_found) == 0,
            'issues_found': issues_found,
            'component_status': {
                'source_data': source_ok,
                'staging_data': staging_ok,
                'uuid_change_detection': uuid_ok,
                'api_integration': api_ok
            },
            'detailed_results': self.test_results
        }


def main():
    """Run isolated subitem milestone test"""
    test_framework = SubitemMilestoneTest()
    results = test_framework.run_isolated_subitem_test()
    
    # Save results
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"subitem_milestone_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    main()
