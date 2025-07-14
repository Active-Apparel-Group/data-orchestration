"""
Master Data Mapping Helper

This module provides programmatic access to the centralized data mapping registry.
All developers and AI agents should use this module to access mapping information
instead of hardcoding field names, types, or board configurations.

Usage Examples:
    import mapping_helper as mapping
    
    # Get board configuration
    board_config = mapping.get_board_config('coo_planning')
    
    # Get field type mappings
    sql_type = mapping.get_sql_type('text')  # Returns 'NVARCHAR(MAX)'
    
    # Get standardized field info
    field_info = mapping.get_standardized_field('mo_number')
    
    # Generate DDL for a table
    ddl = mapping.generate_create_table_ddl('MON_NewBoard', board_mapping)
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Constants
DEFAULT_CONFIG_PATH = Path(__file__).parent / "data_mapping.yaml"
MAPPING_CACHE = {}
CACHE_TIMESTAMP = None


class MappingError(Exception):
    """Raised when mapping operations fail"""
    pass


class MappingValidationError(Exception):
    """Raised when mapping validation fails"""
    pass


def _load_mapping_config(config_path: str = None) -> Dict:
    """
    Load the master mapping configuration from YAML file.
    Uses caching to avoid repeated file reads.
    
    Args:
        config_path: Optional path to mapping config file
        
    Returns:
        Dict containing the complete mapping configuration
    """
    global MAPPING_CACHE, CACHE_TIMESTAMP
    
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    # Check if file has been modified since last load
    try:
        file_mtime = os.path.getmtime(config_path)
        if CACHE_TIMESTAMP and file_mtime <= CACHE_TIMESTAMP and MAPPING_CACHE:
            return MAPPING_CACHE
    except OSError:
        raise MappingError(f"Cannot access mapping config file: {config_path}")
    
    # Load the mapping configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Update cache
        MAPPING_CACHE = config
        CACHE_TIMESTAMP = file_mtime
        
        return config
        
    except yaml.YAMLError as e:
        raise MappingError(f"Invalid YAML in mapping config: {e}")
    except FileNotFoundError:
        raise MappingError(f"Mapping config file not found: {config_path}")


def load_orders_mapping_config() -> Dict:
    """
    Load the orders mapping configuration from the comprehensive mapping YAML.
    
    Returns:
        Dict containing field mappings, Monday.com column IDs, and transformation rules
    """
    # Load the orders mapping from the specific file
    orders_mapping_path = Path(__file__).parent.parent / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
    
    try:
        with open(orders_mapping_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
        
    except yaml.YAMLError as e:
        raise MappingError(f"Invalid YAML in orders mapping config: {e}")
    except FileNotFoundError:
        raise MappingError(f"Orders mapping config file not found: {orders_mapping_path}")


def get_mapping_metadata() -> Dict:
    """
    Get metadata about the mapping system.
    
    Returns:
        Dict with version, creation date, and other metadata
    """
    config = _load_mapping_config()
    return config.get('metadata', {})


def list_monday_boards() -> List[str]:
    """
    Get a list of all configured Monday.com boards.
    
    Returns:
        List of board names (keys)
    """
    config = _load_mapping_config()
    return list(config.get('monday_boards', {}).keys())


def get_board_config(board_name: str) -> Dict:
    """
    Get complete configuration for a Monday.com board.
    
    Args:
        board_name: Name of the board (e.g., 'coo_planning')
        
    Returns:
        Dict with board configuration including columns, table info, etc.
        
    Raises:
        MappingError: If board not found
    """
    config = _load_mapping_config()
    boards = config.get('monday_boards', {})
    
    if board_name not in boards:
        available = list(boards.keys())
        raise MappingError(f"Board '{board_name}' not found. Available: {available}")
    
    return boards[board_name]


def get_board_table_info(board_name: str) -> Dict:
    """
    Get database table information for a Monday.com board.
    
    Args:
        board_name: Name of the board
        
    Returns:
        Dict with table_name, database, description, etc.
    """
    board_config = get_board_config(board_name)
    return {
        'table_name': board_config.get('table_name'),
        'database': board_config.get('database'),
        'description': board_config.get('description'),
        'status': board_config.get('status'),
        'staging_table': board_config.get('staging_table'),
        'error_table': board_config.get('error_table')
    }


def get_board_columns(board_name: str) -> List[Dict]:
    """
    Get column mappings for a Monday.com board.
    
    Args:
        board_name: Name of the board
        
    Returns:
        List of column configuration dicts
    """
    board_config = get_board_config(board_name)
    return board_config.get('columns', [])


def get_sql_type(monday_type: str) -> str:
    """
    Get SQL Server type for a Monday.com field type.
    
    Args:
        monday_type: Monday.com field type (e.g., 'text', 'date', 'numbers')
        
    Returns:
        SQL Server type (e.g., 'NVARCHAR(MAX)', 'DATE', 'BIGINT')
        
    Raises:
        MappingError: If type mapping not found
    """
    config = _load_mapping_config()
    type_mappings = config.get('field_types', {}).get('monday_to_sql', {})
    
    if monday_type not in type_mappings:
        available = list(type_mappings.keys())
        raise MappingError(f"Monday type '{monday_type}' not mapped. Available: {available}")
    
    return type_mappings[monday_type]


def get_monday_type(sql_type: str) -> str:
    """
    Get Monday.com type for a SQL Server field type.
    
    Args:
        sql_type: SQL Server type (e.g., 'NVARCHAR(MAX)', 'DATE')
        
    Returns:
        Monday.com type (e.g., 'text', 'date')
    """
    config = _load_mapping_config()
    type_mappings = config.get('field_types', {}).get('sql_to_monday', {})
    
    if sql_type not in type_mappings:
        available = list(type_mappings.keys())
        raise MappingError(f"SQL type '{sql_type}' not mapped. Available: {available}")
    
    return type_mappings[sql_type]


def get_conversion_function(field_type: str, direction: str = 'monday_to_sql') -> str:
    """
    Get the conversion function for a field type.
    
    Args:
        field_type: Type of field (e.g., 'date', 'numbers', 'text')
        direction: Conversion direction ('monday_to_sql' or 'sql_to_monday')
        
    Returns:
        Function name for conversion
    """
    config = _load_mapping_config()
    conversions = config.get('field_types', {}).get('conversion_functions', {})
    
    if field_type not in conversions:
        raise MappingError(f"No conversion functions for field type: {field_type}")
    
    if direction not in conversions[field_type]:
        available = list(conversions[field_type].keys())
        raise MappingError(f"Direction '{direction}' not available for {field_type}. Available: {available}")
    
    return conversions[field_type][direction]


def get_standardized_field(field_name: str, category: str = None) -> Dict:
    """
    Get information about a standardized field.
    
    Args:
        field_name: Name of the standardized field
        category: Optional category to search within
        
    Returns:
        Dict with field information including aliases, type, etc.
    """
    config = _load_mapping_config()
    std_fields = config.get('standardized_fields', {})
    
    # If category specified, search within that category
    if category:
        if category not in std_fields:
            available = list(std_fields.keys())
            raise MappingError(f"Category '{category}' not found. Available: {available}")
        
        category_fields = std_fields[category]
        if field_name not in category_fields:
            available = list(category_fields.keys())
            raise MappingError(f"Field '{field_name}' not found in category '{category}'. Available: {available}")
        
        return category_fields[field_name]
    
    # Search across all categories
    for cat_name, cat_fields in std_fields.items():
        if field_name in cat_fields:
            return cat_fields[field_name]
    
    raise MappingError(f"Standardized field '{field_name}' not found")


def get_customer_mapping(customer_name: str) -> Dict:
    """
    Get customer name mapping information.
    
    Args:
        customer_name: Customer name to look up
        
    Returns:
        Dict with canonical name, aliases, and system mappings
    """
    config = _load_mapping_config()
    customers = config.get('customer_mappings', {}).get('normalized_customers', {})
    
    # Direct lookup by canonical name
    if customer_name in customers:
        return customers[customer_name]
    
    # Search by aliases
    for canonical_name, customer_info in customers.items():
        aliases = customer_info.get('aliases', [])
        if customer_name in aliases:
            return customer_info
    
    raise MappingError(f"Customer '{customer_name}' not found in mappings")


def get_database_schema(schema_name: str) -> Dict:
    """
    Get database schema information.
    
    Args:
        schema_name: Name of the schema (e.g., 'orders_unified')
        
    Returns:
        Dict with schema configuration
    """
    config = _load_mapping_config()
    schemas = config.get('database_schemas', {})
    
    if schema_name not in schemas:
        available = list(schemas.keys())
        raise MappingError(f"Schema '{schema_name}' not found. Available: {available}")
    
    return schemas[schema_name]


def generate_create_table_ddl(table_name: str, columns: List[Dict], database: str = None) -> str:
    """
    Generate CREATE TABLE DDL statement from column mappings.
    
    Args:
        table_name: Name of the table to create
        columns: List of column configuration dicts
        database: Optional database name for context
        
    Returns:
        SQL CREATE TABLE statement
    """
    if not columns:
        raise MappingValidationError("No columns provided for DDL generation")
    
    # Start DDL statement
    ddl_lines = [
        f"-- Table: {table_name}",
        f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Source: Master Data Mapping System",
        ""
    ]
    
    if database:
        ddl_lines.extend([
            f"-- Database: {database}",
            ""
        ])
    
    ddl_lines.append(f"CREATE TABLE [dbo].[{table_name}] (")
    
    # Generate column definitions
    col_definitions = []
    for col in columns:
        sql_column = col.get('sql_column')
        sql_type = col.get('sql_type')
        required = col.get('required', False)
        description = col.get('description', '')
        
        if not sql_column or not sql_type:
            continue
        
        null_spec = "NOT NULL" if required else "NULL"
        col_def = f"    [{sql_column}] {sql_type} {null_spec}"
        
        if description:
            col_def += f"  -- {description}"
        
        col_definitions.append(col_def)
    
    ddl_lines.append(",\n".join(col_definitions))
    ddl_lines.append(");")
    
    return "\n".join(ddl_lines)


def validate_board_mapping(board_config: Dict) -> List[str]:
    """
    Validate a board mapping configuration.
    
    Args:
        board_config: Board configuration dict to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['board_id', 'board_name', 'table_name', 'database', 'description']
    for field in required_fields:
        if field not in board_config:
            errors.append(f"Missing required field: {field}")
    
    # Validate board_id is numeric
    board_id = board_config.get('board_id')
    if board_id and not isinstance(board_id, (int, str)) or (isinstance(board_id, str) and not board_id.isdigit()):
        errors.append(f"board_id must be numeric: {board_id}")
    
    # Validate table name follows convention
    table_name = board_config.get('table_name', '')
    if table_name and not table_name.startswith('MON_'):
        errors.append(f"table_name should start with 'MON_': {table_name}")
    
    # Validate columns if present
    columns = board_config.get('columns', [])
    for i, col in enumerate(columns):
        if 'name' not in col:
            errors.append(f"Column {i}: Missing 'name' field")
        if 'sql_column' not in col:
            errors.append(f"Column {i}: Missing 'sql_column' field")
        if 'sql_type' not in col:
            errors.append(f"Column {i}: Missing 'sql_type' field")
    
    return errors


def get_field_aliases(field_name: str) -> List[str]:
    """
    Get all known aliases for a field name.
    
    Args:
        field_name: Name of the field to find aliases for
        
    Returns:
        List of aliases (including the original name)
    """
    config = _load_mapping_config()
    aliases = [field_name]  # Include the original name
    
    # Search in standardized fields
    std_fields = config.get('standardized_fields', {})
    for category in std_fields.values():
        for field_config in category.values():
            field_aliases = field_config.get('aliases', [])
            if field_name in field_aliases or field_name == field_config.get('name'):
                aliases.extend(field_aliases)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(aliases))


def search_mappings(search_term: str, search_type: str = 'all') -> Dict:
    """
    Search for mappings containing a term.
    
    Args:
        search_term: Term to search for
        search_type: Type of search ('boards', 'fields', 'customers', 'all')
        
    Returns:
        Dict with search results organized by type
    """
    config = _load_mapping_config()
    results = {'boards': [], 'fields': [], 'customers': [], 'tables': []}
    
    search_term_lower = search_term.lower()
    
    # Search boards
    if search_type in ['boards', 'all']:
        for board_name, board_config in config.get('monday_boards', {}).items():
            if (search_term_lower in board_name.lower() or 
                search_term_lower in board_config.get('description', '').lower() or
                search_term_lower in board_config.get('table_name', '').lower()):
                results['boards'].append({
                    'name': board_name,
                    'table': board_config.get('table_name'),
                    'description': board_config.get('description')
                })
    
    # Search fields  
    if search_type in ['fields', 'all']:
        std_fields = config.get('standardized_fields', {})
        for category, fields in std_fields.items():
            for field_name, field_config in fields.items():
                if (search_term_lower in field_name.lower() or
                    search_term_lower in field_config.get('description', '').lower() or
                    any(search_term_lower in alias.lower() for alias in field_config.get('aliases', []))):
                    results['fields'].append({
                        'name': field_name,
                        'category': category,
                        'description': field_config.get('description'),
                        'aliases': field_config.get('aliases', [])
                    })
    
    # Search customers
    if search_type in ['customers', 'all']:
        customers = config.get('customer_mappings', {}).get('normalized_customers', {})
        for customer_id, customer_config in customers.items():
            canonical = customer_config.get('canonical', '')
            aliases = customer_config.get('aliases', [])
            if (search_term_lower in canonical.lower() or
                any(search_term_lower in alias.lower() for alias in aliases)):
                results['customers'].append({
                    'id': customer_id,
                    'canonical': canonical,
                    'aliases': aliases,
                    'status': customer_config.get('status')
                })
    
    return results


def get_orders_field_mappings() -> Dict:
    """
    Get the field mappings for orders with real Monday.com column IDs.
    
    Returns:
        Dict with source field -> Monday.com column ID mappings
    """
    config = load_orders_mapping_config()
    
    # Handle new expanded mapping structure
    column_mappings = {}
    
    # Exact matches (list format in expanded mapping)
    exact_matches = config.get('exact_matches', [])
    if isinstance(exact_matches, list):
        for mapping in exact_matches:
            source = mapping.get('source_field')
            target_column_id = mapping.get('target_column_id')
            if source and target_column_id:
                column_mappings[source] = target_column_id
    
    # Mapped fields (list format in expanded mapping)
    mapped_fields = config.get('mapped_fields', [])
    if isinstance(mapped_fields, list):
        for mapping in mapped_fields:
            source = mapping.get('source_field')
            target_column_id = mapping.get('target_column_id')
            if source and target_column_id:
                column_mappings[source] = target_column_id
    
    # Computed fields (list format in expanded mapping)
    computed_fields = config.get('computed_fields', [])
    if isinstance(computed_fields, list):
        for mapping in computed_fields:
            source = mapping.get('source_field')
            target_column_id = mapping.get('target_column_id')
            if source and target_column_id:
                column_mappings[source] = target_column_id
    
    # Legacy support for old structure
    field_mappings = config.get('field_mappings', {})
    if field_mappings:
        # Exact matches (old structure)
        exact_matches_old = field_mappings.get('exact_matches', {})
        for field_name, field_config in exact_matches_old.items():
            source = field_config.get('source')
            target_column_id = field_config.get('target_column_id')
            if source and target_column_id:
                column_mappings[source] = target_column_id
        
        # Other field types (old structure)
        for field_type in ['numeric_fields', 'date_fields', 'text_fields']:
            fields = field_mappings.get(field_type, {})
            for field_name, field_config in fields.items():
                source = field_config.get('source')
                target_column_id = field_config.get('target_column_id')
                if source and target_column_id:
                    column_mappings[source] = target_column_id
    
    return column_mappings


def get_orders_subitem_mappings() -> Dict:
    """
    Get the subitem field mappings for orders with real Monday.com column IDs.
    
    Returns:
        Dict with subitem field -> Monday.com column ID mappings
    """
    config = load_orders_mapping_config()
    
    # Handle new expanded mapping structure
    subitem_mappings = {}
    
    # Subitem mappings (list format in expanded mapping)
    subitem_fields = config.get('subitem_mappings', [])
    if isinstance(subitem_fields, list):
        for mapping in subitem_fields:
            source = mapping.get('source_field')
            target_column_id = mapping.get('target_column_id')
            if source and target_column_id:
                subitem_mappings[source] = target_column_id
    
    # Legacy support for old structure
    field_mappings = config.get('field_mappings', {})
    if field_mappings:
        subitem_fields_old = field_mappings.get('subitem_fields', {})
        for field_name, field_config in subitem_fields_old.items():
            target_column_id = field_config.get('target_column_id')
            if target_column_id:
                subitem_mappings[field_name] = target_column_id
    
    return subitem_mappings


# Convenience functions for common operations
def get_coo_planning_config() -> Dict:
    """Get COO Planning board configuration"""
    return get_board_config('coo_planning')


def get_customer_master_schedule_config() -> Dict:
    """Get Customer Master Schedule board configuration"""
    return get_board_config('customer_master_schedule')


def get_orders_unified_schema() -> Dict:
    """Get ORDERS_UNIFIED table schema"""
    return get_database_schema('orders_unified')


# Export commonly used functions for easy importing
__all__ = [
    'get_board_config',
    'get_board_table_info', 
    'get_board_columns',
    'get_sql_type',
    'get_monday_type',
    'get_conversion_function',
    'get_standardized_field',
    'get_customer_mapping',
    'get_database_schema',
    'generate_create_table_ddl',
    'validate_board_mapping',
    'list_monday_boards',
    'search_mappings',
    'get_mapping_stats',
    'load_orders_mapping_config',
    'get_orders_field_mappings',
    'get_orders_subitem_mappings',
    'MappingError',
    'MappingValidationError'
]
