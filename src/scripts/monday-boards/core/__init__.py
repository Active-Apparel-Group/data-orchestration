"""
Dynamic Monday.com Board Template System - Core Components

This package contains the core functionality for dynamically creating
database schemas and extraction scripts for any Monday.com board.

Components:
    - board_schema_generator: Discovers board structure and generates SQL DDL
    - script_template_generator: Generates Python extraction scripts from templates
    - board_registry: Manages board configurations and deployment tracking
    - monday_board_cli: Command-line interface for board management
"""

__version__ = "1.0.0"
__author__ = "Data Orchestration Team"

# Core components
from .board_schema_generator import BoardSchemaGenerator
from .script_template_generator import ScriptTemplateGenerator
from .board_registry import BoardRegistry

__all__ = [
    "BoardSchemaGenerator",
    "ScriptTemplateGenerator", 
    "BoardRegistry"
]
