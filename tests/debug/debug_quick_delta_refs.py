#!/usr/bin/env python3
"""
Quick DELTA Reference Diagnostic
Purpose: Debug Task 19.14.2 failures using validated import pattern
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List

# Proven import pattern from successful integration tests
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Hybrid imports (validated across 15+ successful tests)
from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import load_delta_sync_config  
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def main():
    """Quick diagnostic of DELTA references in templates"""
    try:
        # Use load_delta_sync_config (modern approach, no file paths needed)
        config = load_delta_sync_config()
        logger.info(f"Configuration loaded: {config.source_table} -> {config.target_table}")
        
        # Initialize template engine with config
        template_engine = SQLTemplateEngine(config)
        
        # Test each template
        templates = [
            ("merge_headers", template_engine.render_merge_headers_sql),
            ("unpivot_sizes", template_engine.render_unpivot_sizes_sql),
            ("merge_lines", template_engine.render_merge_lines_sql)
        ]
        
        for template_name, render_func in templates:
            logger.info(f"🔍 Checking {template_name}.j2...")
            
            try:
                rendered_sql = render_func()
                
                # Find all DELTA occurrences 
                delta_matches = []
                lines = rendered_sql.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if 'DELTA' in line.upper():
                        delta_matches.append((i, line.strip()))
                
                if delta_matches:
                    logger.warning(f"❌ {template_name}: Found {len(delta_matches)} DELTA references")
                    for line_num, content in delta_matches[:5]:  # Show first 5
                        logger.warning(f"   Line {line_num}: {content}")
                        
                    # Save for inspection (using current directory)
                    debug_file = Path(f"debug_{template_name}.sql")
                    with open(debug_file, 'w') as f:
                        f.write(rendered_sql)
                    logger.info(f"   Saved to: {debug_file}")
                else:
                    logger.info(f"✅ {template_name}: No DELTA references found")
                    
            except Exception as e:
                logger.error(f"❌ {template_name}: Rendering failed: {e}")
    
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")

if __name__ == "__main__":
    main()
