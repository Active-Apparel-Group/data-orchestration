#!/usr/bin/env python3
"""
Debug: Examine the actual merge SQL to find the issue
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

def examine_merge_sql():
    """Look at the actual merge SQL to find the issue"""
    print("🔍 Examining Merge SQL Template")
    
    config = load_delta_sync_config()
    template_engine = SQLTemplateEngine(config)
    
    # Get size columns first
    conn = db.get_connection(config.db_key)
    size_columns = template_engine._discover_size_columns(config.source_table, conn)
    conn.close()
    
    # Render the merge template with correct context
    context = {
        'source_table': config.source_table,
        'target_table': config.target_table,
        'business_columns': ['CUSTOMER NAME', 'PO NUMBER', 'CUSTOMER STYLE', 'TOTAL QTY'],
        'size_columns': size_columns
    }
    
    # Render the template
    sql = template_engine.render_template('merge_headers.j2', context)
    
    print("📋 RENDERED MERGE SQL:")
    print("=" * 80)
    print(sql[:2000])  # First 2000 characters
    print("...")
    print("=" * 80)
    
    # Look for the key parts
    if "WHERE" in sql:
        where_section = sql[sql.find("WHERE"):sql.find("WHERE")+200]
        print(f"\n🎯 WHERE CLAUSE: {where_section}")
    
    if "WHEN NOT MATCHED" in sql:
        not_matched_section = sql[sql.find("WHEN NOT MATCHED"):sql.find("WHEN NOT MATCHED")+300]
        print(f"\n🎯 INSERT CLAUSE: {not_matched_section}")
    
    if "WHEN MATCHED" in sql:
        matched_section = sql[sql.find("WHEN MATCHED"):sql.find("WHEN MATCHED")+200]
        print(f"\n🎯 UPDATE CLAUSE: {matched_section}")

if __name__ == "__main__":
    examine_merge_sql()
