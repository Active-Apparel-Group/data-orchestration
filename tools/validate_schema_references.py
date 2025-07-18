#!/usr/bin/env python3
"""
Schema Reference Validator
==========================
Purpose: Validate that all SQL operations reference actual columns from DDL schema
Usage: python tools/validate_schema_references.py
Created: 2025-07-18 (Milestone 2: Schema Validation)

This tool prevents the critical issue where SQL operations reference
non-existent columns by validating against the actual DDL schema.
"""
import sys
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple

def find_repo_root():
    """Find repository root directory"""
    current = Path(__file__).parent.parent
    while current != current.parent:
        if (current / "db" / "ddl").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

def extract_columns_from_ddl(ddl_file: Path) -> Set[str]:
    """Extract all column names from DDL CREATE TABLE statement"""
    columns = set()
    
    with open(ddl_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match column definitions: [COLUMN NAME] TYPE
    column_pattern = r'\[([^\]]+)\]\s+(?:NVARCHAR|INT|SMALLINT|DATETIME2|UNIQUEIDENTIFIER)'
    
    matches = re.findall(column_pattern, content, re.IGNORECASE)
    for match in matches:
        columns.add(match)
    
    return columns

def extract_column_references_from_sql(sql_file: Path) -> Set[str]:
    """Extract all column references from SQL operations file"""
    references = set()
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match [COLUMN NAME] references
    column_pattern = r'\[([^\]]+)\]'
    
    matches = re.findall(column_pattern, content)
    for match in matches:
        # Filter out SQL keywords and table names
        if match.upper() not in ['DBO', 'ORDER_LIST_V2', 'SWP_ORDER_LIST', 'ORDER_LIST_DELTA']:
            references.add(match)
    
    return references

def validate_schema_references() -> Dict[str, List[str]]:
    """Validate all SQL operations against DDL schema"""
    repo_root = find_repo_root()
    
    # Load schema columns
    ddl_file = repo_root / "db" / "ddl" / "tables" / "orders" / "dbo_order_list.sql"
    if not ddl_file.exists():
        raise FileNotFoundError(f"DDL file not found: {ddl_file}")
    
    schema_columns = extract_columns_from_ddl(ddl_file)
    print(f"Schema columns loaded: {len(schema_columns)} columns from {ddl_file.name}")
    
    # Check SQL operations files
    operations_dir = repo_root / "sql" / "operations"
    results = {}
    
    if operations_dir.exists():
        for sql_file in operations_dir.glob("*.sql"):
            referenced_columns = extract_column_references_from_sql(sql_file)
            
            # Find invalid references
            invalid_columns = referenced_columns - schema_columns
            
            if invalid_columns:
                results[str(sql_file.relative_to(repo_root))] = list(invalid_columns)
                print(f"INVALID REFERENCES in {sql_file.name}:")
                for col in sorted(invalid_columns):
                    print(f"  - [{col}] <- NOT FOUND IN SCHEMA")
            else:
                print(f"VALID: {sql_file.name} - All {len(referenced_columns)} column references found in schema")
    
    return results

def suggest_corrections(invalid_columns: List[str], schema_columns: Set[str]) -> Dict[str, str]:
    """Suggest corrections for invalid column names"""
    suggestions = {}
    
    for invalid_col in invalid_columns:
        # Simple similarity matching
        invalid_upper = invalid_col.upper()
        
        for schema_col in schema_columns:
            schema_upper = schema_col.upper()
            
            # Exact substring match
            if invalid_upper in schema_upper or schema_upper in invalid_upper:
                suggestions[invalid_col] = schema_col
                break
            
            # Word matching for common patterns
            invalid_words = invalid_upper.replace('_', ' ').split()
            schema_words = schema_upper.replace('_', ' ').split()
            
            common_words = set(invalid_words) & set(schema_words)
            if len(common_words) >= 2:  # At least 2 words match
                suggestions[invalid_col] = schema_col
                break
    
    return suggestions

def main():
    """Main validation process"""
    print("ORDER_LIST Schema Reference Validator")
    print("=" * 50)
    
    try:
        invalid_refs = validate_schema_references()
        
        if invalid_refs:
            print(f"\nSCHEMA VALIDATION FAILED")
            print(f"Found {len(invalid_refs)} files with invalid column references")
            
            # Load schema for suggestions
            repo_root = find_repo_root()
            ddl_file = repo_root / "db" / "ddl" / "tables" / "orders" / "dbo_order_list.sql"
            schema_columns = extract_columns_from_ddl(ddl_file)
            
            for file_path, invalid_columns in invalid_refs.items():
                print(f"\nFile: {file_path}")
                suggestions = suggest_corrections(invalid_columns, schema_columns)
                
                for invalid_col in invalid_columns:
                    if invalid_col in suggestions:
                        print(f"  [{invalid_col}] -> SUGGESTED: [{suggestions[invalid_col]}]")
                    else:
                        print(f"  [{invalid_col}] -> NO SUGGESTION FOUND")
            
            return 1  # Exit with error
        else:
            print(f"\nSCHEMA VALIDATION PASSED")
            print(f"All SQL operations use valid column references")
            return 0
            
    except Exception as e:
        print(f"VALIDATION ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
