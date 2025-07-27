#!/usr/bin/env python3
"""
Quick Fix for Dynamic Schema Discovery - Column Name Sanitization
================================================================

Fix the SQL syntax errors caused by special characters in column names.
"""
import sys
from pathlib import Path
import re

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

import logger_helper

def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize a string to be a valid SQL identifier
    - Remove special characters
    - Replace spaces with underscores
    - Ensure it starts with a letter
    """
    # Replace special characters and spaces with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Ensure it starts with a letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = f'col_{sanitized}'
    
    # Remove trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'unknown_column'
    
    return sanitized

def apply_fix_to_dynamic_schema_discovery():
    """Apply the column name sanitization fix"""
    logger = logger_helper.get_logger(__name__)
    
    script_path = Path(__file__).parent / "dynamic_schema_discovery.py"
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    # Read the current script
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic line and replace it
    old_line = "test_table_name = f'test_{column_name}_{size}'"
    new_line = "test_table_name = f'test_{sanitize_sql_identifier(column_name)}_{size}'"
    
    if old_line not in content:
        logger.warning("Could not find the exact line to replace. Manual fix needed.")
        return False
    
    # Add the sanitization function at the top of the class
    function_to_add = '''
    def sanitize_sql_identifier(self, identifier: str) -> str:
        """
        Sanitize a string to be a valid SQL identifier
        - Remove special characters
        - Replace spaces with underscores
        - Ensure it starts with a letter
        """
        import re
        # Replace special characters and spaces with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Ensure it starts with a letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = f'col_{sanitized}'
        
        # Remove trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'unknown_column'
        
        return sanitized
'''
    
    # Insert the function after the __init__ method
    init_end = content.find('self.test_increments = [100, 1000, 5000, 10000]') + len('self.test_increments = [100, 1000, 5000, 10000]')
    content = content[:init_end] + function_to_add + content[init_end:]
    
    # Replace the problematic line
    content = content.replace(old_line, new_line.replace('sanitize_sql_identifier', 'self.sanitize_sql_identifier'))
    
    # Write the fixed script
    backup_path = script_path.with_suffix('.py.backup')
    script_path.rename(backup_path)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Applied fix to {script_path}")
    logger.info(f"Backup saved to {backup_path}")
    
    return True

if __name__ == "__main__":
    print("🔧 Applying Quick Fix for Dynamic Schema Discovery")
    print("=" * 60)
    
    success = apply_fix_to_dynamic_schema_discovery()
    
    if success:
        print("✅ Fix applied successfully!")
        print("\nThe script should now handle column names with special characters.")
        print("You can restart the dynamic schema discovery process.")
    else:
        print("❌ Fix failed. Manual intervention required.")
        print("\nThe issue is in line:")
        print("test_table_name = f'test_{column_name}_{size}'")
        print("Should be:")
        print("test_table_name = f'test_{sanitize_sql_identifier(column_name)}_{size}'")
