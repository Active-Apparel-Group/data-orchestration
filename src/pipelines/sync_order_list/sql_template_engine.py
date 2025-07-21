"""
SQL Template Engine for ORDER_LIST V2 Delta Sync
===============================================
Purpose: Modern SQL generation using Jinja2 templates + TOML configuration
Location: src/pipelines/sync_order_list/sql_template_engine.py
Created: 2025-07-20 (Modern Python SQL Management)

This module provides a clean, maintainable way to generate SQL operations
using Jinja2 templates with TOML-driven configuration for dynamic size columns.

Architecture:
- SQL Templates: sql/templates/*.j2 (Jinja2 templates with placeholders)
- Configuration: TOML file provides table names, columns, size detection
- Python Engine: Renders templates with config values for execution

Benefits:
- No hardcoded size columns in SQL (TOML-driven)
- Clean separation of SQL logic and configuration
- Type-safe template rendering with validation
- Version-controlled SQL templates
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import jinja2

# Legacy transition support pattern - SAME AS WORKING TESTS
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

# Import with working pattern
from pipelines.utils import logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

class SQLTemplateEngine:
    """
    Modern SQL template engine using Jinja2 for dynamic SQL generation
    """
    
    def __init__(self, config: DeltaSyncConfig):
        """
        Initialize SQL template engine with TOML configuration
        
        Args:
            config: Delta sync configuration from TOML file
        """
        self.config = config
        self.logger = logger.get_logger(__name__)
        
        # Setup Jinja2 template environment - FIXED PATH
        # Templates are in root sql/templates/, not src/sql/templates/
        template_dir = Path(__file__).parent.parent.parent.parent / "sql" / "templates"
        self.logger.info(f"SQL template engine initialized with templates from: {template_dir}")
        
        if not template_dir.exists():
            self.logger.error(f"Template directory not found: {template_dir}")
            raise FileNotFoundError(f"Templates directory not found: {template_dir}")
        
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        self.logger.info(f"SQL template engine initialized with templates from: {template_dir}")
    
    def get_template_context(self) -> Dict[str, Any]:
        """
        Get complete template context from TOML configuration
        
        Returns:
            Dictionary with all template variables for SQL generation
        """
        # Get dynamic size columns from TOML
        size_columns = self.config.get_dynamic_size_columns()
        business_columns = self.config.get_business_columns()
        
        # Table names with proper schema
        source_table = self.config.get_full_table_name('source')
        target_table = self.config.get_full_table_name('target')
        lines_table = self.config.get_full_table_name('lines')
        source_lines_table = self.config.get_full_table_name('source_lines')
        delta_table = self.config.get_full_table_name('delta')
        lines_delta_table = self.config.get_full_table_name('lines_delta')
        
        context = {
            # Table Configuration
            'source_table': source_table,
            'target_table': target_table,
            'lines_table': lines_table,
            'source_lines_table': source_lines_table,
            'delta_table': delta_table,
            'lines_delta_table': lines_delta_table,
            
            # Column Configuration (Dynamic from TOML)
            'business_columns': business_columns,
            'size_columns': size_columns,
            'hash_columns': self.config.hash_columns,
            
            # Metadata
            'environment': self.config.board_type,
            'database': self.config.database_connection,
            'schema': self.config.database_schema
        }
        
        self.logger.debug(f"Template context: {len(size_columns)} size columns, {len(business_columns)} business columns")
        
        return context
    
    def render_merge_headers_sql(self) -> str:
        """
        Render 003_merge_headers SQL from Jinja2 template
        
        Returns:
            Generated SQL string for header merge operation
        """
        try:
            template = self.jinja_env.get_template('merge_headers.j2')
            context = self.get_template_context()
            
            sql = template.render(**context)
            
            self.logger.info(f"✅ Rendered merge_headers SQL: {len(context['size_columns'])} size columns, {len(context['business_columns'])} business columns")
            
            return sql
            
        except Exception as e:
            self.logger.exception(f"❌ Failed to render merge_headers SQL: {e}")
            raise
    
    def render_unpivot_sizes_sql(self) -> str:
        """
        Render 004_unpivot_sizes SQL from Jinja2 template
        
        Returns:
            Generated SQL string for size unpivot operation
        """
        try:
            template = self.jinja_env.get_template('unpivot_sizes.j2')
            context = self.get_template_context()
            
            sql = template.render(**context)
            
            self.logger.info(f"✅ Rendered unpivot_sizes SQL: {len(context['size_columns'])} size columns")
            
            return sql
            
        except Exception as e:
            self.logger.exception(f"❌ Failed to render unpivot_sizes SQL: {e}")
            raise
    
    def render_merge_lines_sql(self) -> str:
        """
        Render 005_merge_lines SQL from Jinja2 template
        
        Returns:
            Generated SQL string for lines merge operation
        """
        try:
            template = self.jinja_env.get_template('merge_lines.j2')
            context = self.get_template_context()
            
            sql = template.render(**context)
            
            self.logger.info(f"✅ Rendered merge_lines SQL")
            
            return sql
            
        except Exception as e:
            self.logger.exception(f"❌ Failed to render merge_lines SQL: {e}")
            raise
    
    def validate_template_context(self) -> Dict[str, Any]:
        """
        Validate template context for completeness
        
        Returns:
            Validation results with success status and details
        """
        context = self.get_template_context()
        validations = {}
        
        # Validate size columns
        validations['size_columns'] = {
            'count': len(context['size_columns']),
            'valid': len(context['size_columns']) > 0,
            'sample': context['size_columns'][:5] if context['size_columns'] else []
        }
        
        # Validate business columns
        validations['business_columns'] = {
            'count': len(context['business_columns']),
            'valid': len(context['business_columns']) > 0,
            'required': ['CUSTOMER NAME', 'AAG ORDER NUMBER', 'CUSTOMER STYLE'],  # Fixed - use actual column names
            'missing': [col for col in ['CUSTOMER NAME', 'AAG ORDER NUMBER', 'CUSTOMER STYLE'] 
                       if col not in context['business_columns']]
        }
        
        # Validate table names
        validations['tables'] = {
            'source': context['source_table'],
            'target': context['target_table'],
            'lines': context['lines_table'],
            'delta': context['delta_table'],
            'all_present': all([
                context['source_table'], context['target_table'], 
                context['lines_table'], context['delta_table']
            ])
        }
        
        overall_valid = (
            validations['size_columns']['valid'] and
            validations['business_columns']['valid'] and 
            validations['tables']['all_present'] and
            len(validations['business_columns']['missing']) == 0
        )
        
        return {
            'valid': overall_valid,
            'validations': validations,
            'context_summary': {
                'size_columns_count': len(context['size_columns']),
                'business_columns_count': len(context['business_columns']),
                'environment': context['environment'],
                'database': context['database']
            }
        }


# Factory function for easy usage
def create_sql_template_engine(environment: str = 'dev') -> SQLTemplateEngine:
    """
    Factory function to create SQLTemplateEngine instance
    
    Args:
        environment: 'dev', 'prod', or path to TOML file
        
    Returns:
        Configured SQLTemplateEngine instance
    """
    from src.pipelines.sync_order_list.config_parser import load_delta_sync_config
    
    config = load_delta_sync_config(environment)
    return SQLTemplateEngine(config)


# Main execution for testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        engine = create_sql_template_engine('dev')
        
        print("🧪 Testing SQL Template Engine")
        print("-" * 50)
        
        # Validate context
        validation = engine.validate_template_context()
        print(f"Context validation: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
        
        if validation['valid']:
            summary = validation['context_summary']
            print(f"Size columns: {summary['size_columns_count']}")
            print(f"Business columns: {summary['business_columns_count']}")
            print(f"Environment: {summary['environment']}")
            
            # Test template rendering
            print(f"\n🔧 Testing Template Rendering")
            
            # Test merge headers
            headers_sql = engine.render_merge_headers_sql()
            print(f"✅ Merge headers SQL: {len(headers_sql):,} characters")
            
            # Test unpivot sizes
            unpivot_sql = engine.render_unpivot_sizes_sql()
            print(f"✅ Unpivot sizes SQL: {len(unpivot_sql):,} characters")
            
            # Test merge lines
            lines_sql = engine.render_merge_lines_sql()
            print(f"✅ Merge lines SQL: {len(lines_sql):,} characters")
            
            print(f"\n🎯 Template engine ready for V2 delta sync!")
            
        else:
            print("❌ Context validation failed:")
            for validation_name, details in validation['validations'].items():
                print(f"  {validation_name}: {details}")
        
    except Exception as e:
        print(f"❌ Template engine test failed: {e}")
        sys.exit(1)
