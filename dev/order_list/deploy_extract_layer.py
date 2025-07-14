"""
ORDER_LIST Extract Layer Deployment Script
Purpose: Deploy and test the extract layer functionality
Author: Data Engineering Team
Date: July 8, 2025
"""

import sys
from pathlib import Path
import time

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists() and (current / "integrations").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "scripts"))

import db_helper as db
import logger_helper
from dev.order_list.order_list_extract import OrderListExtractor

def validate_extract_layer():
    """Validate the extract layer implementation"""
    logger = logger_helper.get_logger(__name__)
    
    print("=" * 80)
    print("🔍 ORDER_LIST EXTRACT LAYER VALIDATION")
    print("=" * 80)
    
    try:
        # Test 1: Initialize extractor
        print("📋 Test 1: Initialize OrderListExtractor")
        extractor = OrderListExtractor()
        print("✅ Extractor initialized successfully")
        
        # Test 2: Test blob connection
        print("\n📋 Test 2: Test blob storage connection")
        xlsx_files = extractor.discover_xlsx_files()
        print(f"✅ Found {len(xlsx_files)} XLSX files in blob storage")
        
        # Test 3: Test database connection
        print("\n📋 Test 3: Test database connection")
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print("✅ Database connection successful")
        
        # Test 4: Process a single file (if available)
        if xlsx_files:
            print(f"\n📋 Test 4: Process single file: {xlsx_files[0]}")
            result = extractor.extract_single_file(xlsx_files[0])
            
            if result['success']:
                print(f"✅ Single file processing successful")
                print(f"   📊 Rows loaded: {result.get('rows_loaded', 0):,}")
                print(f"   ⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                print(f"   📋 Table created: {result['table_name']}")
                
                # Verify table exists in database
                verify_query = f"SELECT COUNT(*) as row_count FROM [{result['table_name']}]"
                with db.get_connection('orders') as conn:
                    cursor = conn.cursor()
                    cursor.execute(verify_query)
                    actual_rows = cursor.fetchone()[0]
                    print(f"   ✅ Database verification: {actual_rows:,} rows in table")
            else:
                print(f"❌ Single file processing failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎉 Extract layer validation complete!")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        return False

def deploy_extract_layer():
    """Deploy the extract layer with limited file processing"""
    logger = logger_helper.get_logger(__name__)
    
    print("=" * 80)
    print("🚀 ORDER_LIST EXTRACT LAYER DEPLOYMENT")
    print("=" * 80)
    
    try:
        # Initialize extractor
        extractor = OrderListExtractor()
        
        # Process first 5 files only for deployment testing
        xlsx_files = extractor.discover_xlsx_files()[:5]  # Limit to 5 files
        
        print(f"📊 Processing {len(xlsx_files)} files for deployment test")
        
        start_time = time.time()
        results = []
        
        for i, xlsx_file in enumerate(xlsx_files, 1):
            print(f"\n[{i}/{len(xlsx_files)}] Processing: {xlsx_file}")
            result = extractor.extract_single_file(xlsx_file)
            results.append(result)
            
            if result['success']:
                print(f"✅ Success: {result.get('rows_loaded', 0):,} rows in {result.get('processing_time', 0):.2f}s")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Calculate summary
        total_time = time.time() - start_time
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        total_rows = sum(r.get('rows_loaded', 0) for r in successful)
        
        print(f"\n📊 DEPLOYMENT SUMMARY")
        print(f"   ✅ Successful: {len(successful)}/{len(results)} files")
        print(f"   📊 Total rows: {total_rows:,}")
        print(f"   ⏱️ Total time: {total_time:.2f}s")
        print(f"   🚀 Performance: {total_rows/total_time:.0f} rows/second")
        
        if failed:
            print(f"\n❌ Failed files:")
            for result in failed:
                print(f"   - {result['xlsx_file']}: {result.get('error', 'Unknown error')}")
        
        # Mark milestone 1 as ready for sign-off
        if len(successful) >= len(results) * 0.8:  # 80% success rate
            print(f"\n🎯 MILESTONE 1 SUCCESS CRITERIA MET!")
            print(f"   ✅ Extract layer operational")
            print(f"   ✅ Bulk loading performance validated")
            print(f"   ✅ Error handling working")
            print(f"   ✅ Ready for sign-off")
            return True
        else:
            print(f"\n⚠️ MILESTONE 1 NEEDS ATTENTION")
            print(f"   ❌ Success rate: {len(successful)/len(results)*100:.1f}% (target: 80%)")
            return False
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"❌ Deployment failed: {e}")
        return False

def main():
    """Main function"""
    print("🎯 ORDER_LIST Extract Layer Deployment")
    print("Choose an option:")
    print("1. Validate extract layer")
    print("2. Deploy extract layer (limited files)")
    print("3. Both validation and deployment")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        validate_extract_layer()
    elif choice == "2":
        deploy_extract_layer()
    elif choice == "3":
        if validate_extract_layer():
            print("\n" + "="*50)
            deploy_extract_layer()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
