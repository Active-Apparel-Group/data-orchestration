"""
Save the rendered merge SQL to a file for detailed analysis
"""
import sys
from pathlib import Path

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

print('🔍 Saving rendered merge SQL for analysis...')

try:
    # Initialize the same components as the integration test  
    config_path = str(Path(__file__).parent.parent.parent.parent / 'configs' / 'pipelines' / 'sync_order_list.toml')
    config = DeltaSyncConfig.from_toml(config_path, 'development')
    template_engine = SQLTemplateEngine(config)
    
    # Render the template
    rendered_sql = template_engine.render_merge_headers_sql()
    
    # Save to file
    output_file = Path(__file__).parent / 'rendered_merge_sql.sql'
    output_file.write_text(rendered_sql, encoding='utf-8')
    
    print(f'✅ SQL saved to: {output_file}')
    print(f'📏 SQL length: {len(rendered_sql)} characters')
    
    # Extract just the source query part to test separately
    source_start = rendered_sql.find('USING (')
    source_end = rendered_sql.find(') AS source')
    
    if source_start != -1 and source_end != -1:
        source_query = rendered_sql[source_start+6:source_end].strip()
        source_file = Path(__file__).parent / 'source_query_only.sql'
        source_file.write_text(f'SELECT COUNT(*) as record_count FROM (\n{source_query}\n) as test_source;', encoding='utf-8')
        print(f'✅ Source query saved to: {source_file}')
    
    print('\n🔍 Key sections to check:')
    print('1. WHERE clause in source query')
    print('2. JOIN condition: ON target.[AAG ORDER NUMBER] = source.[AAG ORDER NUMBER]')
    print('3. Column names and data types')
    
except Exception as e:
    print(f'❌ Error saving SQL: {e}')
    import traceback
    traceback.print_exc()
