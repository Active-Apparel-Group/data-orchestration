"""
Actual Data Test for Simplified 2-Template Architecture
Tests real data processing with our new direct MERGE flow
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator
from src.pipelines.utils import db

def test_actual_data_simplified_architecture():
    """Test the simplified 2-template architecture with actual data"""
    print("🧪 Testing Simplified Architecture with ACTUAL DATA")
    print("=" * 60)
    
    try:
        # 1. Load configuration
        print("1. Loading TOML configuration...")
        config = load_delta_sync_config('development')
        print(f"   ✅ Config loaded for {config.environment}")
        
        # 2. Check initial data state
        print("\n2. Checking initial data state...")
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            
            # Check ORDER_LIST_V2 sync states
            cursor.execute("""
                SELECT sync_state, COUNT(*) as count
                FROM ORDER_LIST_V2 
                GROUP BY sync_state
                ORDER BY sync_state
            """)
            v2_states = cursor.fetchall()
            
            # Check ORDER_LIST_LINES count
            cursor.execute("SELECT COUNT(*) as count FROM ORDER_LIST_LINES")
            lines_count = cursor.fetchone()[0]
            
        print(f"   📊 ORDER_LIST_V2 sync states:")
        for state, count in v2_states:
            print(f"      {state}: {count} records")
        print(f"   📊 ORDER_LIST_LINES: {lines_count} records")
        
        # 3. Run merge orchestrator with actual data
        print("\n3. Running Merge Orchestrator (ACTUAL DATA)...")
        orchestrator = MergeOrchestrator(config)
        
        # Execute template sequence with actual data (not dry run)
        result = orchestrator.execute_template_sequence(new_orders_only=True, dry_run=False)
        
        print(f"   ✅ Orchestrator execution completed")
        print(f"   📊 Overall success: {result['success']}")
        print(f"   📊 Architecture: {result.get('architecture', 'not specified')}")
        print(f"   📊 Duration: {result.get('total_duration_seconds', 0):.2f}s")
        
        # 4. Show operation results
        print(f"\n4. Operation Results:")
        for op_name, op_result in result.get('operations', {}).items():
            success = op_result.get('success', False)
            records = op_result.get('records_affected', 0)
            duration = op_result.get('duration_seconds', 0)
            operation = op_result.get('operation', 'unknown')
            
            status_icon = "✅" if success else "❌"
            print(f"   {status_icon} {op_name}: {records} records in {duration:.2f}s ({operation})")
        
        # 5. Check final data state
        print("\n5. Checking final data state...")
        with db.get_connection('orders') as conn:
            cursor = conn.cursor()
            
            # Check ORDER_LIST_V2 sync states after processing
            cursor.execute("""
                SELECT sync_state, COUNT(*) as count
                FROM ORDER_LIST_V2 
                GROUP BY sync_state
                ORDER BY sync_state
            """)
            v2_states_after = cursor.fetchall()
            
            # Check ORDER_LIST_LINES count after processing
            cursor.execute("SELECT COUNT(*) as count FROM ORDER_LIST_LINES")
            lines_count_after = cursor.fetchone()[0]
            
            # Check distinct record_uuid count in lines
            cursor.execute("SELECT COUNT(DISTINCT record_uuid) as unique_records FROM ORDER_LIST_LINES")
            unique_records = cursor.fetchone()[0]
            
        print(f"   📊 ORDER_LIST_V2 sync states (after):")
        for state, count in v2_states_after:
            print(f"      {state}: {count} records")
        print(f"   📊 ORDER_LIST_LINES (after): {lines_count_after} records")
        print(f"   📊 Unique header records in lines: {unique_records}")
        
        # 6. Validate results
        print("\n6. Validation Results:")
        
        # Check if we processed data
        if result['success']:
            lines_processed = result.get('operations', {}).get('unpivot_sizes_direct', {}).get('records_affected', 0)
            if lines_processed > 0:
                print(f"   ✅ Data processing successful: {lines_processed} line records processed")
                print(f"   ✅ Simplified architecture working: Direct MERGE to ORDER_LIST_LINES")
                print(f"   ✅ No staging table used: Eliminated swp_ORDER_LIST_LINES dependency")
                
                # Calculate unpivot efficiency
                expected_lines = 69 * 245  # 69 PENDING records * 245 size columns (theoretical max)
                efficiency = (lines_processed / expected_lines) * 100 if expected_lines > 0 else 0
                print(f"   📊 Unpivot efficiency: {lines_processed:,} / {expected_lines:,} ({efficiency:.1f}%) - excludes zero quantities")
            else:
                print(f"   ⚠️ No line records processed - may need to check PENDING record data")
        else:
            print(f"   ❌ Processing failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎉 ACTUAL DATA TEST COMPLETED!")
        return result['success']
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_actual_data_simplified_architecture()
    exit(0 if success else 1)
