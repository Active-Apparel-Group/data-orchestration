# Dynamic Monday.com Board Template System - Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to transform the current static Monday.com board extraction script into a dynamic, template-driven system. The solution will automatically create database schemas and extraction scripts for any Monday.com board, eliminating manual coding and enabling rapid deployment of new board integrations.

## Current State Analysis

### Existing Script: `get_board_planning.py`
- **Single Board Focus**: Hardcoded for Board ID 8709134353 → `MON_COO_Planning` table
- **Manual Type Mapping**: Hardcoded field type conversions and column processing
- **Static Schema**: Fixed database table structure
- **Production Ready**: Well-optimized with async processing, pagination, and error handling

### Architecture Strengths to Preserve
- ✅ **Robust Error Handling**: Comprehensive exception handling and recovery
- ✅ **Performance Optimized**: Concurrent processing with configurable batch sizes
- ✅ **Pagination Support**: Cursor-based pagination for large datasets
- ✅ **Type Safety**: Careful data type conversion and validation
- ✅ **Database Integration**: Seamless integration with existing `db_helper.py`
- ✅ **Configuration Management**: Centralized config via `utils/config.yaml`

## Proposed Dynamic System

### Core Components

#### 1. **Board Discovery Engine** (`board_schema_generator.py`)
```python
class BoardSchemaGenerator:
    def discover_board_structure(self, board_id: int) -> BoardSchema:
        """Query Monday.com API to discover all columns and types"""
        
    def generate_sql_schema(self, board_schema: BoardSchema) -> str:
        """Generate CREATE TABLE DDL from board structure"""
        
    def save_board_metadata(self, board_id: int, metadata: dict) -> None:
        """Store board metadata as JSON for future reference"""
```

#### 2. **Script Template Engine** (`script_template_generator.py`)
```python
class ScriptTemplateGenerator:
    def generate_extraction_script(self, board_metadata: dict) -> str:
        """Generate board-specific Python extraction script"""
        
    def create_workflow_config(self, board_metadata: dict) -> str:
        """Generate Kestra workflow YAML"""
```

#### 3. **Board Registry** (`board_registry.py`)
```python
class BoardRegistry:
    def register_board(self, board_config: BoardConfig) -> None:
        """Register new board in system"""
        
    def get_board_config(self, board_id: int) -> BoardConfig:
        """Retrieve board configuration"""
        
    def list_all_boards(self) -> List[BoardConfig]:
        """List all registered boards"""
```

#### 4. **CLI Interface** (`monday_board_cli.py`)
```bash
# Deploy new board
python monday_board_cli.py deploy --board-id 12345 --board-name "customer-orders" --table-name "MON_CustomerOrders"

# Update existing board
python monday_board_cli.py update --board-id 12345

# List all boards
python monday_board_cli.py list

# Test board connection
python monday_board_cli.py test --board-id 12345
```

### Field Type Mapping Strategy

```python
MONDAY_TO_SQL_MAPPING = {
    # Text Types
    "text": "NVARCHAR(MAX)",
    "long_text": "NVARCHAR(MAX)",
    "email": "NVARCHAR(255)",
    "phone": "NVARCHAR(50)",
    "link": "NVARCHAR(500)",
    
    # Numeric Types
    "numbers": "BIGINT",
    "rating": "INT",
    
    # Date/Time Types
    "date": "DATE",
    "datetime": "DATETIME2",
    "timeline": "NVARCHAR(MAX)",  # JSON format
    
    # Choice Types
    "status": "NVARCHAR(100)",
    "dropdown": "NVARCHAR(100)",
    "checkbox": "BIT",
    
    # Relationship Types
    "people": "NVARCHAR(MAX)",     # Comma-separated
    "dependency": "NVARCHAR(MAX)", # JSON format
    "board_relation": "NVARCHAR(MAX)", # JSON format
    "mirror": "NVARCHAR(MAX)",     # Mirror values
    "formula": "NVARCHAR(MAX)",    # Calculated values
    
    # File Types
    "file": "NVARCHAR(MAX)",       # JSON metadata
    "tags": "NVARCHAR(MAX)",       # Comma-separated
    
    # System Fields (Always Present)
    "_item_id": "BIGINT NOT NULL",
    "_item_name": "NVARCHAR(500)",
    "_group_title": "NVARCHAR(200)",
    "_updated_at": "DATETIME2",
    "_created_at": "DATETIME2"
}
```

### Template Structure

#### Generated Script Template (`board_extractor_template.py.j2`)
```python
#!/usr/bin/env python3
"""
GENERATED ETL Script: Monday.com Board {{ board_name }} to SQL Server
Board ID: {{ board_id }}
Table: {{ table_name }}
Database: {{ database }}
Generated: {{ generation_timestamp }}
"""

import os, requests, pandas as pd, pyodbc, asyncio, concurrent.futures
from datetime import datetime
import time, sys
from pathlib import Path

# Repository root discovery (preserved from original)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    # ... (same as original)

# Configuration
BOARD_ID = {{ board_id }}
TABLE_NAME = "{{ table_name }}"
DATABASE = "{{ database }}"

# API configuration (preserved from original)
MONDAY_TOKEN = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
# ... (same as original)

def fetch_board_data_with_pagination():
    """Fetch ALL items from Monday.com board using cursor-based pagination"""
    # Custom GraphQL query for this board
    query = '''
    query GetBoardItems {
      boards(ids: {{ board_id }}) {
        name
        items_page(limit: 250${cursor_arg}) {
          cursor
          items {
            id
            name
            updated_at
            group {
              id
              title
            }
            column_values {
              column {
                title
                id
                type
              }
              value
              text
              {% for column_type in unique_column_types %}
              ... on {{ column_type }}Value { display_value }
              {% endfor %}
            }
          }
        }
      }
    }
    '''
    # ... (pagination logic preserved from original)

def extract_value(column_value):
    """Extract the correct value from Monday.com column based on type"""
    cv = column_value
    column_type = cv["column"]["type"]
    
    # Generated type-specific extraction logic
    {% for column in columns %}
    {% if column.requires_special_handling %}
    if column_type == "{{ column.monday_type }}" and cv["column"]["title"] == "{{ column.title }}":
        {{ column.conversion_logic | indent(8) }}
    {% endif %}
    {% endfor %}
    
    # Default extraction logic (preserved from original)
    # ... (same as original)

def process_items(items):
    """Convert Monday.com items to DataFrame"""
    records = []
    for item in items:
        record = {
            {% for column in columns %}
            "{{ column.sql_column }}": None,  # Will be populated from column_values
            {% endfor %}
        }
        
        # Standard fields
        record["_item_id"] = item["id"]
        record["_item_name"] = item["name"]
        record["_updated_at"] = item["updated_at"]
        record["_group_title"] = item["group"]["title"]
        
        # Extract column values
        for cv in item["column_values"]:
            column_title = cv["column"]["title"]
            {% for column in columns %}
            if column_title == "{{ column.monday_title }}":
                record["{{ column.sql_column }}"] = extract_value(cv)
            {% endfor %}
        
        records.append(record)
    
    return pd.DataFrame(records)

def prepare_for_database(df):
    """Prepare DataFrame for database insert with robust conversions"""
    # Generated type conversion logic
    {% for column in columns %}
    {% if column.sql_type == "DATE" %}
    # Date column: {{ column.sql_column }}
    if "{{ column.sql_column }}" in df.columns:
        df["{{ column.sql_column }}"] = df["{{ column.sql_column }}"].apply(safe_date_convert)
    {% elif column.sql_type == "BIGINT" or column.sql_type == "INT" %}
    # Numeric column: {{ column.sql_column }}
    if "{{ column.sql_column }}" in df.columns:
        df["{{ column.sql_column }}"] = df["{{ column.sql_column }}"].apply(safe_numeric_convert)
    {% endif %}
    {% endfor %}
    
    return df

# ... (rest of the script preserved from original with template substitutions)

if __name__ == "__main__":
    asyncio.run(main())
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Deliverables:**
- [ ] `board_schema_generator.py` - Core discovery engine
- [ ] `script_template_generator.py` - Template rendering engine  
- [ ] `board_registry.py` - Board configuration management
- [ ] Field type mapping logic with comprehensive Monday.com type support
- [ ] Jinja2 template for script generation

**Success Criteria:**
- Can discover any Monday.com board structure via API
- Can generate valid SQL DDL for discovered schema
- Can render functional Python extraction script from template
- All generated DDL executes successfully against target database

### Phase 2: CLI & Integration (Week 3-4)
**Deliverables:**
- [ ] `monday_board_cli.py` - Complete command-line interface
- [ ] Integration with existing `db_helper.py` for DDL execution
- [ ] Board metadata storage and retrieval system
- [ ] Validation and error handling for all operations
- [ ] Unit tests for core components

**Success Criteria:**
- Can deploy new board end-to-end via CLI command
- Generated scripts successfully extract data from Monday.com
- All database operations complete without errors
- Comprehensive error messages guide user through issues

### Phase 3: Operations & Monitoring (Week 5-6)
**Deliverables:**
- [ ] Kestra workflow template generation
- [ ] Board health monitoring and status checks
- [ ] Schema change detection and alerting
- [ ] Performance optimization and benchmarking
- [ ] Comprehensive documentation and examples

**Success Criteria:**
- Generated workflows execute successfully in Kestra
- Monitoring detects and alerts on schema changes
- Performance meets or exceeds current script benchmarks
- Documentation enables easy onboarding of new users

## Directory Structure

```
scripts/monday-boards/
├── core/                          # Core system components
│   ├── __init__.py
│   ├── board_schema_generator.py  # Schema discovery and DDL generation
│   ├── script_template_generator.py # Python script generation
│   ├── board_registry.py          # Board configuration management
│   └── monday_board_cli.py        # Command-line interface
├── templates/                     # Jinja2 templates
│   ├── board_extractor_template.py.j2  # Python script template
│   └── workflow_template.yml.j2   # Kestra workflow template
├── metadata/                      # Board configurations and metadata
│   ├── board_registry.json        # Master board registry
│   └── boards/                    # Individual board metadata
│       ├── board_8709134353_metadata.json
│       └── board_12345_metadata.json
├── generated/                     # Generated extraction scripts
│   ├── get_board_coo_planning.py  # Generated from existing board
│   ├── get_board_customer_orders.py
│   └── get_board_inventory.py
└── legacy/                        # Original scripts for reference
    └── get_board_planning.py       # Original static script
```

## Usage Examples

### Deploy New Board
```bash
# Interactive deployment with prompts
python monday_board_cli.py deploy --interactive

# Direct deployment with all parameters
python monday_board_cli.py deploy \
    --board-id 12345 \
    --board-name "customer-orders" \
    --table-name "MON_CustomerOrders" \
    --database "orders" \
    --batch-size 100 \
    --max-workers 8
```

### Manage Existing Boards
```bash
# List all configured boards
python monday_board_cli.py list

# Show detailed board information
python monday_board_cli.py show --board-id 12345

# Check for schema changes
python monday_board_cli.py check --board-id 12345

# Update board configuration
python monday_board_cli.py update --board-id 12345 --force

# Test board connectivity
python monday_board_cli.py test --board-id 12345

# Remove board configuration
python monday_board_cli.py remove --board-id 12345 --confirm
```

## Risk Mitigation

### Technical Risks
1. **Monday.com API Changes**
   - Mitigation: Version API calls, implement backward compatibility
   - Monitoring: Schema change detection and alerting

2. **Generated Code Quality**
   - Mitigation: Comprehensive template testing and validation
   - Monitoring: Automated testing of generated scripts

3. **Performance Degradation**
   - Mitigation: Preserve proven optimization patterns from original script
   - Monitoring: Performance benchmarking and alerting

### Operational Risks
1. **User Error in Board Configuration**
   - Mitigation: Extensive validation and interactive prompts
   - Recovery: Easy rollback and re-deployment capabilities

2. **Database Schema Conflicts**
   - Mitigation: Schema validation before DDL execution
   - Recovery: Automated cleanup and rollback procedures

## Success Metrics

### Development Metrics
- [ ] **Coverage**: 100% of Monday.com field types supported
- [ ] **Performance**: Generated scripts match or exceed original performance
- [ ] **Reliability**: 99.9% successful deployment rate for valid board configs
- [ ] **Quality**: Zero critical bugs in generated code

### Operational Metrics
- [ ] **Deployment Time**: New board deployment in <5 minutes
- [ ] **User Adoption**: 100% of new Monday.com integrations use template system
- [ ] **Maintenance Reduction**: 90% reduction in manual script development
- [ ] **Error Rate**: <1% failure rate for template-generated extractions

## Conclusion

This dynamic template system represents a significant advancement in our Monday.com integration capabilities. By automating schema discovery, DDL generation, and script creation, we eliminate manual coding effort while ensuring consistency and reliability across all board integrations.

The system preserves all the performance optimizations and robust error handling of the current production script while adding the flexibility to handle any Monday.com board structure. The comprehensive CLI interface makes the system accessible to both technical and business users, enabling rapid deployment of new integrations without developer intervention.

The phased implementation approach ensures incremental value delivery while minimizing risk to existing production systems. Upon completion, this system will serve as a foundation for future enhancements and integration opportunities across the entire data platform.
