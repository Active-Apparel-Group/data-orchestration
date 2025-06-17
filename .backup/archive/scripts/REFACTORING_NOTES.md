# Script Refactoring: get_board_planning.py

## Overview
Refactored the `get_board_planning.py` script to use the standardized `db_helper.py` module instead of custom database connection code.

## Changes Made

### 1. Import Changes
- **Before**: Direct `pyodbc` imports and custom connection building
- **After**: Import `db_helper` module from utils directory
```python
# Added path management for utils import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))
import db_helper as db
```

### 2. Database Connection Refactoring

#### Removed Custom Connection Function
**Before**:
```python
def get_database_connection(db_name='orders'):
    """Create database connection using environment variables from Kestra workflow"""
    env_prefix = f"DB_{db_name.upper()}_"
    config = {
        'host': os.getenv(f'{env_prefix}HOST'),
        'port': os.getenv(f'{env_prefix}PORT', '1433'),
        # ... more config
    }
    conn_str = f"DRIVER={{SQL Server}};SERVER={config['host']},{config['port']};..."
    return pyodbc.connect(conn_str, timeout=60)
```

**After**: Uses `db_helper.get_connection()` directly

### 3. Function Updates

#### truncate_table()
**Before**: Manual cursor management
```python
conn = get_database_connection('orders')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM dbo.MON_COO_Planning")
old_count = cursor.fetchone()[0]
# ... manual cleanup
```

**After**: Uses db_helper methods
```python
count_result = db.run_query("SELECT COUNT(*) as count FROM dbo.MON_COO_Planning", "orders")
old_count = count_result.iloc[0]['count']
db.execute("TRUNCATE TABLE dbo.MON_COO_Planning", "orders")
```

#### concurrent_insert_chunk()
**Before**: Custom connection creation and cursor management
```python
conn = get_database_connection('orders')
cursor = conn.cursor()
# ... manual operations
cursor.close()
conn.close()
```

**After**: Uses db_helper connection
```python
conn = db.get_connection('orders')
cursor = conn.cursor()
# ... operations (maintained executemany for performance)
cursor.close()
conn.close()
```

#### production_concurrent_insert()
**Before**: Manual connection and cursor for schema queries
```python
conn = get_database_connection('orders')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('dbo.MON_COO_Planning')")
valid_cols = {row[0] for row in cursor.fetchall()}
```

**After**: Uses db_helper query method
```python
columns_query = "SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('dbo.MON_COO_Planning')"
columns_df = db.run_query(columns_query, "orders")
valid_cols = set(columns_df['name'].tolist())
```

## Benefits

1. **Standardization**: Uses the centralized `db_helper.py` module
2. **Configuration**: Leverages `config.yaml` instead of environment variables
3. **Error Handling**: Inherits improved error handling from db_helper
4. **Maintenance**: Reduces code duplication and maintenance overhead
5. **Consistency**: Aligns with other scripts using db_helper pattern

## Configuration Requirements

The script now expects database configuration in `utils/config.yaml`:
```yaml
databases:
  orders:
    host: "your-server"
    port: 1433
    database: "your-database"
    username: "your-username"
    password: "your-password"
    driver: "{ODBC Driver 17 for SQL Server}"
    encrypt: "yes"
    trustServerCertificate: "yes"
```

## Backward Compatibility

- The script maintains the same external interface
- Performance characteristics are preserved (still uses executemany for bulk inserts)
- All original functionality is retained

## Testing

Run the test script to verify the refactoring:
```bash
cd scripts/monday-boards
python test_refactored_script.py
```
