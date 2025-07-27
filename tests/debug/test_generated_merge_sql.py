#!/usr/bin/env python3
"""
Test the generated merge_headers.j2 SQL to debug syntax issues
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def main():
    print("🔧 Testing Generated merge_headers.j2 SQL for Syntax Issues...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # SQL Template Engine
    engine = SQLTemplateEngine(config)
    
    # Generate merge_headers.j2 template (with dynamic detection)
    print("\n📝 Generating merge_headers.j2 template (dynamic mode)...")
    merge_sql = engine.render_merge_headers_sql()
    
    # Show the generated SQL
    print("\n" + "="*80)
    print("GENERATED SQL:")
    print("="*80)
    print(merge_sql)
    print("="*80)
    
    # Look for potential syntax issues
    print("\n🔍 Checking for potential syntax issues...")
    
    # Check for trailing commas in INSERT sections
    lines = merge_sql.split('\n')
    for i, line in enumerate(lines):
        if 'INSERT (' in line:
            print(f"\n📋 Found INSERT section starting at line {i+1}")
            # Look for the next few lines after INSERT
            for j in range(i, min(i+20, len(lines))):
                current_line = lines[j].strip()
                if current_line:
                    print(f"  {j+1:3d}: {current_line}")
                    if 'VALUES' in current_line:
                        break
        
        if 'VALUES (' in line:
            print(f"\n💼 Found VALUES section starting at line {i+1}")
            # Look for the next few lines after VALUES
            for j in range(i, min(i+20, len(lines))):
                current_line = lines[j].strip()
                if current_line:
                    print(f"  {j+1:3d}: {current_line}")
                    if ')' == current_line or current_line.endswith(')'):
                        break
    
    # Check for common syntax issues
    issues = []
    
    if ',)' in merge_sql:
        issues.append("❌ Trailing comma before closing parenthesis found")
    
    if ', VALUES' in merge_sql:
        issues.append("❌ Comma immediately before VALUES keyword found")
        
    if merge_sql.count('INSERT (') != merge_sql.count('VALUES ('):
        issues.append("❌ Mismatch between INSERT and VALUES statements")
    
    if issues:
        print(f"\n🚨 SYNTAX ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"\n✅ No obvious syntax issues found")
    
    # Count columns in INSERT vs VALUES
    print(f"\n📊 SQL Analysis:")
    insert_sections = [line for line in lines if 'INSERT (' in line]
    values_sections = [line for line in lines if 'VALUES (' in line]
    
    print(f"  INSERT statements: {len(insert_sections)}")
    print(f"  VALUES statements: {len(values_sections)}")
    
    # Look for column count in first INSERT/VALUES pair
    if insert_sections and values_sections:
        # Find the lines between INSERT ( and )
        insert_start = None
        for i, line in enumerate(lines):
            if 'INSERT (' in line:
                insert_start = i
                break
        
        if insert_start:
            insert_columns = []
            for i in range(insert_start, len(lines)):
                line = lines[i].strip()
                if line.startswith('[') and line.endswith(','):
                    col_name = line.strip('[],')
                    insert_columns.append(col_name)
                elif ')' in line:
                    break
            
            print(f"  INSERT columns found: {len(insert_columns)}")
            if len(insert_columns) <= 10:
                print(f"    Columns: {insert_columns}")

if __name__ == "__main__":
    main()
