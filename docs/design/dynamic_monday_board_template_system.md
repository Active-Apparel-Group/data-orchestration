# Dynamic Monday.com Board Template System Design

## Overview

This design document outlines a comprehensive plan to transform the current static Monday.com board extraction script into a dynamic, template-driven system that can automatically create database schemas and extraction scripts for any Monday.com board.

## Current State Analysis

### Existing Implementation
- **Script**: `scripts/monday-boards/get_board_planning.py`
- **Target**: Single board (ID: 8709134353) → `MON_COO_Planning` table
- **Hardcoded Elements**:
  - Board ID and table name
  - Column mappings and data type conversions
  - Database schema expectations
  - Field-specific processing logic

### Architecture Components
- **Configuration**: Centralized YAML config (`utils/config.yaml`)
- **Database Helper**: Reusable connection/query utilities (`utils/db_helper.py`)
- **DDL Storage**: SQL schema files in `sql/ddl/tables/orders/`
- **Orchestration**: Kestra workflows in `workflows/`

## Proposed Dynamic System Architecture

### System Components

#### 1. Board Discovery & Schema Generator (`board_schema_generator.py`)
**Purpose**: Discover Monday.com board structure and generate database schema

**Key Functions**:
- **Board Introspection**: Query Monday.com API to get all columns and their types
- **Schema Mapping**: Map Monday.com field types to SQL Server data types
- **DDL Generation**: Create appropriate CREATE TABLE statements
- **Metadata Storage**: Store board metadata as JSON for reference

**Input Parameters**:
```python
def generate_board_schema(board_id: int, board_name: str, table_name: str, database: str = "orders"):
    """
    Generate schema for a Monday.com board
    
    Args:
        board_id: Monday.com board identifier
        board_name: Human-readable board name
        table_name: Target database table name (e.g., MON_xxx)
        database: Target database connection name
    """
```

#### 2. Script Template Generator (`script_template_generator.py`)
**Purpose**: Generate customized Python extraction scripts based on board schema

**Key Functions**:
- **Template Rendering**: Use Jinja2 to create board-specific scripts
- **Type Conversion Logic**: Generate appropriate data type handling
- **Cursor Implementation**: Implement pagination for large boards
- **Async Processing**: Generate concurrent insert logic

#### 3. Board Registry & Configuration Manager (`board_registry.py`)
**Purpose**: Manage board configurations and deployment tracking

**Key Functions**:
- **Board Registration**: Track configured boards and their metadata
- **Configuration Validation**: Ensure board configs are valid
- **Deployment Tracking**: Monitor which boards are deployed and operational

#### 4. CLI Interface (`monday_board_cli.py`)
**Purpose**: Provide command-line interface for board management

**Commands**:
```bash
# Deploy a new board
python monday_board_cli.py deploy --board-id 12345 --board-name "customer-orders" --table-name "MON_CustomerOrders"

# Update existing board schema
python monday_board_cli.py update --board-id 12345

# List all configured boards
python monday_board_cli.py list

# Remove board configuration
python monday_board_cli.py remove --board-id 12345
```

### Data Flow Process

#### Phase 1: Board Discovery & Schema Generation
1. **API Introspection**: Query Monday.com GraphQL API to get board columns
2. **Type Mapping**: Map Monday.com field types to SQL Server types
3. **Schema Generation**: Create DDL statements based on discovered schema
4. **Metadata Storage**: Save board metadata as JSON for future reference

#### Phase 2: Database Deployment
1. **DDL Execution**: Create table in target database
2. **Validation**: Verify table creation and structure
3. **Registration**: Add board to registry with deployment status

#### Phase 3: Script Generation
1. **Template Processing**: Generate Python script using board-specific metadata
2. **Code Generation**: Create extraction script with proper type conversions
3. **Testing**: Validate generated script with sample data
4. **Deployment**: Place script in appropriate directory structure

#### Phase 4: Orchestration Integration
1. **Workflow Generation**: Create Kestra workflow for the new board
2. **Scheduling**: Configure extraction frequency and dependencies
3. **Monitoring**: Set up logging and error handling

## Detailed Component Design

### 1. Monday.com Field Type Mapping

```python
MONDAY_TO_SQL_MAPPING = {
    # Core Types
    "text": "NVARCHAR(MAX)",
    "long_text": "NVARCHAR(MAX)", 
    "numbers": "BIGINT",
    "rating": "INT",
    "status": "NVARCHAR(100)",
    "dropdown": "NVARCHAR(100)",
    
    # Date/Time Types
    "date": "DATE",
    "datetime": "DATETIME2",
    "timeline": "NVARCHAR(MAX)",  # JSON timeline data
    
    # Relationship Types
    "people": "NVARCHAR(MAX)",    # Comma-separated names
    "dependency": "NVARCHAR(MAX)", # JSON dependency data
    "link": "NVARCHAR(500)",
    "email": "NVARCHAR(255)",
    "phone": "NVARCHAR(50)",
    
    # Advanced Types
    "file": "NVARCHAR(MAX)",      # JSON file metadata
    "board_relation": "NVARCHAR(MAX)", # JSON board relation data
    "mirror": "NVARCHAR(MAX)",    # Mirror column values
    "formula": "NVARCHAR(MAX)",   # Formula results
    "checkbox": "BIT",
    "tags": "NVARCHAR(MAX)",      # Comma-separated tags
    
    # Special Fields (Always Present)
    "item_id": "BIGINT",
    "item_name": "NVARCHAR(500)",
    "group_title": "NVARCHAR(200)",
    "updated_at": "DATETIME2",
    "created_at": "DATETIME2"
}
```

### 2. Script Template Structure

```python
# Template variables for Jinja2 rendering
TEMPLATE_VARS = {
    "board_id": "{{ board_id }}",
    "board_name": "{{ board_name }}",
    "table_name": "{{ table_name }}",
    "database": "{{ database }}",
    "columns": "{{ columns }}",  # List of column definitions
    "type_conversions": "{{ type_conversions }}",  # Type-specific conversion logic
    "api_query": "{{ api_query }}",  # GraphQL query for board
    "batch_size": "{{ batch_size }}",
    "max_workers": "{{ max_workers }}"
}
```

### 3. Board Metadata Schema

```python
BOARD_METADATA_SCHEMA = {
    "board_id": int,
    "board_name": str,
    "table_name": str,
    "database": str,
    "created_at": datetime,
    "last_updated": datetime,
    "schema_version": str,
    "columns": [
        {
            "monday_id": str,
            "monday_title": str,
            "monday_type": str,
            "sql_column": str,
            "sql_type": str,
            "nullable": bool,
            "conversion_logic": str
        }
    ],
    "deployment_status": {
        "ddl_deployed": bool,
        "script_generated": bool,
        "workflow_created": bool,
        "last_successful_run": datetime
    }
}
```

### 4. Directory Structure

```
scripts/
├── monday-boards/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── board_schema_generator.py
│   │   ├── script_template_generator.py
│   │   ├── board_registry.py
│   │   └── monday_board_cli.py
│   ├── templates/
│   │   ├── board_extractor_template.py.j2
│   │   └── workflow_template.yml.j2
│   ├── metadata/
│   │   ├── board_registry.json
│   │   └── boards/
│   │       ├── board_12345_metadata.json
│   │       └── board_67890_metadata.json
│   ├── generated/
│   │   ├── get_board_customer_orders.py
│   │   ├── get_board_planning.py
│   │   └── get_board_inventory.py
│   └── legacy/
│       └── get_board_planning.py  # Original script for reference
```

### 5. Error Handling & Validation

```python
class BoardDeploymentError(Exception):
    """Raised when board deployment fails"""
    pass

class SchemaValidationError(Exception):
    """Raised when board schema validation fails"""
    pass

class TemplateGenerationError(Exception):
    """Raised when script template generation fails"""
    pass

# Validation checks
VALIDATION_CHECKS = {
    "board_exists": "Verify board ID exists in Monday.com",
    "api_access": "Verify API token has board access permissions",
    "table_name_valid": "Ensure table name follows SQL naming conventions",
    "database_connection": "Verify target database connection",
    "schema_compatibility": "Check for schema breaking changes",
    "dependency_check": "Verify all required dependencies are available"
}
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
1. **Board Schema Generator**
   - Implement Monday.com API introspection
   - Create field type mapping logic
   - Generate DDL creation functionality
   - Add metadata serialization

2. **Template System**
   - Create Jinja2 template for extraction scripts
   - Implement template variable substitution
   - Add validation for generated code

3. **Board Registry**
   - Design metadata storage format
   - Implement CRUD operations for board configs
   - Add validation and error handling

### Phase 2: CLI Interface & Integration (Week 3-4)
1. **Command Line Interface**
   - Implement deployment commands
   - Add board management operations
   - Create interactive configuration wizard

2. **Database Integration**
   - Integrate with existing `db_helper.py`
   - Add DDL execution and validation
   - Implement rollback capabilities

3. **Script Generation**
   - Generate production-ready extraction scripts
   - Implement async processing patterns
   - Add comprehensive error handling

### Phase 3: Orchestration & Monitoring (Week 5-6)
1. **Workflow Generation**
   - Create Kestra workflow templates
   - Implement scheduling configuration
   - Add dependency management

2. **Monitoring & Alerting**
   - Add deployment status tracking
   - Implement health checks
   - Create notification system

3. **Documentation & Testing**
   - Create comprehensive documentation
   - Implement unit and integration tests
   - Add performance benchmarking

## Usage Examples

### 1. Deploy New Board
```bash
# Interactive deployment
python monday_board_cli.py deploy --interactive

# Command-line deployment
python monday_board_cli.py deploy \
  --board-id 12345 \
  --board-name "customer-orders" \
  --table-name "MON_CustomerOrders" \
  --database "orders" \
  --batch-size 100 \
  --max-workers 8
```

### 2. Update Existing Board
```bash
# Check for schema changes
python monday_board_cli.py check --board-id 12345

# Update schema and regenerate script
python monday_board_cli.py update --board-id 12345 --force
```

### 3. Manage Board Registry
```bash
# List all boards
python monday_board_cli.py list

# Show board details
python monday_board_cli.py show --board-id 12345

# Remove board configuration
python monday_board_cli.py remove --board-id 12345 --confirm
```

## Benefits & Advantages

### 1. **Scalability**
- Support unlimited Monday.com boards without code changes
- Automatic schema discovery eliminates manual mapping
- Template-driven approach ensures consistency

### 2. **Maintainability**
- Centralized type mapping and conversion logic
- Generated code follows established patterns
- Easy to update templates for improvements

### 3. **Operational Excellence**
- Automated deployment process reduces errors
- Comprehensive validation and error handling
- Built-in monitoring and health checks

### 4. **Developer Productivity**
- New boards can be deployed in minutes
- No need to write extraction scripts manually
- Consistent patterns across all board extractors

## Risk Mitigation

### 1. **API Changes**
- Version Monday.com API usage
- Implement backward compatibility checks
- Add schema change detection and alerts

### 2. **Data Quality**
- Validate data types during extraction
- Implement data quality checks
- Add anomaly detection for schema changes

### 3. **Performance**
- Monitor extraction performance metrics
- Implement adaptive batch sizing
- Add circuit breakers for failing boards

### 4. **Security**
- Secure API token management
- Implement proper access controls
- Add audit logging for all operations

## Future Enhancements

### 1. **Advanced Features**
- **Schema Evolution**: Automatic handling of board schema changes
- **Data Lineage**: Track data flow from Monday.com to analytics systems
- **Real-time Sync**: WebSocket-based real-time updates
- **Multi-tenant Support**: Support for multiple Monday.com accounts

### 2. **Integration Opportunities**
- **CI/CD Integration**: Deploy boards through GitHub Actions
- **Monitoring Integration**: Integrate with existing monitoring systems
- **Data Quality Framework**: Add comprehensive data quality checks
- **Analytics Integration**: Direct integration with BI tools

### 3. **Performance Optimizations**
- **Incremental Sync**: Only sync changed data
- **Compression**: Compress large payloads for transfer
- **Caching**: Cache board schemas for faster deployments
- **Parallel Processing**: Process multiple boards simultaneously

## Conclusion

This dynamic template system will transform Monday.com board integration from a manual, time-intensive process to an automated, scalable solution. The template-driven approach ensures consistency while providing flexibility for board-specific requirements. The comprehensive CLI interface makes the system accessible to both technical and non-technical users, while the robust error handling and validation ensure reliable operations in production environments.

The phased implementation approach allows for incremental value delivery while minimizing risk. The system is designed to integrate seamlessly with existing infrastructure while providing a foundation for future enhancements and integrations.
