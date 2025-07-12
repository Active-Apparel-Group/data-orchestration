---
applyTo: '**'
---

# Python Import Standards for Data Orchestration Project

## 🚨 CRITICAL RULES - Import Error Prevention

### ❌ NEVER Import From These Folders:
```python
from sql.anything import Something        # sql/ is NOT a Python package
from queries.file import Function        # queries/ is for SQL files only
from docs.mapping.file import Data       # docs/ is documentation only
```

### ✅ ALWAYS Import From These Locations:
```python
from utils.module_name import ClassName   # All utilities go in utils/
from scripts.folder.script import func   # Only for executable scripts
```

## 📁 File Organization Rules

### utils/ Folder - Python Utilities:
- **Purpose**: All reusable Python modules
- **Examples**: `db_helper.py`, `logger_helper.py`, `simple_mapper.py`
- **Rule**: If it's a `.py` file with classes/functions, it goes in `utils/`

### sql/ Folder - SQL and Config Only:
- **Purpose**: SQL files, GraphQL templates, mappings, payloads
- **Examples**: `.sql`, `.graphql`, `.yaml`, `.json` configuration files
- **Rule**: NO `.py` files allowed (they can't be imported)

### scripts/ Folder - Executable Scripts:
- **Purpose**: Scripts that are run directly
- **Rule**: These import from `utils/`, never the other way around

## 🔧 Standard Import Pattern:

```python
"""
Standard import pattern for all scripts
Use this exact pattern to avoid import errors
"""
import sys
from pathlib import Path

# Add project root to Python path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Now import from utils/ (PRODUCTION PATTERN)
import db_helper as db
import logger_helper

# Usage
logger = logger_helper.get_logger(__name__)
with db.get_connection('database_name') as conn:
    # database operations
```

## 🎯 Specific Import Examples:

### Database Operations:
```python
import db_helper as db
with db.get_connection('dms') as conn:
    # database work here
```

### Logging:
```python
import logger_helper
logger = logger_helper.get_logger(__name__)
logger.info("Message")
```

### Configuration:
```python
import db_helper as db
config = db.load_config()
```

### Simple Mapping:
```python
from utils.simple_mapper import SimpleOrdersMapper
mapper = SimpleOrdersMapper()
result = mapper.transform_master_item(data)
```

## 🚨 Import Error Troubleshooting:

### Error: "ModuleNotFoundError: No module named 'sql'"
**Cause**: Trying to import from sql/ folder  
**Fix**: Move the Python file to utils/ folder

### Error: "ImportError: attempted relative import"
**Cause**: Wrong import syntax  
**Fix**: Use the standard import pattern above

### Error: "ModuleNotFoundError: No module named 'utils'"
**Cause**: Python path not set correctly  
**Fix**: Use the `sys.path.append()` pattern above