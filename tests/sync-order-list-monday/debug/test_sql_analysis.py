"""
SQL Analysis Test - Find the MERGE Filtering Issue
==================================================
Purpose: Analyze the generated SQL to find what's filtering out all 52 records
Strategy: Extract and test each part of the MERGE operation separately

ROOT CAUSE: MERGE executes successfully but filters out all records
"""

import sys
from pathlib import Path

# Legacy transition support pattern
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def analyze_generated_sql():
    """Analyze the generated SQL to find the filtering issue"""
    
    print("🔍 SQL ANALYSIS - FIND MERGE FILTERING ISSUE")
    print("="*60)
    
    # Load config and template engine
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    template_engine = SQLTemplateEngine(config)
    
    # Generate SQL
    generated_sql = template_engine.render_unpivot_sizes_direct_sql()
    
    print("📝 Generated SQL Analysis:")
    print("="*40)
    
    # Print key sections of the SQL
    lines = generated_sql.split('\n')
    
    print("🔍 UNPIVOT Section:")
    in_unpivot = False
    for i, line in enumerate(lines):
        if 'UNPIVOT' in line:
            in_unpivot = True
        if in_unpivot:
            print(f"  {line}")
            if ')' in line and 'AS sizes' in line:
                break
    
    print("\n🔍 WHERE Clause:")
    in_where = False
    for i, line in enumerate(lines):
        if line.strip().startswith('WHERE') and 'unpivoted' in line:
            in_where = True
        if in_where:
            print(f"  {line}")
            if line.strip().startswith(') AS source'):
                break
    
    print("\n🔍 MERGE ON Clause:")
    in_on = False
    for i, line in enumerate(lines):
        if line.strip().startswith('ON target.record_uuid'):
            in_on = True
        if in_on:
            print(f"  {line}")
            if 'AND target.size_code' in line:
                break
    
    # Test the exact source subquery
    print("\n🧪 TESTING SOURCE SUBQUERY...")
    
    # Extract just the source part for testing
    source_test = '''
        SELECT COUNT(*) FROM (
            SELECT 
                unpivoted.record_uuid,
                unpivoted.size_code,
                unpivoted.qty,
                CONVERT(CHAR(64), HASHBYTES('SHA2_256', 
                    CONCAT_WS('|', unpivoted.record_uuid, unpivoted.size_code, unpivoted.qty)), 2) as row_hash,
                'NEW' as sync_state,
                GETUTCDATE() as created_at,
                GETUTCDATE() as updated_at
            FROM (
                SELECT 
                    record_uuid,
                    sync_state,
                    size_code,
                    qty
                FROM ORDER_LIST_V2
                UNPIVOT (
                    qty FOR size_code IN ([XL])
                ) AS sizes
            ) AS unpivoted
            WHERE unpivoted.sync_state = 'PENDING'
            AND unpivoted.qty > 0
        ) AS source_test
    '''
    
    with db.get_connection(config.db_key) as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(source_test)
            source_count = cursor.fetchone()[0]
            print(f"✅ Source subquery produces: {source_count} records")
            
            if source_count == 0:
                print("❌ ISSUE FOUND: Source subquery filters out all records!")
                print("🔍 Checking individual filters...")
                
                # Test without qty > 0 filter
                test_without_qty_filter = source_test.replace("AND unpivoted.qty > 0", "")
                cursor.execute(test_without_qty_filter)
                without_qty = cursor.fetchone()[0]
                print(f"  Without qty > 0 filter: {without_qty} records")
                
                # Test without sync_state filter  
                test_without_sync_filter = source_test.replace("WHERE unpivoted.sync_state = 'PENDING'", "WHERE 1=1")
                cursor.execute(test_without_sync_filter)
                without_sync = cursor.fetchone()[0]
                print(f"  Without sync_state filter: {without_sync} records")
                
            else:
                print("✅ Source subquery is correct - issue must be in MERGE logic")
                
        except Exception as e:
            print(f"❌ Source subquery test failed: {str(e)}")

if __name__ == "__main__":
    analyze_generated_sql()
