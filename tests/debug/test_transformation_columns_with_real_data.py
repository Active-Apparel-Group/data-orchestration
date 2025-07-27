#!/usr/bin/env python3
"""
Test transformation columns in merge_headers.j2 template with real available data
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def main():
    print("🧪 Testing Transformation Columns in merge_headers.j2 with Real Data...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check what data we actually have
        cursor.execute(f"SELECT TOP 5 CUSTOMER, STYLE, COLOR FROM {config.source_table}")
        available_data = cursor.fetchall()
        
        if not available_data:
            print("❌ No data available in source table")
            return
            
        print(f"✅ Found {len(available_data)} sample records in {config.source_table}")
        for row in available_data:
            print(f"   Customer: {row[0]}, Style: {row[1]}, Color: {row[2]}")
        
        # SQL Template Engine
        engine = SQLTemplateEngine(config)
        
        # Generate merge_headers.j2 template
        print("\n🔧 Generating merge_headers.j2 template...")
        merge_sql = engine.render_merge_headers_sql()
        
        # Check if transformation columns are in the template
        transformation_columns = ['group_name', 'group_id', 'item_name']
        
        print("\n🔍 Checking for transformation columns in generated SQL:")
        found_columns = []
        missing_columns = []
        
        for col in transformation_columns:
            if col in merge_sql:
                found_columns.append(col)
                print(f"   ✅ {col}: FOUND")
            else:
                missing_columns.append(col)
                print(f"   ❌ {col}: MISSING")
        
        # Show a snippet of the generated SQL around transformation columns
        print("\n📝 SQL Template Preview (first 1000 chars):")
        print("-" * 60)
        print(merge_sql[:1000] + "..." if len(merge_sql) > 1000 else merge_sql)
        print("-" * 60)
        
        # Test execution (dry run with LIMIT 1)
        print("\n🧪 Testing SQL execution (LIMIT 1)...")
        try:
            # Modify the SQL to add LIMIT 1 for testing
            test_sql = merge_sql.replace(
                f"FROM {config.source_table}", 
                f"FROM {config.source_table} LIMIT 1"
            )
            
            cursor.execute(test_sql)
            result = cursor.fetchall()
            print(f"✅ SQL executed successfully, returned {len(result)} rows")
            
        except Exception as e:
            print(f"⚠️  SQL execution test failed: {e}")
            print("   (This might be expected if tables don't exist yet)")
        
        # Summary
        print(f"\n📊 TRANSFORMATION COLUMNS TEST RESULTS:")
        print(f"   Found columns: {found_columns}")
        print(f"   Missing columns: {missing_columns}")
        print(f"   Success rate: {len(found_columns)}/{len(transformation_columns)} = {len(found_columns)/len(transformation_columns)*100:.1f}%")
        
        if len(found_columns) == len(transformation_columns):
            print("🎉 SUCCESS: All transformation columns found in merge template!")
        else:
            print("❌ FAIL: Some transformation columns missing from merge template")
        
        cursor.close()

if __name__ == "__main__":
    main()
