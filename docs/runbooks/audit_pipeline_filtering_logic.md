# Audit Pipeline Filtering Logic

## Overview

This document explains the filtering approach used in the audit pipeline for handling SQL queries and data filtering. The pipeline uses a hybrid approach combining SQL file execution with Python-based filtering for maximum flexibility and maintainability.

## Architecture

### File Structure
```
sql/
├── staging/                    # Base SQL queries
│   ├── v_packed_products.sql   # Core packed products query
│   ├── v_shipped.sql          # Core shipped products query
│   └── v_master_order_list.sql # Master order list query
└── pipelines/                 # Pipeline-specific views (deprecated)
    ├── v_packed_products_audit_pipeline.sql
    └── v_shipped_audit_pipeline.sql

src/
├── audit_pipeline/
│   └── config.py              # Enhanced run_sql function
└── jobs/
    └── run_audit.py           # Main audit script with filtering
```

## Filtering Approach

### Current Implementation: Python-Based Filtering ⭐ (Recommended)

The audit pipeline uses a **hybrid approach** that combines SQL execution with Python filtering:

1. **Execute base SQL files** - Run the original staging SQL queries
2. **Apply filters in Python** - Filter the pandas DataFrames after SQL execution
3. **Maintain single source of truth** - No duplication of SQL logic

### Code Example

```python
# Run base queries
packed = run_sql('staging/v_packed_products.sql', 'distribution')
shipped = run_sql('staging/v_shipped.sql', 'wah')
master = run_sql('staging/v_master_order_list.sql', 'orders')

# Apply filters in Python
if 'Size' in packed.columns:
    packed = packed[packed['Size'] != 'SMS']
    print(f"Packed data filtered: {len(packed)} rows remaining after removing SMS sizes")

if 'Size' in shipped.columns:
    shipped = shipped[shipped['Size'] != 'SMS']
    print(f"Shipped data filtered: {len(shipped)} rows remaining after removing SMS sizes")
```

## Enhanced run_sql Function

The `run_sql` function in `config.py` has been enhanced to support optional parameters:

```python
def run_sql(filename, db_key, params=None):
    """Read and execute SQL from /sql directory, return DataFrame."""
    sql_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sql'))
    with open(os.path.join(sql_dir, filename), "r") as f:
        query = f.read()
    
    # Replace parameters in SQL if provided
    if params:
        for key, value in params.items():
            placeholder = f"{{{key}}}"  # e.g., {size_filter}
            query = query.replace(placeholder, str(value))
    
    with get_connection(db_key) as conn:
        return pd.read_sql(query, conn)
```

### Usage Options

```python
# Option 1: Basic usage (current)
data = run_sql('staging/v_packed_products.sql', 'distribution')

# Option 2: With parameters (future use)
data = run_sql('staging/v_packed_products.sql', 'distribution', 
               params={'size_filter': 'SMS', 'date_filter': '2024-01-01'})
```

## Filtering Strategies Comparison

| Approach                   | Pros                                                                                            | Cons                                                                   | Recommendation         |
| -------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------- |
| **Python Filtering**       | ✅ No SQL duplication<br>✅ Flexible & debuggable<br>✅ Easy to modify<br>✅ Single source of truth | ⚠️ Memory usage for large datasets                                      | **✅ Current choice**   |
| **SQL File Duplication**   | ✅ Database-level filtering                                                                      | ❌ Code duplication<br>❌ Maintenance overhead<br>❌ Hard to sync changes | ❌ Avoid                |
| **Dynamic SQL Parameters** | ✅ Database-level filtering<br>✅ No duplication                                                  | ⚠️ More complex<br>⚠️ SQL injection risks                                | 🔄 Future consideration |
| **Database Views**         | ✅ Reusable across applications                                                                  | ❌ Requires DB schema changes<br>❌ Not portable                         | ❌ Not applicable here  |

## Current Filters Applied

### Size Filtering
- **Filter**: Exclude records where `Size = 'SMS'`
- **Applied to**: 
  - `v_packed_products.sql` results
  - `v_shipped.sql` results
- **Rationale**: SMS sizes are not relevant for the audit process

### Implementation
```python
# Size filter applied in Python
if 'Size' in dataframe.columns:
    dataframe = dataframe[dataframe['Size'] != 'SMS']
```

## Data Quality Issues and Fixes

### NONE Value Handling

**Issue**: The matching logic was incorrectly treating 'NONE' string values as valid purchase order (PO) numbers, resulting in false matches with 100% match scores.

**Root Cause**: 
- ETL process stored null/empty values as the string 'NONE' instead of proper NULL values
- Matching logic used `pd.notna()` which treats 'NONE' strings as valid data
- PO comparison logic didn't validate that PO values were meaningful

**Solution Implemented**:

1. **Enhanced ETL null handling** (`etl.py`):
   ```python
   # Replace various null-like strings with actual None values
   df = df.replace(['NAN', 'NONE', 'NULL', ''], None)
   ```

2. **Added PO validation function** (`matching.py`):
   ```python
   def is_valid_po_value(value):
       """Check if a PO value is valid for matching (not null, empty, or placeholder)."""
       if pd.isna(value):
           return False
       str_val = str(value).strip().upper()
       if str_val in ['', 'NONE', 'NULL', 'NAN', 'N/A']:
           return False
       return True
   ```

3. **Updated matching key creation**:
   - `create_matching_key()` now uses `is_valid_po_value()` instead of `pd.notna()`
   - `create_alternate_matching_keys()` now validates PO values before including them

4. **Fixed PO comparison logic**:
   - Exact matching now validates PO values before comparison
   - Fuzzy matching excludes invalid PO values from similarity calculations
   - Match scores are only assigned when valid PO values are compared

### Impact of Fixes

**Before Fix**:
```
Customer_PO: 4053, Customer_Alt_PO: NONE
Best_Match_PO: 2979, Best_Match_Alt_PO: NONE
PO_Match_Score: 100, Alt_PO_Match_Score: 100  ❌ Incorrect!
```

**After Fix**:
```
Customer_PO: 4053, Customer_Alt_PO: NONE
Best_Match_PO: 2979, Best_Match_Alt_PO: NONE  
PO_Match_Score: 100, Alt_PO_Match_Score: 0    ✅ Correct!
```

**Benefits**:
- Eliminates false positive matches on null/placeholder values
- Improves data quality scoring accuracy
- Reduces misleading match scores in audit reports
- Better identifies genuine data quality issues

## Benefits of Current Approach

### 1. **Maintainability**
- Single source of truth for base queries
- Changes to core logic only need to be made in one place
- Easy to add/remove/modify filters

### 2. **Flexibility**
- Can apply different filters for different use cases
- Easy to add command-line arguments for dynamic filtering
- Can combine multiple filter conditions

### 3. **Debugging**
- Clear separation between data retrieval and filtering
- Can inspect data before and after filtering
- Logging shows exactly what filters were applied

### 4. **Performance**
- Base SQL queries are optimized for the database
- Python filtering is efficient for typical dataset sizes
- Can add sampling for development/testing

## Future Enhancements

### Command Line Filtering
```python
parser.add_argument('--exclude-size', type=str, help='Exclude specific sizes (e.g., SMS)')
parser.add_argument('--min-date', type=str, help='Filter records from this date')
parser.add_argument('--customer', type=str, help='Filter by customer name')

# Apply dynamic filters
if args.exclude_size:
    packed = packed[packed['Size'] != args.exclude_size]
    shipped = shipped[shipped['Size'] != args.exclude_size]
```

### Configuration-Based Filtering
```yaml
# config/filters.yaml
audit_filters:
  size:
    exclude: ['SMS', 'SAMPLE']
  date:
    min_date: '2024-01-01'
  customer:
    exclude: ['TEST_CUSTOMER']
```

## Database Connections

The pipeline connects to multiple databases:
- **distribution**: For packed products data
- **wah**: For shipped products data  
- **orders**: For master order list data

Each connection is configured via environment variables in the `.env` file.

## Best Practices

### 1. **Always Check Column Existence**
```python
if 'Size' in dataframe.columns:
    # Apply filter
```

### 2. **Log Filter Results**
```python
original_count = len(dataframe)
dataframe = dataframe[dataframe['Size'] != 'SMS']
filtered_count = len(dataframe)
print(f"Filtered {original_count - filtered_count} rows, {filtered_count} remaining")
```

### 3. **Use Descriptive Variable Names**
```python
packed_raw = run_sql('staging/v_packed_products.sql', 'distribution')
packed_filtered = packed_raw[packed_raw['Size'] != 'SMS']
```

### 4. **Handle Missing Data Gracefully**
```python
if 'Size' in dataframe.columns and not dataframe['Size'].isna().all():
    dataframe = dataframe[dataframe['Size'] != 'SMS']
```

## Troubleshooting

### Common Issues

1. **"Invalid object name" errors**
   - Ensure SQL files contain complete queries, not references to database views
   - Check database connections are properly configured

2. **Column not found errors**
   - Always check if column exists before filtering
   - Verify SQL query returns expected columns

3. **Empty results after filtering**
   - Check if filter conditions are too restrictive
   - Verify data contains expected values

### Debugging Tips

```python
# Debug data before filtering
print(f"Data shape before filtering: {dataframe.shape}")
print(f"Unique Size values: {dataframe['Size'].unique()}")

# Apply filter
dataframe_filtered = dataframe[dataframe['Size'] != 'SMS']

# Debug data after filtering
print(f"Data shape after filtering: {dataframe_filtered.shape}")
```

## Related Documentation

- [Customer Mapping Logic](../mapping/customer_mapping.yaml)
- [SQL Query Reference](../../sql/staging/)
- [Environment Configuration](../design/migrate_config_yaml_to_env.md)
- [Performance Optimization](../copilot_updates/PERFORMANCE_OPTIMIZATION_ANALYSIS.md)

---

**Last Updated**: June 2, 2025  
**Author**: Development Team  
**Version**: 1.0  
**Review**: Recommended for quarterly review as filtering requirements evolve
