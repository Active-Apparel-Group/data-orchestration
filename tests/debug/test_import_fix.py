#!/usr/bin/env python3
"""
Test import pattern to verify utils can be properly imported
"""
import sys
from pathlib import Path

def find_repo_root(): 
    current = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    while current != current.parent:
        if (current / 'utils').exists():       
            return current
        current = current.parent
    raise FileNotFoundError('Could not find repository root')

def main():
    try:
        repo_root = find_repo_root()
        print(f'Found repo root: {repo_root}')     
        print(f'Utils exists: {(repo_root / "utils").exists()}')
        
        # Add utils to path
        sys.path.insert(0, str(repo_root / 'utils'))
        
        # Test importing db_helper
        import db_helper  
        print('✅ Successfully imported db_helper')
        
        # Test importing mapping_helper
        import mapping_helper
        print('✅ Successfully imported mapping_helper')
        
        # Test loading mapping config
        config = mapping_helper.load_orders_mapping_config()
        print(f'✅ Mapping config loaded - version: {config.get("metadata", {}).get("version", "unknown")}')
        
        # Test getting field mappings
        field_mappings = mapping_helper.get_orders_field_mappings()
        print(f'✅ Field mappings loaded - count: {len(field_mappings)}')
        
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
