---
applyTo: '**'
---

# Enhanced Python Standards - Data Orchestration Project

## 🎯 Core Principles

### File Organization Standards:
- **utils/**: All Python modules (.py files with classes/functions)
- **sql/**: Database files (.sql, .graphql, .yaml configs) - NO Python code
- **scripts/**: Executable Python scripts that import from utils/
- **tests/**: Test files and debug examples

### Import Standards:
- **ALWAYS** import utilities from `utils/` folder
- **NEVER** import from `sql/`, `docs/`, or `queries/` folders
- **ALWAYS** use standard import pattern with sys.path.append()

## 🔧 Standard Code Patterns

### 1. Script Template with Proper Imports:
```python
"""
Script Description
Purpose: What this script does
"""
import sys
from pathlib import Path
import yaml
import pandas as pd

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

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper

def main():
    """Main function"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Script starting")
      # Load config the standard way
    config = db.load_config()
    
    # Database connection the standard way
    # Use appropriate database from config.yaml (dms, dms_item, orders, infor_132)
    with db.get_connection('dms') as conn:
        # database operations
        pass

if __name__ == "__main__":
    main()
```

### 2. Utility Module Template:
```python
"""
Utility Module: [Module Name]
Purpose: [What this module provides]
Location: utils/[module_name].py
"""
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

class UtilityClass:
    """Description of the utility class"""
    
    def __init__(self, config_path: str = "utils/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with type hints and docstring"""
        # Implementation here
        return processed_data

# Factory function for easy usage
def create_utility() -> UtilityClass:
    """Factory function to create utility instance"""
    return UtilityClass()
```

### 3. Database Operation Pattern:
```python
import db_helper as db
import logger_helper

def query_orders(customer_filter: str = None) -> pd.DataFrame:    """Query orders with optional customer filter"""
    logger = logger_helper.get_logger(__name__)
    
    sql = """
    SELECT 
        [AAG ORDER NUMBER],
        [CUSTOMER],
        [ORDER QTY],
        [DUE DATE]
    FROM [dbo].[ORDERS_UNIFIED]
    WHERE (@customer_filter IS NULL OR [CUSTOMER] = @customer_filter)
    """
      try:
        # Use appropriate database from config.yaml (dms, dms_item, orders, infor_132)
        with db.get_connection('orders') as conn:
            df = pd.read_sql(sql, conn, params={'customer_filter': customer_filter})
            logger.info(f"Retrieved {len(df)} orders")
            return df
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise
```

## 🚨 Error Prevention Rules

### Import Error Prevention:
```python
# ❌ WRONG - These will cause ModuleNotFoundError:
from utils.simple_mapper import SimpleOrdersMapper
from docs.mapping.config import settings
from queries.helper import function

# ✅ CORRECT - These will work:
from utils.simple_mapper import SimpleOrdersMapper
from utils.config_loader import load_settings
from utils.query_helper import function
```

### Configuration Loading:
```python
# ✅ ALWAYS load config this way:
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

# ❌ NEVER hardcode paths or use relative imports
```

### Database Connections:
```python
# ✅ ALWAYS use the db_helper pattern:
import db_helper as db
# Use appropriate database from config.yaml (dms, dms_item, orders, infor_132)
with db.get_connection('database_name') as conn:
    # operations here

# ❌ NEVER create direct connections in scripts
```

## 🎯 Monday.com Integration Patterns

### Simple Mapping Usage:
```python
from utils.simple_mapper import SimpleOrdersMapper

# Initialize mapper
mapper = SimpleOrdersMapper()

# Transform data
monday_payload = mapper.transform_master_item(source_data)

# Validate before sending
validation = mapper.validate_data(source_data)
if validation['valid']:
    # Send to Monday.com API
    pass
```

### GraphQL Template Loading:
```python
# Load GraphQL from sql/graphql/ (as text, not import)
def load_graphql_template(template_name: str) -> str:
    """Load GraphQL template from sql/graphql/ folder"""
    template_path = Path(f"sql/graphql/mutations/{template_name}.graphql")
    with open(template_path, 'r') as f:
        return f.read()

# Usage:
create_item_query = load_graphql_template('create-master-item')
```

## 🔧 Debugging and Testing

### Debug Script Pattern:
```python
"""
Debug Script: [Purpose]
Location: tests/debug/[script_name].py
"""
import sys
from pathlib import Path

# Add project root for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.simple_mapper import SimpleOrdersMapper
from utils.db_helper import get_connection

def debug_mapping():
    """Debug mapping functionality"""
    # Test data
    test_data = {
        "AAG ORDER NUMBER": "JOO-00505",
        "CUSTOMER": "greyson",
        "ORDER QTY": 720
    }
    
    # Test mapper
    mapper = SimpleOrdersMapper()
    result = mapper.transform_master_item(test_data)
    print(f"Mapping result: {result}")

if __name__ == "__main__":
    debug_mapping()
```

## 🚀 PowerShell Integration

### VS Code Task Execution:
```yaml
# In .vscode/tasks.json - use correct PowerShell syntax
{
    "label": "Test Simple Mapping",
    "type": "shell", 
    "command": "python",
    "args": ["tests/debug/simple_mapping_example.py"],
    "options": {"cwd": "${workspaceFolder}"}
}
```

### PowerShell Script Execution:
```powershell
# Use ; for command chaining in PowerShell (not &&)
cd "c:\path\to\project"; python script.py

# NOT this (bash syntax):
cd "c:\path\to\project" && python script.py
```