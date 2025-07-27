"""
Debug the generated SQL to see what size columns are being used
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

def debug_generated_sql():
    """Check the generated SQL to see what size columns are being unpivoted"""
    print("🔍 Debugging Generated SQL")
    print("=" * 50)
    
    # Load config and engine
    config = load_delta_sync_config('development')
    engine = SQLTemplateEngine(config)
    
    # Generate the SQL
    sql = engine.render_unpivot_sizes_direct_sql()
    
    # Find the UNPIVOT section
    lines = sql.split('\n')
    unpivot_start = -1
    unpivot_end = -1
    
    for i, line in enumerate(lines):
        if 'qty FOR size_code IN (' in line:
            unpivot_start = i
        if unpivot_start != -1 and ')' in line and 'AS sizes' in line:
            unpivot_end = i
            break
    
    if unpivot_start != -1 and unpivot_end != -1:
        print("UNPIVOT section of generated SQL:")
        print("-" * 40)
        for i in range(max(0, unpivot_start-1), min(len(lines), unpivot_end+2)):
            print(f"{i:3d}: {lines[i]}")
        print("-" * 40)
    
    # Check what size columns are being used
    context = engine.get_template_context()
    size_columns = context['size_columns']
    
    print(f"\nSize columns being used ({len(size_columns)} total):")
    print("First 20:", size_columns[:20])
    print("Last 20:", size_columns[-20:])
    
    # Check if standard sizes are in the list
    standard_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    found_standard = [size for size in standard_sizes if size in size_columns]
    print(f"\nStandard sizes found: {found_standard}")
    
    return sql

if __name__ == "__main__":
    sql = debug_generated_sql()
    
    # Save SQL for inspection
    with open('debug_generated_unpivot.sql', 'w') as f:
        f.write(sql)
    print(f"\nGenerated SQL saved to: debug_generated_unpivot.sql")
