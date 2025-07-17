# GitHub Copilot Custom Instructions for Data Orchestration Project

## Project Context
You are working on a data orchestration project that integrates Monday.com with SQL Server databases. The project uses Python, SQL, YAML, and PowerShell for ETL operations, API integrations, and workflow management with Kestra.

## Core Technologies
- **Database**: SQL Server, Azure SQL
- **APIs**: Monday.com GraphQL API
- **Languages**: Python 3.x, SQL, PowerShell, YAML
- **Orchestration**: Kestra workflows
- **IDE**: VS Code with extensive task automation

## Architecture Patterns to Follow

### File Organization
```
sql/                        # Database concerns (DDL, queries, mappings, GraphQL)
pipelines/      
    scripts/                # Executable Python scripts
    utils/                  # Shared utilities and helpers
    workflows/              # Kestra workflow definitions
tasks/                      # YAML task definitions
tests/                      # Test files organized by type
docs/                       # Documentation
```

### Coding Standards

#### Python
- Use `utils/db_helper.py` for all database connections
- Load configuration from `utils/config.yaml`
- Follow existing import patterns: `from utils.db_helper import get_connection`
- Place test files in `tests/debug/` not in project root
- Use type hints and docstrings for all functions

#### SQL
- Use consistent naming: snake_case for tables/columns
- Prefix staging tables with `stg_`
- Store DDL in `sql/ddl/tables/`
- Use parameterized queries for all dynamic SQL

#### Documentation (markdown)
- All filenames must be lowercase
- lowercase
- hyphenated for readability
- descriptive but concise
- examples
    - monday-board-loader.md
    - etl-pipeline-overview.md
    - setup-guide.md
    - api-reference.md

#### Monday.com Integration
- Store GraphQL operations in `sql/graphql/`
- Use simple field mappings from `sql/mappings/`
- Handle rate limiting (0.1 second delays)
- Always validate API responses

#### PowerShell
- Use `;` not `&&` for command chaining
- Current working directory is already set correctly
- Prefer PowerShell native commands over bash equivalents

## Project-Specific Rules

### Database Connections
```python
# ALWAYS use this pattern
from utils.db_helper import get_connection
# Use appropriate database from config.yaml (dms, dms_item, orders, infor_132)
with get_connection('database_name') as conn:
    # database operations
```

### Available Databases (from config.yaml)
- **dms**: Main data migration database (DMS)
- **dms_item**: Staging database for items (DMS_ITEM)  
- **orders**: Orders database (ORDERS)
- **infor_132**: Infor 13.2 production database (M3FDBPRD)

### Configuration Loading
```python
# ALWAYS load config this way
import yaml
from pathlib import Path

# Use robust path resolution for Kestra compatibility
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
config_path = repo_root / "utils" / "config.yaml"

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
```

### VS Code Tasks
- All tasks are defined in `.vscode/tasks.json`
- Use descriptive task names: "Pipeline: Order Sync V2"
- Group tasks: build, test, ops
- Reference existing tasks rather than creating new ones

### Error Handling
- Always use try/except for database operations
- Log errors using `utils/logger_helper.py`
- Provide meaningful error messages with context

## What NOT to Do

❌ Don't create files in project root - use proper subdirectories
❌ Don't use bash syntax (`&&`) in PowerShell
❌ Don't hardcode database connections - use `utils/config.yaml`
❌ Don't hardcode database names - use appropriate database from config (dms, dms_item, orders, infor_132)
❌ Don't create complex mapping files - keep mappings simple
❌ Don't modify `utils/config.yaml` - it contains live credentials
❌ Don't break existing import patterns
❌ Don't create new dependencies without checking existing utils

## Current Project State

### Simplified Mapping Approach
The project recently moved to simplified field mappings in `sql/mappings/simple-orders-mapping.yaml` to replace complex 798-line YAML files. Use the `SimpleOrdersMapper` class for all transformations.

### Immediate Priorities
1. Test GraphQL operations in `sql/graphql/`
2. Validate simplified mapping approach
3. Complete GREYSON PO 4755 integration testing
4. Maintain zero breaking changes philosophy

## Response Style
- Provide working code examples with proper imports
- Reference existing project files and patterns
- Suggest using existing VS Code tasks when relevant
- Focus on simple, maintainable solutions
- Always consider impact on existing workflows
