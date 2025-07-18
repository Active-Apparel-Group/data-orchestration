#!/usr/bin/env python3
"""
Shadow Table Schema Validator
=============================
Purpose: Validate SQL operations against shadow table schemas (not production)
Usage: python tools/validate_shadow_schema.py
Created: 2025-07-18 (Milestone 2: Corrected Schema Validation)

This validates that SQL operations reference columns that exist in the 
shadow table schemas (ORDER_LIST_V2, ORDER_LIST_DELTA) which include
delta tracking columns that don't exist in production ORDER_LIST.
"""
import sys
import re
from pathlib import Path
from typing import Set, Dict, List

def find_repo_root():
    """Find repository root directory"""
    current = Path(__file__).parent.parent
    while current != current.parent:
        if (current / "db" / "migrations").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

def extract_columns_from_migration(migration_file: Path) -> Dict[str, Set[str]]:
    """Extract column names from shadow table migration DDL"""
    tables = {}
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by CREATE TABLE statements
    table_sections = re.split(r'CREATE TABLE\s+dbo\.(\w+)', content, flags=re.IGNORECASE)
    
    for i in range(1, len(table_sections), 2):
        table_name = table_sections[i]
        table_ddl = table_sections[i+1]
        
        # Extract column definitions - improved pattern
        columns = set()
        column_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_\s\(\)\/\-]*)\s+(?:NVARCHAR|INT|SMALLINT|DATETIME2|UNIQUEIDENTIFIER|VARCHAR|AS\s)'
        
        lines = table_ddl.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('--') and not line.startswith('CONSTRAINT') and not line.startswith(')'):
                # Match column definition patterns
                if ' ' in line and any(dtype in line.upper() for dtype in ['NVARCHAR', 'INT', 'SMALLINT', 'DATETIME2', 'UNIQUEIDENTIFIER', 'VARCHAR', 'AS ']):
                    # Extract column name (everything before the first space/type)
                    col_match = re.match(r'^\s*(\w+)', line)
                    if col_match:
                        columns.add(col_match.group(1))
                    
                    # Also check for bracket notation
                    bracket_match = re.search(r'\[([^\]]+)\]', line)
                    if bracket_match:
                        columns.add(bracket_match.group(1))
        
        tables[table_name] = columns
    
    return tables

def validate_merge_operations() -> Dict[str, List[str]]:
    """Validate merge operations against shadow table schemas"""
    repo_root = find_repo_root()
    
    # Load shadow table schemas
    migration_file = repo_root / "db" / "migrations" / "001_create_shadow_tables.sql"
    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    shadow_schemas = extract_columns_from_migration(migration_file)
    
    print("Shadow table schemas loaded:")
    for table_name, columns in shadow_schemas.items():
        print(f"  {table_name}: {len(columns)} columns")
    
    # Combine all shadow table columns (since merge operations use multiple tables)
    all_shadow_columns = set()
    for columns in shadow_schemas.values():
        all_shadow_columns.update(columns)
    
    # Add metadata columns that are valid in merge operations
    metadata_columns = {
        'action_type',      # $action in OUTPUT clause
        'batch_id',         # Batch tracking
        'delta_sync_state', # Delta table specific
        'delta_created_at', # Delta table specific
        'synced_at'         # Delta table specific
    }
    all_shadow_columns.update(metadata_columns)
    
    print(f"Total shadow columns available: {len(all_shadow_columns)}")
    
    # Check SQL operations files
    operations_dir = repo_root / "sql" / "operations"
    results = {}
    
    if operations_dir.exists():
        for sql_file in operations_dir.glob("*.sql"):
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract column references
            column_pattern = r'\[([^\]]+)\]'
            referenced_columns = set(re.findall(column_pattern, content))
            
            # Filter out SQL keywords and known non-column references
            sql_keywords = {'DBO', 'ORDER_LIST_V2', 'SWP_ORDER_LIST', 'ORDER_LIST_DELTA', 
                          'ORDER_LIST_LINES', 'ORDER_LIST_LINES_DELTA', 'INSERTED', 'DELETED'}
            
            column_references = {col for col in referenced_columns 
                               if col.upper() not in sql_keywords 
                               and not col.startswith('--')}  # Exclude comments
            
            # Find invalid references
            invalid_columns = column_references - all_shadow_columns
            
            if invalid_columns:
                results[str(sql_file.relative_to(repo_root))] = list(invalid_columns)
                print(f"INVALID REFERENCES in {sql_file.name}:")
                for col in sorted(invalid_columns):
                    print(f"  - [{col}] <- NOT FOUND IN SHADOW SCHEMAS")
            else:
                print(f"VALID: {sql_file.name} - All {len(column_references)} column references found")
    
    return results

def main():
    """Main validation process"""
    print("ORDER_LIST Shadow Table Schema Validator")
    print("=" * 50)
    
    try:
        invalid_refs = validate_merge_operations()
        
        if invalid_refs:
            print(f"\nSHADOW SCHEMA VALIDATION FAILED")
            print(f"Found {len(invalid_refs)} files with invalid column references")
            
            for file_path, invalid_columns in invalid_refs.items():
                print(f"\nFile: {file_path}")
                for invalid_col in invalid_columns:
                    print(f"  [{invalid_col}] -> INVALID REFERENCE")
            
            return 1  # Exit with error
        else:
            print(f"\nSHADOW SCHEMA VALIDATION PASSED")
            print(f"All SQL operations use valid shadow table column references")
            return 0
            
    except Exception as e:
        print(f"VALIDATION ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
