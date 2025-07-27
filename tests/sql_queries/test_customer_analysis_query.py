"""
Test: Customer Analysis Query
=============================

Tests the customer analysis query used in milestone 2 staging workflow.
Validates query structure, performance, and data quality.

Location: tests/sql_queries/test_customer_analysis_query.py
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

def test_customer_analysis_query():
    """Test the customer analysis query for new orders"""
    
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing customer analysis query")
    
    # Initialize SQL tester
    sql_tester = create_sql_tester('dms')
    
    # Define the customer analysis query
    customer_analysis_query = """
    WITH customer_summary AS (
        SELECT 
            ou.[CUSTOMER NAME],
            COUNT(*) as total_orders,
            MIN(ou.[ORDER DATE PO RECEIVED]) as earliest_order_date,
            MAX(ou.[ORDER DATE PO RECEIVED]) as latest_order_date,
            SUM(CASE WHEN ou.[TOTAL QTY] IS NOT NULL THEN ou.[TOTAL QTY] ELSE 0 END) as total_qty,
            COUNT(DISTINCT ou.[CUSTOMER STYLE]) as unique_styles,
            COUNT(DISTINCT ou.[CUSTOMER COLOUR DESCRIPTION]) as unique_colors,
            COUNT(DISTINCT ou.[AAG ORDER NUMBER]) as unique_order_numbers
        FROM [dbo].[ORDERS_UNIFIED] ou
        LEFT JOIN [dbo].[MON_CustMasterSchedule] mcs 
            ON ou.[AAG ORDER NUMBER] = mcs.[AAG ORDER NUMBER]
            AND ou.[CUSTOMER NAME] = mcs.[CUSTOMER]
            AND ou.[CUSTOMER STYLE] = mcs.[STYLE] 
            AND ou.[CUSTOMER COLOUR DESCRIPTION] = mcs.[COLOR]
        WHERE mcs.[Item ID] IS NULL  -- Not yet in Monday.com
            AND ou.[CUSTOMER NAME] IS NOT NULL
            AND ou.[AAG ORDER NUMBER] IS NOT NULL
        GROUP BY ou.[CUSTOMER NAME]
    )
    SELECT 
        [CUSTOMER NAME] as CUSTOMER,
        total_orders,
        earliest_order_date,
        latest_order_date,
        total_qty,
        unique_styles,
        unique_colors,
        unique_order_numbers
    FROM customer_summary
    ORDER BY total_orders DESC;
    """
    
    # Expected columns
    expected_columns = [
        'CUSTOMER',
        'total_orders', 
        'earliest_order_date',
        'latest_order_date', 
        'total_qty',
        'unique_styles',
        'unique_colors',
        'unique_order_numbers'
    ]
    
    # Test query execution and structure
    test_result = sql_tester.test_query(
        query_name="Customer Analysis - New Orders",
        sql_query=customer_analysis_query,
        expected_columns=expected_columns,
        expected_min_rows=0,  # May have no new orders
        expected_max_rows=1000  # Reasonable upper limit
    )
    
    # Print results
    print("🔍 CUSTOMER ANALYSIS QUERY TEST")
    print("=" * 50)
    print(f"Query: {test_result['query_name']}")
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
    
    if test_result['data_sample']:
        print("\n📊 SAMPLE DATA:")
        for i, row in enumerate(test_result['data_sample'], 1):
            print(f"  Row {i}: {row}")
    
    # Test data quality
    if test_result['success'] and test_result['row_count'] > 0:
        print("\n🔍 DATA QUALITY VALIDATION")
        print("-" * 30)
        
        quality_validations = {
            'not_null_columns': ['CUSTOMER', 'total_orders'],
            'positive_columns': ['total_orders', 'total_qty', 'unique_styles', 'unique_colors', 'unique_order_numbers'],
            'date_columns': ['earliest_order_date', 'latest_order_date']
        }
        
        quality_result = sql_tester.validate_data_quality(
            query_name="Customer Analysis Data Quality",
            sql_query=customer_analysis_query,
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
    test_customer_analysis_query()
