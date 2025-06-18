# Master Data Mapping System - Developer Guide

## Overview

The Master Data Mapping System provides a centralized registry for all data transformations, field mappings, and schema definitions across the entire data orchestration platform. This system eliminates hardcoded values and ensures consistency across all scripts, queries, and DDL files.

## Core Philosophy

> **"Never hardcode field names, types, or mappings again. One import gives you access to all data mappings in the system, with built-in validation and type safety."**

## Quick Start

### For Developers

```python
# Import the mapping helper
import mapping_helper as mapping

# Get board configuration
board_config = mapping.get_board_config('coo_planning')
BOARD_ID = board_config['board_id']
TABLE_NAME = board_config['table_name']

# Get field type mappings
sql_type = mapping.get_sql_type('text')  # Returns 'NVARCHAR(MAX)'
conversion_func = mapping.get_conversion_function('date', 'monday_to_sql')

# Generate DDL
columns = mapping.get_board_columns('coo_planning')
ddl = mapping.generate_create_table_ddl('MON_NewBoard', columns)
```

### For AI Agents

```python
# Load all mapping context
mapping_stats = mapping.get_mapping_stats()
available_boards = mapping.list_monday_boards()

# Search for relevant mappings
results = mapping.search_mappings('customer', 'fields')

# Get standardized field definitions
field_info = mapping.get_standardized_field('mo_number', 'manufacturing')
```

## File Structure

```
utils/
├── data_mapping.yaml              # Master mapping registry (THE SINGLE SOURCE OF TRUTH)
├── mapping_helper.py              # Programmatic access utilities
└── mapping_migration_helper.py    # Migration and compatibility tools

docs/mapping/                      # Original files (PRESERVED - do not delete)
├── *.yaml                        # All existing mapping files (untouched)
└── backup/                       # Backup directory for migrations
```

## Core Components

### 1. Master Mapping Registry (`utils/data_mapping.yaml`)

**THE SINGLE SOURCE OF TRUTH** - Contains all operational mappings:

- **Monday.com Board Configurations**: Board IDs, table names, column mappings
- **Database Schemas**: Table structures, field definitions, relationships  
- **Field Type Mappings**: Monday.com ↔ SQL Server type conversions
- **Standardized Fields**: Canonical field names with aliases and types
- **Customer Mappings**: Normalized customer names across systems
- **Mapping Patterns**: Reusable templates and common patterns

### 2. Mapping Helper (`utils/mapping_helper.py`)

**PRIMARY INTERFACE** - Provides programmatic access to all mappings:

```python
# Board Operations
get_board_config(board_name)          # Get complete board configuration
get_board_table_info(board_name)      # Get table/database info
get_board_columns(board_name)         # Get column mappings
list_monday_boards()                  # List all configured boards

# Type Operations  
get_sql_type(monday_type)             # Monday → SQL type mapping
get_monday_type(sql_type)             # SQL → Monday type mapping
get_conversion_function(type, direction)  # Get conversion function name

# Field Operations
get_standardized_field(field_name)    # Get canonical field definition
get_field_aliases(field_name)         # Get all known aliases
search_mappings(term, type)           # Search across all mappings

# Schema Operations
get_database_schema(schema_name)      # Get database schema info
generate_create_table_ddl(table, cols) # Generate DDL from mappings

# Validation
validate_board_mapping(config)        # Validate board configuration
get_mapping_stats()                   # Get system statistics
```

### 3. Migration Helper (`utils/mapping_migration_helper.py`)

**TRANSITION TOOL** - Helps migrate from legacy files (future use):

```python
# Analysis
analyze_existing_mappings()           # Analyze legacy files
validate_migration_readiness()        # Check migration readiness

# Migration Support  
create_compatibility_layer(legacy_file)  # Create compatibility mapping
generate_migration_script(script, board) # Generate migration suggestions
compare_mappings(legacy_file, board)     # Compare legacy vs new
backup_legacy_files()                    # Backup before migration
```

## Usage Patterns

### Pattern 1: New Script Development

```python
#!/usr/bin/env python3
"""
New Monday.com extraction script using mapping system
"""
import mapping_helper as mapping

# Get board configuration from mapping system
board_config = mapping.get_board_config('customer_orders')

# Extract configuration values
BOARD_ID = board_config['board_id']
TABLE_NAME = board_config['table_name']
DATABASE = board_config['database']

# Get column mappings
columns = mapping.get_board_columns('customer_orders')

def build_graphql_query():
    """Build GraphQL query using column mappings"""
    column_names = [col['name'] for col in columns]
    # ... build query using actual column names from mappings
    
def process_column_value(column_value):
    """Process column value using type mappings"""
    column_type = column_value['column']['type']
    
    # Get conversion function from mappings
    conversion_func = mapping.get_conversion_function(column_type, 'monday_to_sql')
    
    # Apply appropriate conversion
    if conversion_func == 'safe_date_convert':
        return safe_date_convert(column_value['value'])
    # ... other conversions
```

### Pattern 2: DDL Generation

```python
import mapping_helper as mapping

def create_new_board_table(board_name: str):
    """Create database table for a new Monday.com board"""
    
    # Get board configuration
    board_config = mapping.get_board_config(board_name)
    columns = mapping.get_board_columns(board_name)
    
    # Generate DDL
    ddl = mapping.generate_create_table_ddl(
        board_config['table_name'],
        columns,
        board_config['database']
    )
    
    # Execute DDL
    db.execute(ddl, board_config['database'])
    
    print(f"✅ Created table {board_config['table_name']} for board {board_name}")
```

### Pattern 3: Field Standardization

```python
import mapping_helper as mapping

def standardize_customer_name(raw_customer_name: str) -> str:
    """Standardize customer name using mapping system"""
    try:
        customer_mapping = mapping.get_customer_mapping(raw_customer_name)
        return customer_mapping['canonical']
    except mapping.MappingError:
        # Customer not found in mappings - needs to be added
        print(f"⚠️ Customer '{raw_customer_name}' not found in mappings")
        return raw_customer_name.upper().strip()

def get_standard_field_name(field_alias: str) -> str:
    """Get standardized field name from alias"""
    try:
        field_info = mapping.get_standardized_field(field_alias)
        return field_info['name']
    except mapping.MappingError:
        # Try searching for the field
        results = mapping.search_mappings(field_alias, 'fields')
        if results['fields']:
            return results['fields'][0]['name']
        return field_alias  # Fallback to original
```

### Pattern 4: Schema Discovery

```python
import mapping_helper as mapping

def discover_available_data():
    """Discover all available data mappings"""
    
    # Get system overview
    stats = mapping.get_mapping_stats()
    print(f"📊 Mapping System Stats:")
    print(f"   Boards: {stats['boards_count']}")
    print(f"   Database Schemas: {stats['database_schemas_count']}")
    print(f"   Field Types: {stats['field_type_mappings_count']}")
    
    # List available boards
    boards = mapping.list_monday_boards()
    print(f"📋 Available Monday.com Boards:")
    for board in boards:
        config = mapping.get_board_config(board)
        print(f"   {board}: {config['table_name']} ({config['status']})")
    
    # Search for specific fields
    customer_fields = mapping.search_mappings('customer', 'fields')
    print(f"👤 Customer-related Fields: {len(customer_fields['fields'])}")
```

## Maintenance Guidelines

### For Developers

#### When Creating New Scripts:
1. **ALWAYS** check the mapping system first:
   ```python
   available_boards = mapping.list_monday_boards()
   ```

2. **NEVER** hardcode board IDs, table names, or field types:
   ```python
   # ❌ DON'T DO THIS
   BOARD_ID = 8709134353
   TABLE_NAME = "MON_COO_Planning"
   
   # ✅ DO THIS INSTEAD
   board_config = mapping.get_board_config('coo_planning')
   BOARD_ID = board_config['board_id']
   TABLE_NAME = board_config['table_name']
   ```

3. **ALWAYS** use standardized field names:
   ```python
   # ❌ DON'T DO THIS
   if 'MO Number' in row or 'MO_NUMBER' in row:
   
   # ✅ DO THIS INSTEAD
   field_info = mapping.get_standardized_field('mo_number')
   standard_name = field_info['name']
   aliases = field_info['aliases']
   ```

#### When Adding New Boards:
1. **Update the master mapping file** (`utils/data_mapping.yaml`)
2. **Add complete board configuration** with all required fields
3. **Test the configuration** using `mapping.validate_board_mapping()`
4. **Update any related patterns** or templates

#### When Discovering New Field Types:
1. **Add to field_types section** in the master mapping file
2. **Define both monday_to_sql and sql_to_monday mappings**
3. **Add conversion functions** if special handling needed
4. **Update existing boards** that use the new type

### For AI Agents

#### Before Any Code Generation:
1. **Load the complete mapping context**:
   ```python
   import mapping_helper as mapping
   stats = mapping.get_mapping_stats()
   boards = mapping.list_monday_boards()
   ```

2. **Search for relevant existing mappings**:
   ```python
   # Search for related fields/boards
   search_results = mapping.search_mappings(user_query_term, 'all')
   ```

3. **Use standardized field names and types**:
   ```python
   # Get canonical field definitions
   field_info = mapping.get_standardized_field(field_name)
   sql_type = mapping.get_sql_type(monday_type)
   ```

#### When Generating New Code:
1. **ALWAYS** use mapping system instead of hardcoded values
2. **Reference existing patterns** from mapping_patterns section
3. **Validate generated mappings** before suggesting to user
4. **Update mapping file** if new patterns discovered

#### When Analyzing Existing Code:
1. **Extract hardcoded mappings** and suggest migration to mapping system
2. **Identify inconsistencies** in field names/types across scripts
3. **Recommend standardization** using existing mapping patterns

## Error Handling

### Common Errors and Solutions

```python
try:
    board_config = mapping.get_board_config('unknown_board')
except mapping.MappingError as e:
    # Board not found - check available boards
    available = mapping.list_monday_boards()
    print(f"Available boards: {available}")

try:
    sql_type = mapping.get_sql_type('unknown_type')
except mapping.MappingError as e:
    # Type not mapped - add to mapping file or use default
    sql_type = 'NVARCHAR(MAX)'  # Safe default for unknown text types

try:
    field_info = mapping.get_standardized_field('unknown_field')
except mapping.MappingError as e:
    # Field not standardized - use search to find similar
    search_results = mapping.search_mappings('unknown_field', 'fields')
    if search_results['fields']:
        suggested = search_results['fields'][0]
        print(f"Did you mean: {suggested['name']}?")
```

### Validation Patterns

```python
# Validate board configuration before use
errors = mapping.validate_board_mapping(board_config)
if errors:
    for error in errors:
        print(f"❌ Validation Error: {error}")
    raise ValueError("Invalid board configuration")

# Check mapping system health
readiness = mapping_migration_helper.validate_migration_readiness()
if not readiness['ready']:
    for issue in readiness['issues']:
        print(f"🚨 System Issue: {issue}")
```

## Integration Examples

### With Existing db_helper.py

```python
import mapping_helper as mapping
import db_helper as db

def create_board_table_with_mappings(board_name: str):
    """Create table using both mapping and db systems"""
    
    # Get configuration from mapping system
    board_config = mapping.get_board_config(board_name)
    columns = mapping.get_board_columns(board_name)
    
    # Generate DDL using mapping system
    ddl = mapping.generate_create_table_ddl(
        board_config['table_name'], 
        columns,
        board_config['database']
    )
    
    # Execute using existing db_helper
    db.execute(ddl, board_config['database'])
    
    # Verify table creation
    verify_sql = f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{board_config['table_name']}'"
    result = db.run_query(verify_sql, board_config['database'])
    
    if result.iloc[0, 0] > 0:
        print(f"✅ Table {board_config['table_name']} created successfully")
    else:
        raise Exception(f"❌ Table creation failed for {board_config['table_name']}")
```

### With Dynamic Board Template System

```python
import mapping_helper as mapping

def generate_dynamic_board_script(board_name: str) -> str:
    """Generate extraction script using mapping system"""
    
    # Get board configuration
    board_config = mapping.get_board_config(board_name)
    columns = mapping.get_board_columns(board_name)
    
    # Build template variables from mappings
    template_vars = {
        'board_id': board_config['board_id'],
        'board_name': board_config['board_name'],
        'table_name': board_config['table_name'],
        'database': board_config['database'],
        'columns': columns,
        'type_conversions': {}
    }
    
    # Generate type conversion logic
    for col in columns:
        monday_type = col.get('monday_type')
        if monday_type:
            conversion_func = mapping.get_conversion_function(monday_type, 'monday_to_sql')
            template_vars['type_conversions'][col['name']] = conversion_func
    
    # Use template engine to generate script
    # ... (integrate with Jinja2 template system)
    
    return generated_script
```

## Best Practices

### DO's ✅

1. **Always import mapping_helper** in new scripts
2. **Use mapping.get_board_config()** instead of hardcoded board info  
3. **Use mapping.get_sql_type()** for type conversions
4. **Use standardized field names** from the mapping system
5. **Validate mappings** before using in production
6. **Update mapping file** when adding new boards or fields
7. **Search existing mappings** before creating new ones
8. **Use mapping patterns** for common field groups

### DON'Ts ❌

1. **Never hardcode board IDs** or table names
2. **Never hardcode field type mappings** 
3. **Never create fields without checking standardized names**
4. **Never modify legacy files** in docs/mapping/ (they're preserved for compatibility)
5. **Never skip validation** of board configurations
6. **Never assume field names** are consistent across systems
7. **Never duplicate mapping logic** across scripts

### Performance Tips

1. **Cache mapping calls** in long-running scripts:
   ```python
   board_config = mapping.get_board_config('board_name')  # Cache this
   # Use board_config throughout script instead of repeated calls
   ```

2. **Load all needed mappings upfront**:
   ```python
   # At script start
   boards = {name: mapping.get_board_config(name) for name in needed_boards}
   type_mappings = {t: mapping.get_sql_type(t) for t in needed_types}
   ```

3. **Use search for discovery, direct access for known items**:
   ```python
   # For exploration
   results = mapping.search_mappings('customer')
   
   # For known access
   field_info = mapping.get_standardized_field('mo_number', 'manufacturing')
   ```

## Future Migration Path

When ready to migrate existing scripts (no timeline pressure):

1. **Phase 1**: Use mapping system for all new development
2. **Phase 2**: Add mapping calls alongside existing hardcoded values  
3. **Phase 3**: Replace hardcoded values with mapping calls
4. **Phase 4**: Remove hardcoded fallbacks
5. **Phase 5**: Archive legacy mapping files (far future)

The system is designed to work alongside existing code with zero disruption.

## Support and Troubleshooting

### Common Issues

**"Board not found"**: Check `mapping.list_monday_boards()` for available boards

**"Type not mapped"**: Add new type to `field_types.monday_to_sql` in master file

**"Field not standardized"**: Use `mapping.search_mappings()` to find similar fields

**"Validation failed"**: Check required fields using `mapping.validate_board_mapping()`

### Getting Help

1. **Check mapping stats**: `mapping.get_mapping_stats()`
2. **Search for similar**: `mapping.search_mappings(term, 'all')`  
3. **Validate configuration**: `mapping.validate_board_mapping(config)`
4. **Check system readiness**: `mapping_migration_helper.validate_migration_readiness()`

## Version History

- **v1.0** (2025-06-17): Initial implementation with complete mapping consolidation
- All existing mapping files preserved in docs/mapping/ (no disruption to current code)
- New system operational and ready for immediate use in new development
