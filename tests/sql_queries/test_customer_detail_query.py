"""
Test: Customer Detail Query
===========================

Tests the customer detail query used for specific customer analysis.
Validates query structure, filtering, and data quality.

Location: tests/sql_queries/test_customer_detail_query.py
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

# Import from utils/
import logger_helper
from sql_test_helper import create_sql_tester

def test_customer_detail_query():
    """Test the customer detail query with various filters"""
    
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing customer detail query")
    
    # Initialize SQL tester
    sql_tester = create_sql_tester('dms')
    
    # Define the customer detail query (base query without filters)
    customer_detail_query = """
    SELECT 
        ou.[CUSTOMER NAME] as CUSTOMER,
        ou.[AAG ORDER NUMBER],
        ou.[CUSTOMER STYLE] as STYLE,
        ou.[CUSTOMER COLOUR DESCRIPTION] as COLOR,
        ou.[TOTAL QTY] as ORDER_QTY,
        ou.[ORDER DATE PO RECEIVED],
        ou.[CUSTOMER SEASON],
        ou.[AAG SEASON],
        ou.[DROP],
        ou.[PO NUMBER]
    FROM [dbo].[ORDERS_UNIFIED] ou
    LEFT JOIN [dbo].[MON_CustMasterSchedule] mcs 
        ON ou.[AAG ORDER NUMBER] = mcs.[AAG ORDER NUMBER]
        AND ou.[CUSTOMER NAME] = mcs.[CUSTOMER]
        AND ou.[CUSTOMER STYLE] = mcs.[STYLE] 
        AND ou.[CUSTOMER COLOUR DESCRIPTION] = mcs.[COLOR]
    WHERE mcs.[Item ID] IS NULL  -- Not yet in Monday.com
        AND ou.[CUSTOMER NAME] IS NOT NULL
        AND ou.[AAG ORDER NUMBER] IS NOT NULL
    ORDER BY ou.[ORDER DATE PO RECEIVED] DESC, ou.[AAG ORDER NUMBER]
    """
    
    # Expected columns
    expected_columns = [
        'CUSTOMER',
        'AAG ORDER NUMBER',
        'STYLE',
        'COLOR', 
        'ORDER_QTY',
        'ORDER DATE PO RECEIVED',
        'CUSTOMER SEASON',
        'AAG SEASON',
        'DROP',
        'PO NUMBER'
    ]
    
    # Test 1: Base query without filters
    print("🔍 CUSTOMER DETAIL QUERY TEST - Base Query")
    print("=" * 60)
    
    test_result = sql_tester.test_query(
        query_name="Customer Detail - All New Orders",
        sql_query=customer_detail_query,
        expected_columns=expected_columns,
        expected_min_rows=0,
        expected_max_rows=10000  # Reasonable upper limit
    )
    
    print(f"Status: {'✅ PASSED' if test_result['success'] else '❌ FAILED'}")
    print(f"Execution Time: {test_result['execution_time']}s")
    print(f"Rows Returned: {test_result['row_count']:,}")
    print(f"Columns: {test_result['column_count']}")
    
    if test_result['errors']:
        print("\n❌ ERRORS:")
        for error in test_result['errors']:
            print(f"  - {error}")
    
    if test_result['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in test_result['warnings']:
            print(f"  - {warning}")
    
    # Test 2: Query with customer filter (if data exists)
    if test_result['row_count'] > 0:
        print("\n🔍 CUSTOMER DETAIL QUERY TEST - With Customer Filter")
        print("=" * 60)
        
        # Query with customer filter
        filtered_query = """
        SELECT 
            ou.[CUSTOMER NAME] as CUSTOMER,
            ou.[AAG ORDER NUMBER],
            ou.[CUSTOMER STYLE] as STYLE,
            ou.[CUSTOMER COLOUR DESCRIPTION] as COLOR,
            ou.[TOTAL QTY] as ORDER_QTY,
            ou.[ORDER DATE PO RECEIVED],
            ou.[CUSTOMER SEASON],
            ou.[AAG SEASON],
            ou.[DROP],
            ou.[PO NUMBER]
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] mcs 
            ON ou.[AAG ORDER NUMBER] = mcs.[AAG ORDER NUMBER]
            AND ou.[CUSTOMER NAME] = mcs.[CUSTOMER]
            AND ou.[CUSTOMER STYLE] = mcs.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = mcs.[COLOR]
        WHERE mcs.[Item ID] IS NULL  -- Not yet in Monday.com
            AND ou.[CUSTOMER NAME] = ?
        ORDER BY ou.[ORDER DATE PO RECEIVED] DESC, ou.[AAG ORDER NUMBER]
        """
        
        # Use first customer from sample data for testing
        sample_customer = None
        if test_result['data_sample']:
            sample_customer = test_result['data_sample'][0]['CUSTOMER']
        
        if sample_customer:
            filtered_result = sql_tester.test_query(
                query_name=f"Customer Detail - Filtered by '{sample_customer}'",
                sql_query=filtered_query,
                expected_columns=expected_columns,
                expected_min_rows=1,
                params=[sample_customer]
            )
            
            print(f"Status: {'✅ PASSED' if filtered_result['success'] else '❌ FAILED'}")
            print(f"Execution Time: {filtered_result['execution_time']}s")
            print(f"Rows Returned: {filtered_result['row_count']:,}")
            
            if filtered_result['errors']:
                print("\n❌ ERRORS:")
                for error in filtered_result['errors']:
                    print(f"  - {error}")
    
    # Test 3: Data quality validation
    if test_result['success'] and test_result['row_count'] > 0:
        print("\n🔍 DATA QUALITY VALIDATION")
        print("-" * 30)
        
        quality_validations = {
            'not_null_columns': ['CUSTOMER', 'AAG ORDER NUMBER', 'STYLE', 'COLOR'],
            'positive_columns': ['ORDER_QTY'],
            'date_columns': ['ORDER DATE PO RECEIVED']
        }
        
        quality_result = sql_tester.validate_data_quality(
            query_name="Customer Detail Data Quality",
            sql_query=customer_detail_query,
            validations=quality_validations
        )
        
        print(f"Data Quality Score: {quality_result['data_quality_score']}%")
        print(f"Validations Passed: {quality_result['validations_passed']}")
        print(f"Validations Failed: {quality_result['validations_failed']}")
        
        if quality_result['issues']:
            print("\n❌ DATA QUALITY ISSUES:")
            for issue in quality_result['issues']:
                print(f"  - {issue}")
    
    return test_result

if __name__ == "__main__":
    test_customer_detail_query()
