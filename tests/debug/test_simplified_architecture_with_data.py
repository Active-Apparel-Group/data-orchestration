"""
Test Simplified 2-Template Architecture with Actual Data
Tests the new unpivot_sizes_direct.j2 template and updated merge orchestrator with real GREYSON data
"""

import sys
from pathlib import Path
import time

# Add project root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator

logger = logger.get_logger(__name__)

def setup_test_data():
    """Setup GREYSON PO 4755 test data in swp_ORDER_LIST_V2"""
    print("🔄 Setting up test data...")
    
    setup_sql = """
    -- Clear staging table
    TRUNCATE TABLE swp_ORDER_LIST_V2;
    
    -- Load GREYSON PO 4755 test data
    INSERT INTO swp_ORDER_LIST_V2 
    SELECT * FROM ORDER_LIST 
    WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' 
    AND [PO NUMBER] = '4755';
    """
    
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        cursor.execute(setup_sql)
        records_loaded = cursor.rowcount
        conn.commit()
    
    print(f"   ✅ {records_loaded} GREYSON PO 4755 records loaded into swp_ORDER_LIST_V2")
    return records_loaded

def validate_results():
    """Validate that simplified architecture populated tables correctly"""
    print("\n📊 Validating Results...")
    
    # Check ORDER_LIST_V2 population
    v2_sql = """
    SELECT COUNT(*) as header_count,
           COUNT(CASE WHEN sync_state IS NOT NULL THEN 1 END) as sync_state_count,
           COUNT(CASE WHEN action_type IS NOT NULL THEN 1 END) as action_type_count
    FROM ORDER_LIST_V2 
    WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755'
    """
    
    # Check ORDER_LIST_LINES population 
    lines_sql = """
    SELECT COUNT(*) as lines_count,
           COUNT(DISTINCT l.record_uuid) as unique_records,
           COUNT(CASE WHEN l.sync_state IS NOT NULL THEN 1 END) as lines_sync_state_count,
           COUNT(CASE WHEN l.size_code IS NOT NULL THEN 1 END) as size_code_count
    FROM ORDER_LIST_LINES l
    INNER JOIN ORDER_LIST_V2 v ON l.record_uuid = v.record_uuid
    WHERE v.[CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND v.[PO NUMBER] = '4755'
    """
    
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        
        # Check headers
        cursor.execute(v2_sql)
        v2_results = cursor.fetchone()
        print(f"   📋 ORDER_LIST_V2: {v2_results.header_count} records")
        print(f"      - Sync State populated: {v2_results.sync_state_count}/{v2_results.header_count}")
        print(f"      - Action Type populated: {v2_results.action_type_count}/{v2_results.header_count}")
        
        # Check lines
        cursor.execute(lines_sql)
        lines_results = cursor.fetchone()
        print(f"   📐 ORDER_LIST_LINES: {lines_results.lines_count} line records")
        print(f"      - Unique headers: {lines_results.unique_records}")
        print(f"      - Sync State populated: {lines_results.lines_sync_state_count}/{lines_results.lines_count}")
        print(f"      - Size Code populated: {lines_results.size_code_count}/{lines_results.lines_count}")
        
        return {
            'headers': {
                'count': v2_results.header_count,
                'sync_coverage': v2_results.sync_state_count / v2_results.header_count if v2_results.header_count > 0 else 0
            },
            'lines': {
                'count': lines_results.lines_count,
                'unique_records': lines_results.unique_records,
                'sync_coverage': lines_results.lines_sync_state_count / lines_results.lines_count if lines_results.lines_count > 0 else 0
            }
        }

def test_simplified_architecture_with_data():
    """Test the simplified 2-template architecture with actual GREYSON data"""
    print("🧪 Testing Simplified 2-Template Architecture with Actual Data")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        # 1. Setup test data
        records_loaded = setup_test_data()
        if records_loaded == 0:
            raise Exception("No GREYSON PO 4755 records found in ORDER_LIST source table")
        
        # 2. Load configuration
        print("\n⚙️  Loading configuration...")
        config = load_delta_sync_config('development')
        print(f"   ✅ Config loaded for {config.environment}")
        print(f"   📊 Architecture: Simplified 2-template flow")
        
        # 3. Create merge orchestrator
        print("\n🔄 Creating merge orchestrator...")
        orchestrator = MergeOrchestrator(config)
        
        # 4. Execute template sequence (LIVE mode - not dry run)
        print("\n🚀 Executing Simplified Merge Sequence (LIVE MODE)...")
        print("   📋 Template 1: merge_headers.j2 (swp_ORDER_LIST_V2 → ORDER_LIST_V2)")
        print("   📐 Template 2: unpivot_sizes_direct.j2 (ORDER_LIST_V2 → ORDER_LIST_LINES DIRECT)")
        print("   🗂️  ELIMINATED: merge_lines.j2 (handled by direct MERGE)")
        
        result = orchestrator.execute_template_sequence(new_orders_only=True, dry_run=False)
        
        # 5. Check execution results
        execution_time = time.time() - start_time
        
        print(f"\n📊 Execution Results:")
        print(f"   ⏱️  Total time: {execution_time:.2f}s")
        print(f"   ✅ Overall success: {result['success']}")
        print(f"   🏗️  Architecture: {result.get('architecture', 'unknown')}")
        
        for op_name, op_result in result.get('operations', {}).items():
            success_icon = "✅" if op_result.get('success') else "❌"
            records = op_result.get('records_affected', 0)
            print(f"   {success_icon} {op_name}: {records} records")
        
        # 6. Validate results
        if result['success']:
            validation_results = validate_results()
            
            # Calculate success metrics
            header_success = validation_results['headers']['sync_coverage'] >= 0.95
            lines_success = validation_results['lines']['sync_coverage'] >= 0.95
            overall_success = header_success and lines_success
            
            print(f"\n🎯 Success Metrics:")
            print(f"   📋 Header sync coverage: {validation_results['headers']['sync_coverage']:.1%} {'✅' if header_success else '❌'}")
            print(f"   📐 Lines sync coverage: {validation_results['lines']['sync_coverage']:.1%} {'✅' if lines_success else '❌'}")
            
            if overall_success:
                print(f"\n🎉 SIMPLIFIED ARCHITECTURE TEST SUCCESSFUL!")
                print(f"✅ 2-template flow executed successfully")
                print(f"✅ Direct MERGE to ORDER_LIST_LINES working")
                print(f"✅ No staging table dependency")
                print(f"✅ {validation_results['headers']['count']} headers processed")
                print(f"✅ {validation_results['lines']['count']} line records created")
                print(f"✅ Sync columns populated correctly")
                return True
            else:
                print(f"\n❌ VALIDATION FAILED: Sync coverage below 95% threshold")
                return False
        else:
            print(f"\n❌ EXECUTION FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simplified_architecture_with_data()
    exit(0 if success else 1)
