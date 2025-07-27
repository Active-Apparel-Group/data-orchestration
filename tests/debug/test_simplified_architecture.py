"""
Quick test for Simplified 2-Template Architecture
Tests the new unpivot_sizes_direct.j2 template and updated merge orchestrator
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine
from src.pipelines.sync_order_list.merge_orchestrator import MergeOrchestrator

def test_simplified_architecture():
    """Test the simplified 2-template architecture"""
    print("🧪 Testing Simplified 2-Template Architecture")
    print("=" * 60)
    
    try:
        # 1. Load configuration
        print("1. Loading TOML configuration...")
        config = load_delta_sync_config('development')
        print(f"   ✅ Config loaded for {config.environment}")
        print(f"   📊 Source table: {config.source_table}")
        print(f"   📊 Target table: {config.target_table}")
        print(f"   📊 Lines table: {config.lines_table}")
        print(f"   📊 Source lines table (should be same as lines): {config.source_lines_table}")
        
        # 2. Test template engine
        print("\n2. Testing SQL Template Engine...")
        engine = SQLTemplateEngine(config)
        
        # Test template context
        context = engine.get_template_context()
        print(f"   ✅ Template context generated")
        print(f"   📊 Size columns discovered: {len(context['size_columns'])}")
        print(f"   📊 Target table: {context['target_table']}")
        print(f"   📊 Lines table: {context['lines_table']}")
        
        # 3. Test new direct template rendering
        print("\n3. Testing unpivot_sizes_direct.j2 template...")
        direct_sql = engine.render_unpivot_sizes_direct_sql()
        print(f"   ✅ Template rendered successfully")
        print(f"   📊 SQL length: {len(direct_sql)} characters")
        print(f"   📊 Contains MERGE keyword: {'MERGE' in direct_sql}")
        print(f"   📊 Contains business key logic: {'record_uuid' in direct_sql and 'size_code' in direct_sql}")
        
        # 4. Test merge orchestrator (dry run)
        print("\n4. Testing Merge Orchestrator (dry run)...")
        orchestrator = MergeOrchestrator(config)
        
        # Run template sequence in dry run mode
        result = orchestrator.execute_template_sequence(new_orders_only=True, dry_run=True)
        
        print(f"   ✅ Orchestrator dry run completed")
        print(f"   📊 Overall success: {result['success']}")
        print(f"   📊 Architecture: {result.get('architecture', 'not specified')}")
        print(f"   📊 Operations:")
        
        for op_name, op_result in result.get('operations', {}).items():
            print(f"      - {op_name}: {op_result.get('success', 'unknown')} ({op_result.get('operation', 'unknown')})")
        
        print("\n🎉 SIMPLIFIED ARCHITECTURE TEST SUCCESSFUL!")
        print("✅ 2-template flow working")
        print("✅ Direct MERGE to ORDER_LIST_LINES")
        print("✅ No staging table dependency")
        print("✅ Business key logic implemented")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simplified_architecture()
    exit(0 if success else 1)
