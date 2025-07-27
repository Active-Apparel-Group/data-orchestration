#!/usr/bin/env python3
"""
Fix SQL Query Issues - Debug and repair broken SQL queries in test framework
Based on findings from sql_query_debugger.py analysis
"""

import sys
from pathlib import Path

# Use robust path resolution
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root))

import yaml
from utils.db_helper import get_connection
from utils.logger_helper import get_logger

logger = get_logger(__name__)

def test_staging_table_access():
    """Test access to staging tables that were failing in queries"""
    
    logger.info("🔍 Testing staging table access and column structure...")
    
    with get_connection('dms') as conn:
        cursor = conn.cursor()
        
        # Test 1: Check if staging subitems table exists and accessible
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_records 
                FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
            """)
            result = cursor.fetchone()
            logger.info(f"✅ STG_MON_CustMasterSchedule_Subitems: {result[0]} records")
        except Exception as e:
            logger.error(f"❌ STG_MON_CustMasterSchedule_Subitems access failed: {e}")
        
        # Test 2: Check staging items table
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_records 
                FROM [dbo].[STG_MON_CustMasterSchedule]
            """)
            result = cursor.fetchone()
            logger.info(f"✅ STG_MON_CustMasterSchedule: {result[0]} records")
        except Exception as e:
            logger.error(f"❌ STG_MON_CustMasterSchedule access failed: {e}")
        
        # Test 3: Verify column names for staging subitems
        try:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            logger.info(f"✅ STG_MON_CustMasterSchedule_Subitems columns: {len(columns)} found")
            
            # Check for key columns
            column_names = [col[0] for col in columns]
            required_cols = ['stg_batch_id', 'stg_status', 'Size', 'Order_Qty', 'stg_monday_subitem_id']
            for col in required_cols:
                if col in column_names:
                    logger.info(f"  ✅ Found column: {col}")
                else:
                    logger.warning(f"  ❌ Missing column: {col}")
                    
        except Exception as e:
            logger.error(f"❌ Column check failed: {e}")

def test_parameterized_queries():
    """Test parameterized queries that were failing"""
    
    logger.info("🔍 Testing parameterized query execution...")
    
    with get_connection('dms') as conn:
        cursor = conn.cursor()
        
        # Test 1: Simple parameterized query
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_orders
                FROM [dbo].[ORDERS_UNIFIED] 
                WHERE [CUSTOMER NAME] LIKE ?
                AND [PO NUMBER] = ?
            """, ('%GREYSON%', '4755'))
            result = cursor.fetchone()
            logger.info(f"✅ Parameterized GREYSON filter: {result[0]} orders")
        except Exception as e:
            logger.error(f"❌ Parameterized query failed: {e}")
        
        # Test 2: Batch ID parameter test
        try:
            # Get a sample batch ID first
            cursor.execute("""
                SELECT TOP 1 batch_id 
                FROM [dbo].[MON_BatchProcessing] 
                WHERE customer_name LIKE '%GREYSON%'
                ORDER BY start_time DESC
            """)
            batch_result = cursor.fetchone()
            
            if batch_result:
                batch_id = batch_result[0]
                logger.info(f"📝 Testing with batch_id: {batch_id}")
                
                # Test the failing staging query pattern
                cursor.execute("""
                    SELECT COUNT(*) as staging_count
                    FROM [dbo].[STG_MON_CustMasterSchedule]
                    WHERE stg_batch_id = ?
                """, (batch_id,))
                result = cursor.fetchone()
                logger.info(f"✅ Staging items for batch {batch_id}: {result[0]} records")
                
        except Exception as e:
            logger.error(f"❌ Batch ID parameter test failed: {e}")

def test_column_name_corrections():
    """Test queries with corrected column names"""
    
    logger.info("🔍 Testing column name corrections...")
    
    with get_connection('dms') as conn:
        cursor = conn.cursor()
        
        # Test 1: Check actual MON_CustMasterSchedule columns
        try:
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'MON_CustMasterSchedule'
                AND COLUMN_NAME IN ('CUSTOMER', 'CUSTOMER_CODE', 'ORDER_NUMBER', 'AAG ORDER NUMBER')
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            found_columns = [col[0] for col in columns]
            logger.info(f"✅ Found MON_CustMasterSchedule columns: {found_columns}")
            
            # Test with correct column name
            cursor.execute("""
                SELECT TOP 5 [Item ID], [CUSTOMER], [AAG ORDER NUMBER], [STYLE], [COLOR]
                FROM [dbo].[MON_CustMasterSchedule]
                WHERE [CUSTOMER] LIKE '%GREYSON%'
            """)
            results = cursor.fetchall()
            logger.info(f"✅ GREYSON production data: {len(results)} records found")
            
        except Exception as e:
            logger.error(f"❌ Column name test failed: {e}")

def test_size_column_detection():
    """Test the size column detection logic that was failing"""
    
    logger.info("🔍 Testing size column detection for GREYSON orders...")
    
    with get_connection('dms') as conn:
        cursor = conn.cursor()
        
        try:
            # Get size columns like our mapper does
            cursor.execute("""
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
            """)
            size_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ Size columns detected: {len(size_columns)} columns")
            logger.info(f"📝 First 10 size columns: {size_columns[:10]}")
            
            # Test size data for GREYSON
            if size_columns:
                # Build dynamic query for first 5 size columns
                first_5_sizes = size_columns[:5]
                size_select = ', '.join([f'[{col}]' for col in first_5_sizes])
                
                query = f"""
                    SELECT [AAG ORDER NUMBER], [CUSTOMER STYLE], {size_select}
                    FROM [dbo].[ORDERS_UNIFIED]
                    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
                    AND [PO NUMBER] = '4755'
                    AND ([{first_5_sizes[0]}] IS NOT NULL OR [{first_5_sizes[1]}] IS NOT NULL)
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                logger.info(f"✅ GREYSON orders with size data: {len(results)} records")
                
                if results:
                    sample = results[0]
                    logger.info(f"📝 Sample size data: {dict(zip(['ORDER', 'STYLE'] + first_5_sizes, sample))}")
            
        except Exception as e:
            logger.error(f"❌ Size column detection failed: {e}")

def validate_subitem_workflow():
    """Validate the complete subitem workflow data path"""
    
    logger.info("🔍 Validating complete subitem workflow...")
    
    with get_connection('dms') as conn:
        cursor = conn.cursor()
        
        # 1. Source data
        cursor.execute("""
            SELECT COUNT(*) as source_orders,
                   SUM(CASE WHEN [TOTAL QTY] > 0 THEN 1 ELSE 0 END) as orders_with_qty
            FROM [dbo].[ORDERS_UNIFIED]
            WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
            AND [PO NUMBER] = '4755'
        """)
        source_result = cursor.fetchone()
        logger.info(f"📊 Source: {source_result[0]} orders, {source_result[1]} with quantity")
        
        # 2. Staging items
        cursor.execute("""
            SELECT COUNT(*) as staged_items,
                   COUNT(CASE WHEN stg_status = 'API_SUCCESS' THEN 1 END) as successful_items
            FROM [dbo].[STG_MON_CustMasterSchedule]
            WHERE [CUSTOMER] LIKE '%GREYSON%'
        """)
        staging_result = cursor.fetchone()
        logger.info(f"📊 Staging Items: {staging_result[0]} total, {staging_result[1]} successful")
        
        # 3. Staging subitems
        cursor.execute("""
            SELECT COUNT(*) as staged_subitems,
                   COUNT(CASE WHEN stg_status = 'API_SUCCESS' THEN 1 END) as successful_subitems,
                   COUNT(DISTINCT [Size]) as unique_sizes
            FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
            WHERE [CUSTOMER] LIKE '%GREYSON%'
        """)
        subitem_result = cursor.fetchone()
        logger.info(f"📊 Staging Subitems: {subitem_result[0]} total, {subitem_result[1]} successful, {subitem_result[2]} unique sizes")
        
        # 4. Production items
        cursor.execute("""
            SELECT COUNT(*) as prod_items
            FROM [dbo].[MON_CustMasterSchedule]
            WHERE [CUSTOMER] LIKE '%GREYSON%'
            AND [PO NUMBER] = '4755'
        """)
        prod_result = cursor.fetchone()
        logger.info(f"📊 Production Items: {prod_result[0]} items")
        
        # 5. Production subitems
        cursor.execute("""
            SELECT COUNT(*) as prod_subitems
            FROM [dbo].[MON_CustMasterSchedule_Subitems] ms
            WHERE EXISTS (
                SELECT 1 FROM [dbo].[MON_CustMasterSchedule] m
                WHERE m.[Item ID] = ms.[Item ID]
                AND m.[CUSTOMER] LIKE '%GREYSON%'
                AND m.[PO NUMBER] = '4755'
            )
        """)
        subitem_prod_result = cursor.fetchone()
        logger.info(f"📊 Production Subitems: {subitem_prod_result[0]} subitems")
        
        return {
            'source_orders': source_result[0],
            'orders_with_qty': source_result[1],
            'staged_items': staging_result[0],
            'successful_items': staging_result[1],
            'staged_subitems': subitem_result[0],
            'successful_subitems': subitem_result[1],
            'unique_sizes': subitem_result[2],
            'prod_items': prod_result[0],
            'prod_subitems': subitem_prod_result[0]
        }

def main():
    """Run all SQL query issue tests"""
    
    logger.info("🚀 Starting SQL Query Issues Fix and Validation...")
    logger.info("=" * 80)
    
    # Run all tests
    test_staging_table_access()
    logger.info("-" * 80)
    
    test_parameterized_queries()
    logger.info("-" * 80)
    
    test_column_name_corrections()
    logger.info("-" * 80)
    
    test_size_column_detection()
    logger.info("-" * 80)
    
    # Get complete workflow validation
    workflow_data = validate_subitem_workflow()
    logger.info("-" * 80)
    
    # Summary and recommendations
    logger.info("📋 SUMMARY AND RECOMMENDATIONS:")
    logger.info("=" * 80)
    
    if workflow_data['staged_subitems'] == 0:
        logger.warning("❌ CRITICAL: No subitems in staging - subitem creation logic not working")
        logger.info("🔧 REQUIRED ACTIONS:")
        logger.info("   1. Fix batch processor subitem insertion logic")
        logger.info("   2. Verify size melting and staging processor integration")
        logger.info("   3. Test end-to-end subitem workflow")
    else:
        logger.info("✅ Subitems are being staged successfully")
    
    if workflow_data['source_orders'] != workflow_data['staged_items']:
        logger.warning(f"❌ Source/Staging mismatch: {workflow_data['source_orders']} source vs {workflow_data['staged_items']} staged")
    else:
        logger.info("✅ Source to staging flow working correctly")
    
    logger.info("🎯 Next steps: Focus on subitem creation in batch processor")
    
if __name__ == "__main__":
    main()
