"""
Test the actual merge template execution with detailed error reporting
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

print('🔍 Testing actual merge template execution...')

try:
    # Initialize the same components as the integration test
    config = DeltaSyncConfig('configs/pipelines/sync_order_list.toml', 'development')
    template_engine = SQLTemplateEngine(config)
    
    print('📊 Rendering merge_headers.j2 template...')
    
    # Render the template with the same context
    context = template_engine.get_template_context()
    
    print(f"📋 Template context summary:")
    print(f"  Business columns: {len(context['business_columns'])}")
    print(f"  Size columns: {len(context['size_columns'])}")
    print(f"  Hash columns: {len(context['hash_columns'])}")
    print(f"  Source table: {context['source_table']}")
    print(f"  Target table: {context['target_table']}")
    
    # Render the template
    rendered_sql = template_engine.render_template('merge_headers.j2', context)
    
    print('✅ Template rendered successfully')
    print(f'📏 SQL length: {len(rendered_sql)} characters')
    
    # Try to execute the rendered SQL with better error handling
    print('\n🔍 Executing rendered merge template...')
    
    conn = db.get_connection('orders')
    cursor = conn.cursor()
    
    try:
        # Execute with transaction for safety
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(rendered_sql)
        
        # Check if there are results to fetch
        try:
            results = cursor.fetchall()
            if results:
                print('📊 Merge execution results:')
                for row in results:
                    print(f'  {row}')
            else:
                print('📊 No results returned from merge')
        except Exception as fetch_e:
            print(f'📊 No fetchable results (this is normal for merge): {fetch_e}')
        
        # Check the row count
        row_count = cursor.rowcount
        print(f'📊 Rows affected by merge: {row_count}')
        
        # Check what's in the target table now
        cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_V2")
        target_count = cursor.fetchone()[0]
        print(f'📊 Records in target table after merge: {target_count}')
        
        cursor.execute("ROLLBACK TRANSACTION")  # Rollback for testing
        print('✅ Transaction rolled back')
        
    except Exception as exec_e:
        print(f'❌ Error executing merge: {exec_e}')
        cursor.execute("ROLLBACK TRANSACTION")
        # Print the first 1000 characters of the SQL for debugging
        print(f'\n🔍 SQL snippet (first 1000 chars):')
        print(rendered_sql[:1000])
        print('...')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error in template execution test: {e}')
    import traceback
    traceback.print_exc()
