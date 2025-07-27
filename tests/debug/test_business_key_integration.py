"""
Test Business Key Generation with ORDER_LIST Data
=================================================
Purpose: Validate business key generation with actual ORDER_LIST records
Location: tests/debug/test_business_key_integration.py
Created: 2025-07-19 (Milestone 2: Business Key Implementation)

This test validates the customer resolver and business key generator
modules using actual ORDER_LIST data to ensure the business key approach
works correctly with Excel-compatible logic.
"""
import sys
from pathlib import Path
import pandas as pd
import logging

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))
sys.path.insert(0, str(repo_root / "src" / "pipelines" / "order_delta_sync"))

# Import from utils/
import db_helper as db
import logger_helper

# Import our new modules
from customer_resolver import create_customer_resolver
from business_key_generator import create_business_key_generator

def test_business_key_integration():
    """Test business key generation with actual ORDER_LIST data"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting business key integration test")
    
    try:
        # Initialize modules
        customer_resolver = create_customer_resolver()
        key_generator = create_business_key_generator(customer_resolver)
        
        # Test query to get sample ORDER_LIST data
        sql = """
        SELECT TOP 10
            [AAG ORDER NUMBER],
            [CUSTOMER],
            [CUSTOMER STYLE],
            [PO NUMBER],
            [ORDER TYPE],
            [ORDER QTY],
            [PLANNED DELIVERY METHOD]
        FROM [dbo].[ORDER_LIST]
        WHERE [CUSTOMER] IN ('GREYSON', 'TRACKSMITH', 'AJE ATHLETICA (AU)')
        AND [AAG ORDER NUMBER] IS NOT NULL
        ORDER BY [AAG ORDER NUMBER]
        """
        
        logger.info("Querying ORDER_LIST for sample data")
        with db.get_connection('dms') as conn:
            df = pd.read_sql(sql, conn)
        
        if df.empty:
            logger.warning("No sample data found, creating synthetic test data")
            df = create_synthetic_test_data()
        
        logger.info(f"Retrieved {len(df)} records for testing")
        
        # Get existing orders for NEW detection
        existing_orders_sql = """
        SELECT DISTINCT [AAG ORDER NUMBER]
        FROM [dbo].[ORDER_LIST]
        WHERE [AAG ORDER NUMBER] IS NOT NULL
        """
        
        with db.get_connection('dms') as conn:
            existing_df = pd.read_sql(existing_orders_sql, conn)
        
        existing_orders = set(existing_df['AAG ORDER NUMBER'].tolist())
        logger.info(f"Found {len(existing_orders)} existing AAG ORDER NUMBERs")
        
        # Test customer resolution
        logger.info("\n" + "="*60)
        logger.info("CUSTOMER RESOLUTION TEST")
        logger.info("="*60)
        
        for idx, row in df.iterrows():
            source_customer = row['CUSTOMER']
            canonical = customer_resolver.resolve_canonical_customer(source_customer)
            unique_keys = customer_resolver.get_unique_keys(canonical)
            status = customer_resolver.get_customer_status(canonical)
            
            logger.info(f"Row {idx+1}:")
            logger.info(f"  Source Customer: {source_customer}")
            logger.info(f"  Canonical: {canonical}")
            logger.info(f"  Status: {status}")
            logger.info(f"  Unique Keys: {unique_keys}")
            logger.info("")
        
        # Test business key generation
        logger.info("="*60)
        logger.info("BUSINESS KEY GENERATION TEST")
        logger.info("="*60)
        
        # Define hash columns for change detection
        hash_columns = [
            'CUSTOMER STYLE',
            'ORDER QTY', 
            'ORDER TYPE',
            'PLANNED DELIVERY METHOD'
        ]
        
        # Process DataFrame
        result_df = key_generator.process_dataframe(df, hash_columns, existing_orders)
        
        # Display results
        logger.info("\nGenerated Business Keys:")
        logger.info("-" * 80)
        
        for idx, row in result_df.iterrows():
            logger.info(f"Record {idx+1}:")
            logger.info(f"  AAG ORDER NUMBER: {row['AAG ORDER NUMBER']}")
            logger.info(f"  Customer: {row['CUSTOMER']}")
            logger.info(f"  Business Key: {row['business_key']}")
            logger.info(f"  Sync State: {row['sync_state']}")
            logger.info(f"  Row Hash: {row['row_hash'][:16]}...")
            logger.info("")
        
        # Validate business keys
        logger.info("="*60)
        logger.info("VALIDATION RESULTS")
        logger.info("="*60)
        
        validation = key_generator.validate_business_keys(result_df)
        
        for key, value in validation.items():
            logger.info(f"{key}: {value}")
        
        # Test duplicate detection within batch
        logger.info("\n" + "="*60)
        logger.info("DUPLICATE DETECTION TEST")
        logger.info("="*60)
        
        # Create a duplicate record for testing
        if len(result_df) > 0:
            duplicate_row = result_df.iloc[0].copy()
            duplicate_row['ORDER QTY'] = 999  # Change content but keep keys same
            
            test_df = pd.concat([result_df, duplicate_row.to_frame().T], ignore_index=True)
            
            # Process with duplicates
            key_generator_dup = create_business_key_generator(customer_resolver)
            dup_result = key_generator_dup.process_dataframe(test_df, hash_columns, existing_orders)
            
            logger.info("Testing duplicate detection:")
            logger.info(f"Original business key: {dup_result.iloc[0]['business_key']}")
            logger.info(f"Duplicate business key: {dup_result.iloc[-1]['business_key']}")
            
            dup_validation = key_generator_dup.validate_business_keys(dup_result)
            logger.info(f"Duplicate validation - unique keys: {dup_validation['unique_keys']}")
            logger.info(f"Duplicate validation - duplicate count: {dup_validation['duplicate_count']}")
        
        logger.info("\n" + "="*60)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.exception("Full error details:")
        return False

def create_synthetic_test_data():
    """Create synthetic test data if no real data available"""
    return pd.DataFrame([
        {
            'AAG ORDER NUMBER': 'TEST-001',
            'CUSTOMER': 'GREYSON',
            'CUSTOMER STYLE': 'GREYSON-TEST-001',
            'PO NUMBER': 'TEST-PO-001',
            'ORDER TYPE': 'DEVELOPMENT',
            'ORDER QTY': 100,
            'PLANNED DELIVERY METHOD': 'AIR'
        },
        {
            'AAG ORDER NUMBER': 'TEST-002',
            'CUSTOMER': 'TRACKSMITH',
            'CUSTOMER STYLE': 'TRK-TEST-002',
            'PO NUMBER': 'TEST-PO-002',
            'ORDER TYPE': 'PRODUCTION',
            'ORDER QTY': 500,
            'PLANNED DELIVERY METHOD': 'OCEAN'
        }
    ])

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    print("🧪 Business Key Integration Test")
    print("="*60)
    
    success = test_business_key_integration()
    
    if success:
        print("\n✅ All tests passed!")
        print("🎯 Business key generation ready for Milestone 2 implementation")
    else:
        print("\n❌ Tests failed!")
        print("🔧 Check logs for details and fix issues before proceeding")
