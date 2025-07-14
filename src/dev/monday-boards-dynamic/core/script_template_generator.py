#!/usr/bin/env python3
"""
Script Template Generator - Generate Python extraction scripts from board schemas

This module generates customized Python extraction scripts based on Monday.com
board schemas discovered by the BoardSchemaGenerator. It uses Jinja2 templates
to create production-ready scripts that preserve all the performance optimizations
and error handling patterns from the reference implementation.

Key Features:
- Template-driven script generation using Jinja2
- Board-specific GraphQL query generation
- Type-specific conversion logic injection
- Performance configuration (batch size, workers, etc.)
- Integration with existing infrastructure (db_helper, config.yaml)
- Comprehensive error handling and logging

Usage:
    from core.script_template_generator import ScriptTemplateGenerator
    
    generator = ScriptTemplateGenerator()
    script_content = generator.generate_extraction_script(board_schema)
    generator.save_script(script_content, "get_board_customer_orders.py")
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import logging

# Jinja2 for template rendering
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    raise ImportError("Jinja2 is required. Install with: pip install jinja2")

# Repository root discovery (using the same pattern as existing scripts)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

try:
    import db_helper as db
    import mapping_helper as mapping
except ImportError as e:
    raise ImportError(f"Failed to import utilities: {e}. Ensure utils directory is accessible.")

# Import BoardSchema from the schema generator
sys.path.insert(0, str(Path(__file__).parent))
from board_schema_generator import BoardSchema, ColumnDefinition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptTemplateGeneratorError(Exception):
    """Raised when script template generation fails"""
    pass


class ScriptTemplateGenerator:
    """
    Generates Python extraction scripts from Monday.com board schemas
    """
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the script template generator
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.template_dir = Path(template_dir)
        
        if not self.template_dir.exists():
            raise ScriptTemplateGeneratorError(f"Template directory not found: {template_dir}")
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.info(f"Initialized ScriptTemplateGenerator with template dir: {template_dir}")
    
    def generate_extraction_script(
        self, 
        board_schema: BoardSchema, 
        script_config: Dict[str, Any] = None
    ) -> str:
        """
        Generate a Python extraction script from board schema
        
        Args:
            board_schema: BoardSchema object from BoardSchemaGenerator
            script_config: Optional configuration overrides
            
        Returns:
            Generated Python script content
        """
        logger.info(f"Generating extraction script for board '{board_schema.board_name}'")
        
        # Default configuration
        default_config = {
            "batch_size": 100,
            "max_workers": 8,
            "rate_limit_delay": 0.1,
            "timeout": 30
        }
        
        # Merge with provided config
        config = {**default_config, **(script_config or {})}
        
        # Prepare template variables
        template_vars = self._prepare_template_variables(board_schema, config)
        
        try:            # Load and render the template
            template = self.env.get_template("board_extractor_production.py.j2")  # Using production template
            script_content = template.render(**template_vars)
            
            logger.info(f"Successfully generated script ({len(script_content)} characters)")
            return script_content
            
        except Exception as e:
            raise ScriptTemplateGeneratorError(f"Failed to render template: {e}")
    
    def _prepare_template_variables(self, board_schema: BoardSchema, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare all variables needed for template rendering
        
        Args:
            board_schema: BoardSchema object
            config: Script configuration
            
        Returns:
            Dictionary of template variables
        """
        # Extract unique column types for GraphQL query generation
        unique_column_types = self._get_unique_column_types(board_schema.columns)
        
        # Prepare column data for template
        columns_data = []
        for col in board_schema.columns:
            col_data = col.to_dict()
            # Add any additional processing here if needed
            columns_data.append(col_data)
        
        # Generate sanitized script name
        script_name = self._generate_script_name(board_schema.board_name)
        
        template_vars = {
            # Board configuration object (matches template expectation)
            "board_config": {
                "board_id": board_schema.board_id,
                "board_name": board_schema.board_name,
                "table_name": board_schema.table_name,
                "database": board_schema.database,
                "columns": columns_data
            },
              # Board config key for mapping_helper lookup
            "board_config_key": "coo_planning",  # Default - should be parameterized
            "board_key": board_schema.board_name.lower().replace(" ", "_").replace("-", "_"),  # For YAML schema decisions
            
            # Generation metadata
            "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            
            # Legacy variables for backwards compatibility
            "board_id": board_schema.board_id,
            "board_name": board_schema.board_name,
            "table_name": board_schema.table_name,
            "database": board_schema.database,
            "columns": columns_data,
            "unique_column_types": unique_column_types,
            "total_columns": len(board_schema.columns),
            "batch_size": config["batch_size"],
            "max_workers": config["max_workers"],
            "rate_limit_delay": config["rate_limit_delay"],
            "timeout": config["timeout"],
            "script_name": script_name,
            "generated_by": "Dynamic Monday.com Board Template System",
            "template_version": "1.0",
            "board_metadata": board_schema.metadata
        }
        
        logger.debug(f"Prepared template variables for {len(columns_data)} columns")
        return template_vars
    
    def _get_unique_column_types(self, columns: List[ColumnDefinition]) -> Set[str]:
        """
        Extract unique Monday.com column types for GraphQL query generation
        
        Args:
            columns: List of ColumnDefinition objects
            
        Returns:
            Set of unique column type names for GraphQL fragments
        """
        type_mapping = {
            "text": "Text",
            "long_text": "LongText", 
            "numbers": "Numbers",
            "status": "Status",
            "dropdown": "Dropdown",
            "date": "Date",
            "people": "People",
            "dependency": "Dependency",
            "mirror": "Mirror",
            "board_relation": "BoardRelation",
            "formula": "Formula",
            "checkbox": "Checkbox",
            "rating": "Rating",
            "email": "Email",
            "phone": "Phone",
            "link": "Link",
            "file": "File",
            "tags": "Tags",
            "timeline": "Timeline",
            "item_id": "ItemId"
        }
        
        unique_types = set()
        for col in columns:
            if not col.is_system_field and col.monday_type in type_mapping:
                unique_types.add(type_mapping[col.monday_type])
        
        logger.debug(f"Found {len(unique_types)} unique column types: {unique_types}")
        return unique_types
    
    def _generate_script_name(self, board_name: str) -> str:
        """
        Generate a sanitized script filename from board name
        
        Args:
            board_name: Original board name
            
        Returns:
            Sanitized script name
        """
        import re
        # Convert to lowercase, replace spaces and special chars with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', board_name.lower())
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores
        sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
        return f"get_board_{sanitized}"
    
    def save_script(
        self, 
        script_content: str, 
        filename: str = None, 
        output_dir: str = None
    ) -> str:
        """
        Save generated script to file
        
        Args:
            script_content: Generated Python script content
            filename: Output filename (optional, will be generated)
            output_dir: Output directory (optional, defaults to generated/)
            
        Returns:
            Path to saved script file
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "generated"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            filename = "generated_script.py"
        
        if not filename.endswith('.py'):
            filename += '.py'
        
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"Saved generated script to {filepath}")
        return str(filepath)
    
    def generate_workflow_config(
        self, 
        board_schema: BoardSchema, 
        workflow_config: Dict[str, Any] = None
    ) -> str:
        """
        Generate Kestra workflow YAML configuration
        
        Args:
            board_schema: BoardSchema object
            workflow_config: Optional workflow configuration
            
        Returns:
            Generated workflow YAML content
        """
        logger.info(f"Generating workflow config for board '{board_schema.board_name}'")
        
        # Default workflow configuration
        default_config = {
            "schedule": "0 */6 * * *",  # Every 6 hours
            "timeout": "PT30M",  # 30 minutes
            "retry_attempts": 3,
            "namespace": "monday-boards"
        }
        
        # Merge with provided config
        config = {**default_config, **(workflow_config or {})}
        
        # Prepare template variables for workflow
        workflow_vars = {
            "board_id": board_schema.board_id,
            "board_name": board_schema.board_name,
            "table_name": board_schema.table_name,
            "database": board_schema.database,
            "script_name": self._generate_script_name(board_schema.board_name),
            "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **config
        }
        
        try:
            # Check if workflow template exists
            workflow_template_path = self.template_dir / "workflow_template.yml.j2"
            if workflow_template_path.exists():
                template = self.env.get_template("workflow_template.yml.j2")
                workflow_content = template.render(**workflow_vars)
            else:
                # Generate basic workflow if template doesn't exist
                workflow_content = self._generate_basic_workflow(workflow_vars)
            
            logger.info(f"Successfully generated workflow config")
            return workflow_content
            
        except Exception as e:
            raise ScriptTemplateGeneratorError(f"Failed to generate workflow config: {e}")
    
    def _generate_basic_workflow(self, vars: Dict[str, Any]) -> str:
        """Generate a basic workflow YAML if template doesn't exist"""
        return f"""# Generated Kestra Workflow for Monday.com Board: {vars['board_name']}
# Generated: {vars['generation_timestamp']}

id: {vars['script_name']}
namespace: {vars['namespace']}

description: |
  ETL workflow for Monday.com board '{vars['board_name']}' (ID: {vars['board_id']})
  Target table: {vars['database']}.dbo.{vars['table_name']}

triggers:
  - id: schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "{vars['schedule']}"

tasks:
  - id: extract_board_data
    type: io.kestra.core.tasks.scripts.Python
    description: "Extract data from Monday.com board {vars['board_id']}"
    timeout: "{vars['timeout']}"
    retry:
      type: "constant"
      interval: "PT5M"
      maxAttempt: {vars['retry_attempts']}
    script: |
      import subprocess
      import sys
      
      # Execute the generated extraction script
      result = subprocess.run([
          sys.executable, 
          "scripts/monday-boards/generated/{vars['script_name']}.py"
      ], capture_output=True, text=True, cwd="/app")
      
      if result.returncode != 0:
          print(f"Script failed with return code {{result.returncode}}")
          print(f"STDERR: {{result.stderr}}")
          raise Exception(f"Extraction script failed: {{result.stderr}}")
      
      print(f"STDOUT: {{result.stdout}}")
      print("✅ Board extraction completed successfully")

labels:
  board_id: "{vars['board_id']}"
  board_name: "{vars['board_name']}"
  table_name: "{vars['table_name']}"
  database: "{vars['database']}"
  generated_by: "Dynamic Monday.com Board Template System"
"""
    
    def validate_script(self, script_content: str) -> bool:
        """
        Validate generated script for basic syntax errors
        
        Args:
            script_content: Generated Python script content
            
        Returns:
            True if script is valid
        """
        try:
            import ast
            ast.parse(script_content)
            logger.info("Script validation passed")
            return True
        except SyntaxError as e:
            logger.error(f"Script syntax validation failed: {e}")
            raise ScriptTemplateGeneratorError(f"Generated script has syntax errors: {e}")


# Convenience functions
def generate_script_from_schema(
    board_schema: BoardSchema, 
    output_dir: str = None,
    script_config: Dict[str, Any] = None
) -> str:
    """
    Convenience function to generate and save script from schema
    
    Args:
        board_schema: BoardSchema object
        output_dir: Output directory for script
        script_config: Script configuration overrides
        
    Returns:
        Path to generated script file
    """
    generator = ScriptTemplateGenerator()
    script_content = generator.generate_extraction_script(board_schema, script_config)
    
    # Generate filename from board name
    script_name = generator._generate_script_name(board_schema.board_name)
    filename = f"{script_name}.py"
    
    return generator.save_script(script_content, filename, output_dir)


if __name__ == "__main__":
    # Test with existing board metadata
    import json
    
    metadata_file = Path(__file__).parent.parent / "metadata" / "boards" / "board_8709134353_metadata.json"
    
    if metadata_file.exists():
        logger.info("Testing Script Template Generator")
        
        # Load board metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Convert back to BoardSchema object
        from datetime import datetime
        
        # Convert columns back to ColumnDefinition objects
        columns = []
        for col_data in metadata['columns']:
            col = ColumnDefinition(**col_data)
            columns.append(col)
        
        # Create BoardSchema object
        board_schema = BoardSchema(
            board_id=metadata['board_id'],
            board_name=metadata['board_name'],
            table_name=metadata['table_name'],
            database=metadata['database'],
            discovered_at=datetime.fromisoformat(metadata['discovered_at']),
            columns=columns,
            metadata=metadata['metadata']
        )
        
        # Generate script
        script_path = generate_script_from_schema(board_schema)
        print(f"\n✅ Generated script: {script_path}")        
        # Generate workflow
        generator = ScriptTemplateGenerator()
        workflow_content = generator.generate_workflow_config(board_schema)
        
        workflow_path = Path(__file__).parent.parent / "generated" / f"workflow_{board_schema.board_name.lower()}.yml"
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(workflow_content)
        
        print(f"✅ Generated workflow: {workflow_path}")
        
    else:
        logger.error(f"Metadata file not found: {metadata_file}")
        print("Please run board_schema_generator.py first to generate metadata.")
