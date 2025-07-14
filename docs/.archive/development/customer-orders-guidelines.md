# Customer Orders Development Guidelines

## Development Patterns & Lessons Learned

### Schema Validation Patterns
- ✅ **PATTERN**: Always read DDL files to get exact column order and names
- ✅ **PATTERN**: Exclude internal tracking columns from database inserts
- ✅ **PATTERN**: Apply robust data type cleaning before any database operation
- ✅ **PATTERN**: Use UUID-based identification for all records

### Database Operation Patterns
- ✅ **PATTERN**: Always use `get_connection()` from `utils/db_helper.py`
- ✅ **PATTERN**: Use parameterized queries for all dynamic SQL
- ✅ **PATTERN**: Implement proper transaction handling with rollback capability
- ✅ **PATTERN**: Validate all database operations with test queries

### Import Standards (CRITICAL)
- ✅ **PATTERN**: Import utilities only from `utils/` folder
- ❌ **NEVER**: Import from `sql/`, `docs/`, or `queries/` folders
- ✅ **PATTERN**: Use standard import pattern with `sys.path.append()`
- ✅ **PATTERN**: All Python modules go in `utils/`, configs go in `sql/`

### File Organization Standards
```
utils/           # All Python modules (.py files with classes/functions)
sql/             # Database files (.sql, .graphql, .yaml configs) - NO Python code  
scripts/         # Executable Python scripts that import from utils/
tests/           # Test files and debug examples
docs/            # Documentation only - NO code files
workflows/       # Kestra workflow YAML definitions
```

### Error Handling Patterns
- ✅ **PATTERN**: Always use try/except for database operations
- ✅ **PATTERN**: Log errors using `utils/logger_helper.py`
- ✅ **PATTERN**: Provide meaningful error messages with context
- ✅ **PATTERN**: Implement graceful degradation for non-critical failures

### Group Logic Placement
- ✅ **FIXED**: Implemented group name logic in staging processor, not API adapter
- ✅ **PATTERN**: Customer CUSTOMER_SEASON → CUSTOMER AAG_SEASON → CUSTOMER [fallback]
- ✅ **PATTERN**: Business logic belongs in staging, API layer just consumes data

### Test Validation Accuracy
- ✅ **PATTERN**: All validation queries use exact table and column names from DDL
- ✅ **PATTERN**: Never use made-up or mismatched table/column names in queries
- ✅ **PATTERN**: Test scripts should validate the actual data being inserted
- ✅ **PATTERN**: Use proper function signatures for database operations

### Monday.com Integration Patterns
- ✅ **PATTERN**: Use simple field mappings from `sql/mappings/`
- ✅ **PATTERN**: Handle rate limiting (0.1 second delays)
- ✅ **PATTERN**: Always validate API responses
- ✅ **PATTERN**: Store GraphQL operations in `sql/graphql/`

### Code Standards
- ✅ **PATTERN**: Use type hints and docstrings for all functions
- ✅ **PATTERN**: Follow consistent naming: snake_case for tables/columns
- ✅ **PATTERN**: Prefix staging tables with `stg_`
- ✅ **PATTERN**: Use descriptive variable names and comments

## Development Workflow

### Standard Script Template
```python
"""
Script Description
Purpose: What this script does
"""
import sys
from pathlib import Path

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/ only
from utils.db_helper import get_connection
from utils.logger_helper import get_logger

def main():
    """Main function"""
    logger = get_logger(__name__)
    logger.info("Script starting")
    
    # Database connection the standard way
    with get_connection('orders') as conn:
        # database operations
        pass

if __name__ == "__main__":
    main()
```

### Testing Approach
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test end-to-end workflows with real data
- **Debug Scripts**: Create test scripts in `tests/debug/` for development
- **Validation Scripts**: Verify database operations and data integrity

### VS Code Integration
- **Tasks**: Define all development tasks in `.vscode/tasks.json`
- **Debugging**: Use VS Code debugger for step-through debugging
- **Terminal**: Use PowerShell with `;` for command chaining (not `&&`)

## Critical Fixes Implemented

### Method Signature Alignment
- Fixed argument mismatch in `process_customer_batch` method calls
- Ensured consistent parameter passing between orchestrator and processor

### Unicode Logging Issues
- Removed emoji characters that cause encoding errors in Windows console
- Used plain text logging messages for compatibility

### Table Name Consistency
- Fixed UNIFIED_SNAPSHOT vs ORDERS_UNIFIED_SNAPSHOT naming inconsistency
- Updated all queries to use correct table names from DDL

### Import Error Prevention
- Moved all Python modules to `utils/` folder
- Updated all import statements to use correct paths
- Implemented standard import pattern across all scripts
