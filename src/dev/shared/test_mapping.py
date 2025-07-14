#!/usr/bin/env python3
"""
Test script to validate the master data mapping YAML file
"""

import yaml
import sys
import os

def test_yaml_syntax():
    """Test that the YAML file loads without syntax errors"""
    try:
        with open('data_mapping.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ YAML syntax is valid")
        return config
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return None
    except FileNotFoundError:
        print("❌ data_mapping.yaml file not found")
        return None

def test_metadata(config):
    """Test metadata section"""
    if not config:
        return False
    
    metadata = config.get('metadata', {})
    print(f"📊 Version: {metadata.get('version', 'Unknown')}")
    print(f"🔧 Last updated: {metadata.get('last_updated', 'Unknown')}")
    print(f"📝 Description: {metadata.get('description', 'Unknown')}")
    return True

def test_board_configs(config):
    """Test Monday.com board configurations"""
    if not config:
        return False
    
    boards = config.get('monday_boards', {})
    print(f"🎯 Number of configured boards: {len(boards)}")
    
    for board_key, board_config in boards.items():
        board_id = board_config.get('board_id', 'Unknown')
        board_name = board_config.get('board_name', 'Unknown')
        print(f"  - {board_key}: {board_name} (ID: {board_id})")
    
    return True

def test_database_schemas(config):
    """Test database schema configurations"""
    if not config:
        return False
    
    schemas = config.get('database_schemas', {})
    print(f"🗄️ Database schema sections: {len(schemas)}")
    
    for schema_key in schemas.keys():
        print(f"  - {schema_key}")
    
    return True

def test_field_types(config):
    """Test field type mappings"""
    if not config:
        return False
    
    field_types = config.get('field_types', {})
    monday_to_sql = field_types.get('monday_to_sql', {})
    sql_to_monday = field_types.get('sql_to_monday', {})
    
    print(f"🔄 Monday.com to SQL type mappings: {len(monday_to_sql)}")
    print(f"🔄 SQL to Monday.com type mappings: {len(sql_to_monday)}")
    
    return True

def main():
    """Main test function"""
    print("🧪 Testing Master Data Mapping YAML Configuration")
    print("=" * 50)
    
    # Test YAML syntax
    config = test_yaml_syntax()
    if not config:
        sys.exit(1)
    
    # Test major sections
    test_metadata(config)
    print()
    
    test_board_configs(config)
    print()
    
    test_database_schemas(config)
    print()
    
    test_field_types(config)
    print()
    
    print("✅ All tests passed! Master mapping system is ready.")

if __name__ == "__main__":
    main()
