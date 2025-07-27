"""
GREYSON PO 4755 Staging Table Validation Test
Purpose: Validate actual data flow through staging tables with YAML transformation
"""
import sys
from pathlib import Path
import pandas as pd
import yaml

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
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))

import db_helper as db
import logger_helper

def clear_staging_tables():
    """Clear staging tables to start fresh"""
    print("🧹 CLEARING STAGING TABLES")
    print("-" * 30)
    
    try:
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE [dbo].[STG_MON_CustMasterSchedule];")
            cursor.execute("TRUNCATE TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems];")
            conn.commit()
        print("✅ Staging tables cleared")
        return True
    except Exception as e:
        print(f"❌ Failed to clear staging tables: {e}")
        return False

def validate_source_data():
    """Validate source data from ORDERS_UNIFIED"""
    print("\n1️⃣ SOURCE DATA VALIDATION")
    print("-" * 30)
    
    # Query GREYSON data
    query = """
    SELECT TOP 5
        [CUSTOMER NAME],
        [AAG ORDER NUMBER], 
        [CUSTOMER STYLE],
        [CUSTOMER COLOUR DESCRIPTION],
        [TOTAL QTY],
        [PO NUMBER],
        [ORDER DATE PO RECEIVED]
    FROM [dbo].[ORDERS_UNIFIED] 
    WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS'
        AND [PO NUMBER] = '4755'
    ORDER BY [AAG ORDER NUMBER]
    """
    
    try:
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
        
        print(f"✅ Found {len(df)} GREYSON PO 4755 records")
        if len(df) > 0:
            print("📋 Sample source data:")
            sample = df.iloc[0]
            print(f"   Customer: {sample['CUSTOMER NAME']}")
            print(f"   Order: {sample['AAG ORDER NUMBER']}")
            print(f"   Style: {sample['CUSTOMER STYLE']}")
            print(f"   Color: {sample['CUSTOMER COLOUR DESCRIPTION']}")
            print(f"   Qty: {sample['TOTAL QTY']}")
            print(f"   PO: {sample['PO NUMBER']}")
        
        return df
    except Exception as e:
        print(f"❌ Source data validation failed: {e}")
        return pd.DataFrame()

def run_pipeline():
    """Run the customer orders pipeline"""
    print("\n2️⃣ PIPELINE EXECUTION")
    print("-" * 30)
    
    try:
        # Import the MainCustomerOrders class instead of main function
        from main_customer_orders import MainCustomerOrders
        
        # Run with GREYSON, limit 5
        print("🚀 Running main_customer_orders.py...")
        
        # Create orchestrator in TEST mode
        orchestrator = MainCustomerOrders(mode='TEST')
        
        # Run the sync with proper parameters
        result = orchestrator.run_customer_sync(
            customer_filter='GREYSON',
            limit=5,
            po_number_filter='4755'
        )
        
        print(f"✅ Pipeline completed: {result}")
        return True
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_staging_master():
    """Validate STG_MON_CustMasterSchedule data"""
    print("\n3️⃣ STAGING MASTER TABLE VALIDATION")
    print("-" * 30)
    
    query = """
    SELECT 
        [stg_id],
        [AAG ORDER NUMBER],
        [CUSTOMER NAME] as staged_customer,
        [CUSTOMER STYLE] as staged_style,
        [COLOR] as staged_color,
        [TOTAL QTY] as staged_qty,
        [stg_status],
        [stg_customer_batch],
        [stg_batch_id]
    FROM [dbo].[STG_MON_CustMasterSchedule]
    ORDER BY [stg_id]
    """
    
    try:
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
        
        print(f"✅ Found {len(df)} records in staging master table")
        
        if len(df) > 0:
            print("📋 Sample staging data:")
            sample = df.iloc[0]
            print(f"   Staging ID: {sample['stg_id']}")
            print(f"   Customer: {sample['staged_customer']}")
            print(f"   Order: {sample['AAG ORDER NUMBER']}")
            print(f"   Style: {sample['staged_style']}")
            print(f"   Color: {sample['staged_color']}")
            print(f"   Qty: {sample['staged_qty']}")
            print(f"   Status: {sample['stg_status']}")
            print(f"   Batch: {sample['stg_customer_batch']}")
            
            # Check for YAML transformation evidence
            if sample['staged_customer'] == 'GREYSON':
                print("✅ Customer canonicalization applied")
            else:
                print(f"⚠️  Expected 'GREYSON', got '{sample['staged_customer']}'")
        
        return df
    except Exception as e:
        print(f"❌ Staging master validation failed: {e}")
        return pd.DataFrame()

def validate_staging_subitems():
    """Validate STG_MON_CustMasterSchedule_Subitems data"""
    print("\n4️⃣ STAGING SUBITEMS TABLE VALIDATION")
    print("-" * 30)
    
    query = """
    SELECT 
        [stg_subitem_id],
        [AAG_ORDER_NUMBER],
        [stg_size_label],
        [ORDER_QTY],
        [stg_status],
        [stg_batch_id],
        [stg_parent_stg_id]
    FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
    ORDER BY [stg_subitem_id]
    """
    
    try:
        with db.get_connection('orders') as conn:
            df = pd.read_sql(query, conn)
        
        print(f"✅ Found {len(df)} records in staging subitems table")
        
        if len(df) > 0:
            print("📋 Sample subitem data:")
            sample = df.iloc[0]
            print(f"   Subitem ID: {sample['stg_subitem_id']}")
            print(f"   Order: {sample['AAG_ORDER_NUMBER']}")
            print(f"   Size: {sample['stg_size_label']}")
            print(f"   Qty: {sample['ORDER_QTY']}")
            print(f"   Status: {sample['stg_status']}")
            print(f"   Parent: {sample['stg_parent_stg_id']}")
            
            # Group by size to see distribution
            size_summary = df.groupby('stg_size_label')['ORDER_QTY'].sum()
            print(f"\n📊 Size distribution:")
            for size, qty in size_summary.items():
                print(f"   {size}: {qty}")
        
        return df
    except Exception as e:
        print(f"❌ Staging subitems validation failed: {e}")
        return pd.DataFrame()

def compare_source_vs_staging():
    """Compare source data vs staging data to validate YAML transformation"""
    print("\n5️⃣ SOURCE VS STAGING COMPARISON")
    print("-" * 30)
    
    # Get source data
    source_query = """
    SELECT TOP 1
        [CUSTOMER NAME] as source_customer,
        [AAG ORDER NUMBER] as source_order,
        [CUSTOMER STYLE] as source_style,
        [CUSTOMER COLOUR DESCRIPTION] as source_color,
        [TOTAL QTY] as source_qty
    FROM [dbo].[ORDERS_UNIFIED] 
    WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755'
    """
    
    # Get staging data
    staging_query = """
    SELECT TOP 1
        [CUSTOMER NAME] as staged_customer,
        [AAG ORDER NUMBER] as staged_order,
        [CUSTOMER STYLE] as staged_style,
        [COLOR] as staged_color,
        [TOTAL QTY] as staged_qty
    FROM [dbo].[STG_MON_CustMasterSchedule]
    ORDER BY [stg_id]
    """
    
    try:
        with db.get_connection('orders') as conn:
            source_df = pd.read_sql(source_query, conn)
            staging_df = pd.read_sql(staging_query, conn)
        
        if len(source_df) > 0 and len(staging_df) > 0:
            source = source_df.iloc[0]
            staged = staging_df.iloc[0]
            
            print("📊 Field-by-field comparison:")
            print(f"   Customer: '{source['source_customer']}' → '{staged['staged_customer']}'")
            print(f"   Order: '{source['source_order']}' → '{staged['staged_order']}'")
            print(f"   Style: '{source['source_style']}' → '{staged['staged_style']}'")
            print(f"   Color: '{source['source_color']}' → '{staged['staged_color']}'")
            print(f"   Qty: {source['source_qty']} → {staged['staged_qty']}")
            
            # Validate transformations
            transformations_valid = True
            
            # Customer should be canonicalized
            if staged['staged_customer'] != 'GREYSON':
                print(f"⚠️  Customer canonicalization: Expected 'GREYSON', got '{staged['staged_customer']}'")
                transformations_valid = False
            else:
                print("✅ Customer canonicalization working")
            
            # Other fields should be preserved or mapped
            if source['source_order'] != staged['staged_order']:
                print("⚠️  Order number mismatch")
                transformations_valid = False
            else:
                print("✅ Order number preserved")
            
            return transformations_valid
        else:
            print("❌ No data found for comparison")
            return False
            
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 GREYSON PO 4755 STAGING VALIDATION TEST")
    print("=" * 50)
    
    # Step 0: Clear staging tables
    if not clear_staging_tables():
        return False
    
    # Step 1: Validate source data
    source_data = validate_source_data()
    if source_data.empty:
        print("❌ No source data found - cannot proceed")
        return False
    
    # Step 2: Run pipeline
    if not run_pipeline():
        print("❌ Pipeline failed - cannot proceed")
        return False
    
    # Step 3: Validate staging tables
    staging_master = validate_staging_master()
    staging_subitems = validate_staging_subitems()
    
    # Step 4: Compare transformations
    transformation_valid = compare_source_vs_staging()
    
    # Final summary
    print(f"\n🎯 FINAL VALIDATION SUMMARY")
    print("=" * 30)
    print(f"✅ Source data: {len(source_data)} records")
    print(f"✅ Staging master: {len(staging_master)} records")
    print(f"✅ Staging subitems: {len(staging_subitems)} records")
    print(f"{'✅' if transformation_valid else '❌'} YAML transformations: {'WORKING' if transformation_valid else 'FAILED'}")
    
    overall_success = (
        len(source_data) > 0 and 
        len(staging_master) > 0 and 
        transformation_valid
    )
    
    if overall_success:
        print(f"\n🎉 STAGING VALIDATION: PASSED")
        print("   Pipeline is correctly applying YAML transformations!")
    else:
        print(f"\n❌ STAGING VALIDATION: FAILED")
        print("   Check the issues above and fix before proceeding")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)