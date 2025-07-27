# 🔧 Test Import Patterns - REFERENCE GUIDE

## ✅ WORKING IMPORT PATTERN (DO NOT CHANGE!)

Based on successfully running tests, here's the EXACT pattern that works:

```python
#!/usr/bin/env python3
"""
Test description here
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def main():
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # SQL Template Engine
        engine = SQLTemplateEngine(config)
        
        # Your test code here...
        
        cursor.close()

if __name__ == "__main__":
    main()
```
    
    # Your test code here...
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
```

## 🚨 CRITICAL RULES

1. **NEVER CHANGE THE IMPORT PATTERN** - It works, don't touch it
2. **Config FIRST**: `config = DeltaSyncConfig.from_toml(config_path)`
3. **Database Connection**: `with db.get_connection(config.db_key) as connection:`
4. **Cursor**: `cursor = connection.cursor()`
5. **Template Engine**: `engine = SQLTemplateEngine(config)`
6. **Logger**: `logger = logger.get_logger(__name__)`
7. **Always close cursor**: `cursor.close()`

## 📁 Working Test Examples

These tests ran successfully with this pattern:
- `test_fixed_template.py` ✅
- `test_simplified_merge.py` ✅  
- `test_size_column_detection_issue.py` ✅
- `test_unpivot_quick_diagnosis.py` ✅

## ❌ NEVER DO THESE

```python
# WRONG - Don't do this
from utils.db_helper import get_cursor_and_connection
from pipelines.utils.db_helper import get_cursor_and_connection
from src.pipelines.utils.db_helper import get_cursor_and_connection

# WRONG - Don't do this
config = DeltaSyncConfig("development")
cursor, connection = db.get_cursor_and_connection()

# WRONG - Don't do this  
from pipelines.utils.db import get_cursor_and_connection
```

## 📋 Template for New Tests

Copy this EXACT template for any new test:

```python
#!/usr/bin/env python3
"""
[TEST NAME] - [DESCRIPTION]
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🧪 [TEST NAME]...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # YOUR TEST CODE HERE
        
        cursor.close()

if __name__ == "__main__":
    main()
```

**REMEMBER: This pattern works - DO NOT CHANGE IT!**
