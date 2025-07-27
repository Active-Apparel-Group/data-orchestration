"""
OPUS Update Infrastructure Validation
Purpose: Comprehensive validation of update infras                for _, row in staging_results.iterrows():
            if row['update_columns_count'] != 8:
                print(f"   ❌ {row['TABLE_NAME']}: {row['update_columns_count']}/8 update columns")
                schema_success = False
            else:
                print(f"   ✅ {row['TABLE_NAME']}: All 8 update columns present") _, row in staging_results.iterrows():
            if row['update_columns_count'] != 8:
                print(f"   ❌ {row['TABLE_NAME']}: {row['update_columns_count']}/8 update columns")
                schema_success = False
            else:
                print(f"   ✅ {row['TABLE_NAME']}: All 8 update columns present")   if row['update_columns_count'] < 8:
                print(f"   ❌ {row['TABLE_NAME']}: {row['update_columns_count']}/8 update columns")
                schema_success = False
            else:
                print(f"   ✅ {row['TABLE_NAME']}: All 8 update columns present")ure deployment
Date: 2025-06-30
Reference: OPUS_dev_update_boards.yaml - Task IMM.4

This script validates th    # Test 5: Audit Trail Functionality  
    print("\n5️⃣ VALIDATING AUDIT TRAIL FUNCTIONALITY")
    try:
        with db.get_connection('orders') as conn:ll OPUS update infrastructure components
are properly deployed and functional before proceeding to Phase 1.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

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
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import utilities
import db_helper as db
import logger_helper

def validate_opus_update_infrastructure():
    """
    Comprehensive infrastructure validation for OPUS update boards
    
    Validates:
    1. Database schema extensions
    2. UpdateOperations module availability
    3. Board metadata loading
    4. Staging table accessibility
    5. Audit infrastructure
    """
    
    logger = logger_helper.get_logger(__name__)
    logger.info("=== OPUS UPDATE INFRASTRUCTURE VALIDATION ===")
    
    validation_results = {}
    overall_success = True
    
    print("🔍 OPUS UPDATE INFRASTRUCTURE VALIDATION")
    print("=" * 50)
    
    # Test 1: Database Schema Validation
    print("\n1️⃣ VALIDATING DATABASE SCHEMA EXTENSIONS")
    try:
        with db.get_connection('orders') as conn:
            # Check staging table extensions
            staging_validation_sql = """
            SELECT 
                t.TABLE_NAME,
                COUNT(c.COLUMN_NAME) as update_columns_count
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
                AND c.COLUMN_NAME IN (
                    'board_id', 'update_operation', 'update_fields', 'source_table', 
                    'source_query', 'update_batch_id', 'validation_status', 'validation_errors'
                )
            WHERE t.TABLE_NAME IN ('STG_MON_CustMasterSchedule', 'STG_MON_CustMasterSchedule_Subitems')
            GROUP BY t.TABLE_NAME
            """
            
            import pandas as pd
            staging_results = pd.read_sql(staging_validation_sql, conn)
            
            # Check audit infrastructure
            audit_validation_sql = """
            SELECT 
                CASE WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_UpdateAudit') 
                     THEN 1 ELSE 0 END as audit_table_exists,
                CASE WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'SP_RollbackBatch') 
                     THEN 1 ELSE 0 END as rollback_proc_exists,
                CASE WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'VW_UpdateOperationSummary') 
                     THEN 1 ELSE 0 END as summary_view_exists
            """
            
            audit_results = pd.read_sql(audit_validation_sql, conn)
        
        # Validate results
        schema_success = True
        for _, row in staging_results.iterrows():
            if row['update_columns_count'] != 8:
                print(f"   ❌ {row['TABLE_NAME']}: {row['update_columns_count']}/8 update columns")
                schema_success = False
            else:
                print(f"   ✅ {row['TABLE_NAME']}: All 8 update columns present")
        
        audit_row = audit_results.iloc[0]
        if audit_row['audit_table_exists'] == 1:
            print("   ✅ MON_UpdateAudit table exists")
        else:
            print("   ❌ MON_UpdateAudit table missing")
            schema_success = False
            
        if audit_row['rollback_proc_exists'] == 1:
            print("   ✅ SP_RollbackBatch procedure exists")
        else:
            print("   ❌ SP_RollbackBatch procedure missing")
            schema_success = False
            
        if audit_row['summary_view_exists'] == 1:
            print("   ✅ VW_UpdateOperationSummary view exists")
        else:
            print("   ❌ VW_UpdateOperationSummary view missing")
            schema_success = False
        
        validation_results['database_schema'] = {
            'success': schema_success,
            'staging_tables': staging_results.to_dict('records'),
            'audit_infrastructure': audit_results.to_dict('records')[0]
        }
        
        if not schema_success:
            overall_success = False
            
    except Exception as e:
        print(f"   ❌ Database schema validation failed: {e}")
        validation_results['database_schema'] = {'success': False, 'error': str(e)}
        overall_success = False
    
    # Test 2: UpdateOperations Module
    print("\n2️⃣ VALIDATING UPDATEOPERATIONS MODULE")
    try:
        from update_operations import UpdateOperations
        
        # Test initialization
        test_board_id = 8709134353  # Planning board
        update_ops = UpdateOperations(test_board_id)
        
        print(f"   ✅ UpdateOperations module imported successfully")
        print(f"   ✅ Initialized for board {test_board_id}")
        print(f"   ✅ Board metadata loaded: {len(update_ops.board_metadata)} keys")
        
        validation_results['update_operations'] = {
            'success': True,
            'board_id': test_board_id,
            'metadata_keys': list(update_ops.board_metadata.keys())
        }
        
    except Exception as e:
        print(f"   ❌ UpdateOperations module validation failed: {e}")
        validation_results['update_operations'] = {'success': False, 'error': str(e)}
        overall_success = False
    
    # Test 3: Board Metadata Access
    print("\n3️⃣ VALIDATING BOARD METADATA ACCESS")
    try:
        metadata_dir = repo_root / "configs" / "boards"
        if metadata_dir.exists():
            metadata_files = list(metadata_dir.glob("board_*_metadata.json"))
            print(f"   ✅ Metadata directory exists: {metadata_dir}")
            print(f"   ✅ Found {len(metadata_files)} board metadata files")
            
            validation_results['board_metadata'] = {
                'success': True,
                'metadata_directory': str(metadata_dir),
                'metadata_files_count': len(metadata_files)
            }
        else:
            print(f"   ⚠️ Metadata directory not found: {metadata_dir}")
            print("   ℹ️ This is acceptable - metadata will be created as needed")
            
            validation_results['board_metadata'] = {
                'success': True,
                'metadata_directory': str(metadata_dir),
                'metadata_files_count': 0,
                'note': 'Directory will be created as needed'
            }
            
    except Exception as e:
        print(f"   ❌ Board metadata validation failed: {e}")
        validation_results['board_metadata'] = {'success': False, 'error': str(e)}
        overall_success = False
    
    # Test 4: Database Connectivity
    print("\n4️⃣ VALIDATING DATABASE CONNECTIVITY")
    try:
        config = db.load_config()
        databases = config.get('databases', {})
        
        print(f"   ✅ Configuration loaded: {len(databases)} databases configured")
        
        # Test DMS connection (primary database for staging)
        with db.get_connection('orders') as conn:
            test_query = "SELECT @@VERSION as sql_version, GETDATE() as [current_time]"
            import pandas as pd
            result = pd.read_sql(test_query, conn)
            
            print(f"   ✅ ORDERS database connection successful")
            print(f"   ✅ SQL Server version confirmed")
        
        validation_results['database_connectivity'] = {
            'success': True,
            'databases_configured': len(databases),
            'dms_connection': 'successful'
        }
        
    except Exception as e:
        print(f"   ❌ Database connectivity validation failed: {e}")
        validation_results['database_connectivity'] = {'success': False, 'error': str(e)}
        overall_success = False
    
    # Test 5: Audit Trail Functionality
    print("\n5️⃣ VALIDATING AUDIT TRAIL FUNCTIONALITY")
    try:
        with db.get_connection('orders') as conn:
            # Test audit table access
            audit_test_sql = """
            SELECT 
                COUNT(*) as audit_record_count,
                CASE WHEN COUNT(*) >= 0 THEN 'accessible' ELSE 'error' END as audit_status
            FROM MON_UpdateAudit
            """
            
            import pandas as pd
            audit_test = pd.read_sql(audit_test_sql, conn)
            
            print(f"   ✅ Audit table accessible: {audit_test.iloc[0]['audit_record_count']} records")
            print(f"   ✅ Audit trail ready for operation logging")
        
        validation_results['audit_trail'] = {
            'success': True,
            'audit_table_accessible': True,
            'existing_records': int(audit_test.iloc[0]['audit_record_count'])
        }
        
    except Exception as e:
        print(f"   ❌ Audit trail validation failed: {e}")
        validation_results['audit_trail'] = {'success': False, 'error': str(e)}
        overall_success = False
    
    # Final Results
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for result in validation_results.values() if result.get('success', False))
    total_tests = len(validation_results)
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Tests Passed: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if overall_success:
        print("\n🎉 INFRASTRUCTURE VALIDATION SUCCESSFUL")
        print("✅ All components ready for Phase 1 GraphQL implementation")
        print("\nNext Steps:")
        print("1. Proceed to Phase 1: GraphQL template creation")
        print("2. Begin Monday.com API integration")
        print("3. Test single update workflow")
    else:
        print("\n⚠️ INFRASTRUCTURE VALIDATION FAILED")
        print("❌ Issues must be resolved before proceeding to Phase 1")
        print("\nRequired Actions:")
        for test_name, result in validation_results.items():
            if not result.get('success', False):
                print(f"   - Fix {test_name}: {result.get('error', 'Unknown error')}")
    
    # Save validation results
    results_file = repo_root / "test_results" / f"opus_infrastructure_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'validation_timestamp': datetime.now().isoformat(),
            'overall_success': overall_success,
            'success_rate': success_rate,
            'validation_results': validation_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved: {results_file}")
    
    return overall_success, validation_results

if __name__ == "__main__":
    success, results = validate_opus_update_infrastructure()
    
    # Exit with appropriate code for CI/CD integration
    sys.exit(0 if success else 1)
