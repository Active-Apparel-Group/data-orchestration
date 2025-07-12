---
applyTo: '**'
---

# Quick Fixes & Common Mistakes

## 🚨 CRITICAL: Import Errors - Never Import from sql/ folder

**❌ WRONG:**
```python
from sql.mappings.simple_mapper import SimpleOrdersMapper  # BAD - importing from sql/
```

**✅ CORRECT:**
```python
from utils.simple_mapper import SimpleOrdersMapper  # GOOD - importing from utils/
```

## 📁 File Placement Rules

**❌ NEVER put Python modules in:**
- `sql/` folder (not a Python package)
- `queries/` folder (for SQL only)  
- `docs/` folder (documentation only)

**✅ ALWAYS put Python modules in:**
- `utils/` - All utility modules (.py files)
- `scripts/` - Executable scripts only
- `tests/` - Test files only

## 🔧 Quick Fixes for Common Issues

### Import Error Fix:
```bash
# Move misplaced Python files:
move "sql/mappings/file.py" "utils/file.py"
# Update imports to use utils/
```

### Database Connection:
```python
# ALWAYS use this pattern:
import db_helper as db
# Use appropriate database from config.yaml (dms, dms_item, orders, infor_132)
with db.get_connection('database_name') as conn:
    # database operations
```

### Configuration Loading:
```python
# ALWAYS load config this way:
import db_helper as db
config = db.load_config()
```

### PowerShell vs Bash:
```powershell
# Use ; not && in PowerShell:
cd "path"; python script.py  # ✅ CORRECT
cd "path" && python script.py  # ❌ WRONG in PowerShell
```

## 🎯 Standard Import Pattern:
```python
import sys
from pathlib import Path

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Now import from utils/
import db_helper as db
import logger_helper
```