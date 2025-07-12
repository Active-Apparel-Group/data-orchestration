# Universal Monday.com Board Extraction System

## Overview

The Universal Monday.com Board Extraction System provides a unified approach to discovering, configuring, and extracting data from Monday.com boards into SQL Server tables. The system consists of two main components:

1. **Board Discovery & Configuration**: `universal_board_extractor.py`
2. **ETL Pipeline Execution**: `load_boards.py`

## Quick Start

### 1. Discover and Configure a New Board

```bash
# Discover board schema and generate metadata configuration
python pipelines/codegen/universal_board_extractor.py --board-id 8685586257

# This creates:
# - configs/boards/board_8685586257_metadata.json (metadata file)
# - workflows/extract_board_8685586257.yaml (Kestra workflow)
# - Updates configs/registry.json (central board registry)
```

### 2. Run ETL Pipeline

```bash
# Execute complete ETL pipeline (fetch data → process → load to SQL)
python pipelines/scripts/load_boards.py --board-id 8685586257

# Alternative operations:
python pipelines/scripts/load_boards.py --board-id 8685586257 --generate-config-only  # Config only
python pipelines/scripts/load_boards.py --board-id 8685586257 --update-registry      # Update registry
```

## Directory Structure

```
configs/
├── registry.json                                    # Central board registry
└── boards/
    └── board_8685586257_metadata.json              # Board-specific metadata

pipelines/
├── codegen/
│   └── universal_board_extractor.py                # Board discovery & config generation
├── scripts/
│   └── load_boards.py                              # ETL pipeline execution
└── utils/                                          # Utility modules (copied from root utils/)

workflows/
└── extract_board_8685586257.yaml                   # Auto-generated Kestra workflow
```

## Column Control System

### Overview

The column control system provides granular control over which columns to include/exclude and how to process them during ETL operations. Each column in the metadata has four control fields:

### Control Fields

#### 1. `exclude` (Boolean)
- **Purpose**: Include or exclude column from ETL pipeline
- **Default**: `false` (include column)
- **Example**:
```json
{
  "id": "status",
  "title": "Status",
  "type": "color",
  "exclude": true,        // Exclude this column from ETL
  "custom_sql_type": null,
  "custom_extraction_field": null
}
```

#### 2. `custom_sql_type` (String or null)
- **Purpose**: Override the default SQL Server data type
- **Default**: `null` (use automatic type mapping)
- **Example**:
```json
{
  "id": "creation_log",
  "title": "Creation Log",
  "type": "creation_log",
  "exclude": false,
  "custom_sql_type": "VARCHAR(500)",  // Override default NVARCHAR(MAX)
  "custom_extraction_field": null
}
```

#### 3. `custom_extraction_field` (String or null)
- **Purpose**: Override the GraphQL field used for data extraction
- **Default**: `null` (use automatic field mapping)
- **Example**:
```json
{
  "id": "name",
  "title": "Name",
  "type": "name",
  "exclude": false,
  "custom_sql_type": null,
  "custom_extraction_field": "name"  // Use 'name' instead of default 'text'
}
```

### Type Mapping Priority System

The system uses a three-tier priority system for determining SQL data types:

1. **Custom Overrides** (Highest Priority)
   - Per-column `custom_sql_type` in metadata
   - Allows complete type customization

2. **Type Defaults** (Medium Priority)  
   - Default mappings for Monday.com column types
   - Defined in `global_defaults.type_defaults`

3. **Global Defaults** (Lowest Priority)
   - Fallback mapping when type is unknown
   - Default: `NVARCHAR(MAX)`

### Global Defaults Configuration

The metadata includes a `global_defaults` section with standardized mappings:

```json
{
  "global_defaults": {
    "sql_type": "NVARCHAR(MAX)",
    "extraction_field": "text",
    "type_defaults": {
      "text": "NVARCHAR(255)",
      "long_text": "NVARCHAR(MAX)",
      "numbers": "DECIMAL(18,2)",
      "status": "NVARCHAR(50)",
      "dropdown": "NVARCHAR(100)",
      "people": "NVARCHAR(255)",
      "date": "DATE",
      "color": "NVARCHAR(50)",
      "checkbox": "BIT",
      "name": "NVARCHAR(255)",
      "creation_log": "NVARCHAR(MAX)",
      "last_updated": "DATETIME2"
    }
  }
}
```

## Practical Examples

### Example 1: Exclude Columns

To exclude specific columns from ETL processing:

```json
{
  "id": "status",
  "title": "Status", 
  "type": "color",
  "exclude": true,        // This column will be skipped
  "custom_sql_type": null,
  "custom_extraction_field": null
}
```

### Example 2: Custom SQL Types

To use custom SQL data types:

```json
{
  "id": "priority",
  "title": "Priority",
  "type": "numbers", 
  "exclude": false,
  "custom_sql_type": "INT",  // Override default DECIMAL(18,2)
  "custom_extraction_field": null
}
```

### Example 3: Custom Extraction Fields

To use different GraphQL fields for data extraction:

```json
{
  "id": "assignee",
  "title": "Assignee",
  "type": "people",
  "exclude": false,
  "custom_sql_type": null,
  "custom_extraction_field": "persons_and_teams.name"  // Custom GraphQL path
}
```

## Metadata File Structure

### Complete Example

```json
{
  "board_id": "8685586257",
  "board_name": "Factory List", 
  "table_name": "MON_FactoryList",
  "database": "orders",
  "discovery_version": "2.0",
  "timestamp": "2025-06-29T00:27:11.123456",
  "item_terminology": "items",
  
  "global_defaults": {
    "sql_type": "NVARCHAR(MAX)",
    "extraction_field": "text", 
    "type_defaults": {
      "text": "NVARCHAR(255)",
      "numbers": "DECIMAL(18,2)",
      "status": "NVARCHAR(50)"
    }
  },
  
  "columns": [
    {
      "id": "name",
      "title": "Name",
      "type": "name",
      "exclude": false,
      "custom_sql_type": null,
      "custom_extraction_field": null
    },
    {
      "id": "status",
      "title": "Status",
      "type": "color", 
      "exclude": true,             // Excluded from ETL
      "custom_sql_type": null,
      "custom_extraction_field": null
    },
    {
      "id": "priority",
      "title": "Priority", 
      "type": "numbers",
      "exclude": false,
      "custom_sql_type": "INT",    // Custom SQL type
      "custom_extraction_field": null
    }
  ]
}
```

## ETL Pipeline Process

### 1. Schema Loading
- Loads metadata from `configs/boards/board_{board_id}_metadata.json`
- Applies column control rules (exclude, custom types, custom fields)
- Builds column mapping for SQL table creation

### 2. Data Extraction
- Fetches all board items via Monday.com GraphQL API
- Uses configured extraction fields for each column
- Handles pagination automatically

### 3. Data Processing  
- Builds pandas DataFrame with fetched data
- Applies data cleaning and validation
- Makes column names SQL-safe

### 4. Database Loading
- Creates staging table with appropriate SQL types
- Loads data to staging table in optimized batches  
- Performs atomic swap to production table
- Updates registry with execution metadata

## Registry System

### Central Board Registry

The `configs/registry.json` file tracks all configured boards:

```json
{
  "boards": {
    "8685586257": {
      "board_name": "Factory List",
      "table_name": "MON_FactoryList", 
      "database": "orders",
      "last_run": "2025-06-29T18:33:40.295000",
      "status": "active",
      "metadata_path": "configs/boards/board_8685586257_metadata.json",
      "workflow_path": "workflows/extract_board_8685586257.yaml"
    }
  },
  "metadata": {
    "version": "1.0",
    "created_at": "2025-06-29T00:00:00Z",
    "updated_at": "2025-06-29T18:33:40.295000"
  }
}
```

### Registry Benefits
- **Centralized tracking** of all board configurations
- **Path management** for metadata and workflow files  
- **Execution history** with timestamps and status
- **Discovery support** for finding existing configurations

## Command Line Interface

### Universal Board Extractor

```bash
# Basic board discovery
python pipelines/codegen/universal_board_extractor.py --board-id BOARD_ID

# Options:
--board-id          Monday.com board ID (required)
--database          Target database name (default: orders)
--force-overwrite   Overwrite existing configurations
```

### ETL Pipeline Loader

```bash
# Run complete ETL pipeline
python pipelines/scripts/load_boards.py --board-id BOARD_ID

# Options:
--board-id              Monday.com board ID (required)
--generate-config-only  Generate configuration only, skip ETL
--update-registry       Update registry after manual config changes
```

## Error Handling

### Common Issues

1. **Board Not Found**: Verify board ID and Monday.com access permissions
2. **Column Type Mapping**: Check `global_defaults.type_defaults` for unknown types
3. **SQL Server Connection**: Validate database credentials in `utils/config.yaml`
4. **Metadata Missing**: Run board discovery first with `universal_board_extractor.py`

### Debugging

- **Enable detailed logging**: Logs show each ETL phase with performance metrics
- **Check staging tables**: Failed ETL operations leave staging tables for inspection
- **Validate metadata**: Ensure JSON syntax is correct after manual edits
- **Test column rules**: Use `--generate-config-only` to validate configurations

## Best Practices

### 1. Column Configuration
- **Start with discovery**: Always run `universal_board_extractor.py` first
- **Review and customize**: Edit metadata file to exclude unnecessary columns
- **Test incremental**: Use `--generate-config-only` to validate changes
- **Document customizations**: Add comments explaining custom overrides

### 2. Performance Optimization
- **Exclude unused columns**: Set `exclude: true` for columns not needed in SQL
- **Optimize SQL types**: Use appropriate data types (INT vs DECIMAL, VARCHAR vs NVARCHAR)
- **Monitor batch sizes**: ETL auto-optimizes but monitor for large boards
- **Schedule wisely**: Run ETL during off-peak hours for large datasets

### 3. Production Deployment
- **Version control**: Store metadata files in git repository
- **Environment separation**: Use different databases for dev/staging/prod
- **Backup strategy**: Atomic swaps preserve data but maintain backup procedures
- **Monitoring**: Set up alerts for ETL failures using registry status field

## Integration Examples

### Kestra Workflow Integration

The system auto-generates Kestra workflows for each board:

```yaml
id: extract_board_8685586257
namespace: monday_etl
description: "Extract data from Monday.com board: Factory List (8685586257)"

tasks:
  - id: extract_data
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import subprocess
      result = subprocess.run([
        "python", 
        "pipelines/scripts/load_boards.py", 
        "--board-id", "8685586257"
      ], capture_output=True, text=True)
      
      if result.returncode != 0:
        raise Exception(f"ETL failed: {result.stderr}")
      
      print("SUCCESS: Board extraction completed")
      print(result.stdout)
```

### PowerBI Integration

After ETL completion, data is available in SQL Server for PowerBI:

```sql
-- Query the extracted board data
SELECT 
    name,
    status,
    priority,
    creation_log,
    last_updated
FROM orders.MON_FactoryList
WHERE status = 'Active'
ORDER BY priority DESC;
```

## Support

For additional help:
- **Review logs**: ETL operations provide detailed logging for troubleshooting
- **Check registry**: `configs/registry.json` tracks all board configurations and status
- **Validate metadata**: Use JSON validators for syntax checking
- **Test incrementally**: Use CLI flags to test configuration changes before full ETL
