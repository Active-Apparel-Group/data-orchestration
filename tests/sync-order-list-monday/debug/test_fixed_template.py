"""
Test the FIXED unpivot_sizes_direct.j2 template to verify it now creates 52 records.

This test compares the fixed template results against our working simplified MERGE.
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def test_fixed_template():
    """Test the fixed template produces the expected 52 records."""
    
    print("🧪 Testing FIXED unpivot_sizes_direct.j2 template...")
    
    # Load config (SAME AS WORKING TEST)
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as conn:
        cursor = conn.cursor()
        
        # Clean target table
        print("\n🧹 Cleaning ORDER_LIST_LINES...")
        cursor.execute("TRUNCATE TABLE ORDER_LIST_LINES")
        conn.commit()
        
        # Generate SQL using template engine (SAME AS INTEGRATION TEST)
        template_engine = SQLTemplateEngine(config)
        rendered_sql = template_engine.render_unpivot_sizes_direct_sql()
        
        print("\n📝 Executing fixed template SQL...")
        print("=" * 60)
        print("FULL GENERATED SQL:")
        print(rendered_sql)
        print("=" * 60)
        
        # Execute the template
        try:
            cursor.execute(rendered_sql)
            conn.commit()
            print("✅ Template executed successfully")
        except Exception as e:
            print(f"❌ Template execution failed: {str(e)}")
            return False
        
        # Check results
        print("\n📊 Checking results...")
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_LINES WHERE sync_state = 'PENDING'")
        result = cursor.fetchone()
        record_count = result[0] if result else 0
        
        print(f"✅ Fixed template result: {record_count} records")
        
        # Verify detailed breakdown
        cursor.execute("""
            SELECT 
                size_code,
                COUNT(*) as record_count,
                AVG(CAST(qty AS FLOAT)) as avg_qty
            FROM ORDER_LIST_LINES 
            WHERE sync_state = 'PENDING'
            GROUP BY size_code
            ORDER BY size_code
        """)
        
        details = cursor.fetchall()
        
        print("\n📋 Size breakdown:")
        for row in details:
            print(f"  {row[0]}: {row[1]} records (avg qty: {row[2]:.1f})")
        
        # Compare against expected
        if record_count == 52:
            print(f"\n🎉 SUCCESS! Fixed template created exactly 52 records as expected!")
            return True
        else:
            print(f"\n❌ ISSUE: Expected 52 records, got {record_count}")
            
            # Debug info
            if record_count == 0:
                print("🔍 Debugging 0 records...")
                cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_V2 WHERE sync_state = 'PENDING'")
                pending_count = cursor.fetchone()[0]
                print(f"   PENDING records in ORDER_LIST_V2: {pending_count}")
                
                cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_V2 WHERE sync_state = 'PENDING' AND [XL] > 0")
                xl_count = cursor.fetchone()[0]
                print(f"   XL > 0 records in PENDING: {xl_count}")
            
            return False

if __name__ == "__main__":
    try:
        success = test_fixed_template()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
