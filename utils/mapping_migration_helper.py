"""
Master Data Mapping Migration Helper

This module provides utilities for migrating from existing mapping files
to the new centralized mapping system. It ensures compatibility and provides
tools for gradual transition without breaking existing code.

Usage:
    # For future migration of existing scripts
    from mapping_migration_helper import create_compatibility_layer
    
    # Generate compatibility mapping for old field references
    legacy_mapping = create_compatibility_layer('docs/mapping/orders_unified_monday_mapping.yaml')
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import mapping_helper as mapping


class MigrationError(Exception):
    """Raised when migration operations fail"""
    pass


def analyze_existing_mappings() -> Dict:
    """
    Analyze all existing mapping files and report on their content.
    
    Returns:
        Dict with analysis results and migration recommendations
    """
    docs_mapping_path = Path(__file__).parent.parent / "docs" / "mapping"
    
    analysis = {
        'files_found': [],
        'total_mappings': 0,
        'mapping_types': {},
        'recommendations': [],
        'potential_conflicts': []
    }
    
    if not docs_mapping_path.exists():
        analysis['recommendations'].append("No docs/mapping directory found")
        return analysis
    
    # Analyze each mapping file
    for file_path in docs_mapping_path.glob("*.yaml"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            file_info = {
                'path': str(file_path),
                'name': file_path.name,
                'size_kb': round(file_path.stat().st_size / 1024, 2),
                'structure': _analyze_yaml_structure(content)
            }
            
            analysis['files_found'].append(file_info)
            
        except Exception as e:
            analysis['recommendations'].append(f"Could not parse {file_path.name}: {e}")
    
    # Analyze JSON files
    for file_path in docs_mapping_path.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            file_info = {
                'path': str(file_path),
                'name': file_path.name,
                'size_kb': round(file_path.stat().st_size / 1024, 2),
                'structure': _analyze_json_structure(content)
            }
            
            analysis['files_found'].append(file_info)
            
        except Exception as e:
            analysis['recommendations'].append(f"Could not parse {file_path.name}: {e}")
    
    # Generate recommendations
    analysis['total_files'] = len(analysis['files_found'])
    analysis['recommendations'].extend(_generate_migration_recommendations(analysis))
    
    return analysis


def _analyze_yaml_structure(content: Dict) -> Dict:
    """Analyze the structure of a YAML mapping file"""
    structure = {
        'top_level_keys': list(content.keys()) if isinstance(content, dict) else [],
        'estimated_mappings': 0,
        'has_metadata': False,
        'mapping_patterns': []
    }
    
    if isinstance(content, dict):
        # Check for common patterns
        if 'metadata' in content:
            structure['has_metadata'] = True
        
        if 'exact_matches' in content:
            structure['mapping_patterns'].append('exact_matches')
            if isinstance(content['exact_matches'], list):
                structure['estimated_mappings'] += len(content['exact_matches'])
        
        if 'fields' in content:
            structure['mapping_patterns'].append('fields')
            if isinstance(content['fields'], list):
                structure['estimated_mappings'] += len(content['fields'])
        
        if 'customers' in content:
            structure['mapping_patterns'].append('customers')
            if isinstance(content['customers'], list):
                structure['estimated_mappings'] += len(content['customers'])
    
    return structure


def _analyze_json_structure(content: Union[Dict, List]) -> Dict:
    """Analyze the structure of a JSON mapping file"""
    structure = {
        'type': 'dict' if isinstance(content, dict) else 'list',
        'estimated_mappings': 0,
        'has_metadata': False,
        'mapping_patterns': []
    }
    
    if isinstance(content, dict):
        structure['top_level_keys'] = list(content.keys())
        
        if 'metadata' in content:
            structure['has_metadata'] = True
        
        if 'mappable_fields' in content:
            structure['mapping_patterns'].append('mappable_fields')
            mappable = content['mappable_fields']
            if isinstance(mappable, dict):
                for key, value in mappable.items():
                    if isinstance(value, dict):
                        structure['estimated_mappings'] += len(value)
    
    elif isinstance(content, list):
        structure['estimated_mappings'] = len(content)
    
    return structure


def _generate_migration_recommendations(analysis: Dict) -> List[str]:
    """Generate migration recommendations based on analysis"""
    recommendations = []
    
    if analysis['total_files'] == 0:
        recommendations.append("No mapping files found - migration not needed")
        return recommendations
    
    recommendations.append(f"Found {analysis['total_files']} mapping files to potentially migrate")
    
    # Check for large files that might need special handling
    large_files = [f for f in analysis['files_found'] if f['size_kb'] > 50]
    if large_files:
        recommendations.append(f"Large files found ({len(large_files)}) - consider breaking into sections")
    
    # Check for files with metadata
    files_with_metadata = [f for f in analysis['files_found'] if f['structure'].get('has_metadata')]
    if files_with_metadata:
        recommendations.append(f"Files with metadata ({len(files_with_metadata)}) - preserve versioning info")
    
    return recommendations


def create_compatibility_layer(legacy_file_path: str) -> Dict:
    """
    Create a compatibility layer for accessing legacy mapping file data
    through the new mapping system interface.
    
    Args:
        legacy_file_path: Path to legacy mapping file
        
    Returns:
        Dict with compatibility mappings
    """
    if not os.path.exists(legacy_file_path):
        raise MigrationError(f"Legacy file not found: {legacy_file_path}")
    
    # Load legacy file
    try:
        with open(legacy_file_path, 'r', encoding='utf-8') as f:
            if legacy_file_path.endswith('.json'):
                legacy_content = json.load(f)
            else:
                legacy_content = yaml.safe_load(f)
    except Exception as e:
        raise MigrationError(f"Cannot load legacy file {legacy_file_path}: {e}")
    
    compatibility = {
        'legacy_file': legacy_file_path,
        'migration_date': None,  # Will be set when migration happens
        'field_mappings': {},
        'type_mappings': {},
        'board_mappings': {},
        'warnings': []
    }
    
    # Extract mappings based on file structure
    if 'exact_matches' in legacy_content:
        for match in legacy_content['exact_matches']:
            source_field = match.get('source_field')
            target_field = match.get('target_field')
            if source_field and target_field:
                compatibility['field_mappings'][source_field] = {
                    'target_field': target_field,
                    'source_type': match.get('source_type'),
                    'target_type': match.get('target_type'),
                    'column_id': match.get('target_column_id')
                }
    
    return compatibility


def validate_migration_readiness() -> Dict:
    """
    Validate that the system is ready for migration from legacy files.
    
    Returns:
        Dict with validation results and readiness status
    """
    validation = {
        'ready': True,
        'issues': [],
        'warnings': [],
        'master_file_status': 'unknown',
        'helper_module_status': 'unknown'
    }
    
    # Check if master mapping file exists and is valid
    try:
        mapping_stats = mapping.get_mapping_stats()
        validation['master_file_status'] = 'valid'
        validation['warnings'].append(f"Master file contains {mapping_stats['boards_count']} boards")
    except Exception as e:
        validation['ready'] = False
        validation['issues'].append(f"Master mapping file issue: {e}")
        validation['master_file_status'] = 'invalid'
    
    # Check if helper module is working
    try:
        boards = mapping.list_monday_boards()
        validation['helper_module_status'] = 'working'
        validation['warnings'].append(f"Helper module can access {len(boards)} boards")
    except Exception as e:
        validation['ready'] = False
        validation['issues'].append(f"Helper module issue: {e}")
        validation['helper_module_status'] = 'broken'
    
    # Check for potential conflicts in existing files
    docs_mapping_path = Path(__file__).parent.parent / "docs" / "mapping"
    if docs_mapping_path.exists():
        yaml_files = list(docs_mapping_path.glob("*.yaml"))
        json_files = list(docs_mapping_path.glob("*.json"))
        total_legacy = len(yaml_files) + len(json_files)
        
        if total_legacy > 0:
            validation['warnings'].append(f"Found {total_legacy} legacy mapping files")
        else:
            validation['warnings'].append("No legacy mapping files found")
    
    return validation


def generate_migration_script(target_script_path: str, board_name: str) -> str:
    """
    Generate a migration script to update an existing Python script
    to use the new mapping system.
    
    Args:
        target_script_path: Path to script to migrate
        board_name: Name of the board configuration to use
        
    Returns:
        Suggested code changes as a string
    """
    if not os.path.exists(target_script_path):
        raise MigrationError(f"Target script not found: {target_script_path}")
    
    try:
        board_config = mapping.get_board_config(board_name)
    except Exception as e:
        raise MigrationError(f"Cannot get board config for '{board_name}': {e}")
    
    # Read existing script
    with open(target_script_path, 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    migration_suggestions = [
        "# MIGRATION SUGGESTIONS FOR MAPPING SYSTEM",
        "# Add this import at the top of your script:",
        "import mapping_helper as mapping",
        "",
        "# Replace hardcoded values with mapping calls:",
        "",
        f"# Instead of hardcoded board ID:",
        f"# BOARD_ID = 12345",
        f"# Use:",
        f"board_config = mapping.get_board_config('{board_name}')",
        f"BOARD_ID = board_config['board_id']",
        f"TABLE_NAME = board_config['table_name']",
        f"DATABASE = board_config['database']",
        "",
        f"# For field type conversions:",
        f"# Instead of hardcoded type mapping:",
        f"# if column_type == 'text': sql_type = 'NVARCHAR(MAX)'",
        f"# Use:",
        f"sql_type = mapping.get_sql_type(column_type)",
        "",
        f"# For generating DDL:",
        f"columns = mapping.get_board_columns('{board_name}')",
        f"ddl = mapping.generate_create_table_ddl(TABLE_NAME, columns, DATABASE)",
        "",
        "# This ensures your script stays synchronized with schema changes"
    ]
    
    return "\n".join(migration_suggestions)


def backup_legacy_files(backup_dir: str = None) -> Dict:
    """
    Create backups of all legacy mapping files before migration.
    
    Args:
        backup_dir: Optional backup directory path
        
    Returns:
        Dict with backup results
    """
    if backup_dir is None:
        backup_dir = Path(__file__).parent.parent / "docs" / "mapping" / "backup"
    
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    docs_mapping_path = Path(__file__).parent.parent / "docs" / "mapping"
    
    backup_results = {
        'backup_dir': str(backup_path),
        'files_backed_up': [],
        'errors': []
    }
    
    if not docs_mapping_path.exists():
        backup_results['errors'].append("Source mapping directory not found")
        return backup_results
    
    # Backup YAML files
    for file_path in docs_mapping_path.glob("*.yaml"):
        try:
            backup_file = backup_path / file_path.name
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(content)
            backup_results['files_backed_up'].append(file_path.name)
        except Exception as e:
            backup_results['errors'].append(f"Failed to backup {file_path.name}: {e}")
    
    # Backup JSON files  
    for file_path in docs_mapping_path.glob("*.json"):
        try:
            backup_file = backup_path / file_path.name
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(content)
            backup_results['files_backed_up'].append(file_path.name)
        except Exception as e:
            backup_results['errors'].append(f"Failed to backup {file_path.name}: {e}")
    
    return backup_results


def compare_mappings(legacy_file: str, board_name: str) -> Dict:
    """
    Compare legacy mapping file with new master mapping system.
    
    Args:
        legacy_file: Path to legacy mapping file
        board_name: Board name in new system to compare against
        
    Returns:
        Dict with comparison results
    """
    comparison = {
        'legacy_file': legacy_file,
        'board_name': board_name,
        'matches': [],
        'differences': [],
        'missing_in_new': [],
        'missing_in_legacy': [],
        'summary': {}
    }
    
    # Load legacy mappings
    try:
        with open(legacy_file, 'r', encoding='utf-8') as f:
            if legacy_file.endswith('.json'):
                legacy_content = json.load(f)
            else:
                legacy_content = yaml.safe_load(f)
    except Exception as e:
        comparison['differences'].append(f"Cannot load legacy file: {e}")
        return comparison
    
    # Load new mappings
    try:
        board_config = mapping.get_board_config(board_name)
        new_columns = mapping.get_board_columns(board_name)
    except Exception as e:
        comparison['differences'].append(f"Cannot load new mappings: {e}")
        return comparison
    
    # Extract legacy field mappings
    legacy_fields = {}
    if 'exact_matches' in legacy_content:
        for match in legacy_content['exact_matches']:
            source_field = match.get('source_field')
            if source_field:
                legacy_fields[source_field] = match
    
    # Extract new field mappings
    new_fields = {}
    for col in new_columns:
        field_name = col.get('name')
        if field_name:
            new_fields[field_name] = col
    
    # Compare fields
    for field_name, legacy_info in legacy_fields.items():
        if field_name in new_fields:
            new_info = new_fields[field_name]
            
            # Check for exact match
            legacy_type = legacy_info.get('target_type')
            new_type = new_info.get('monday_type')
            
            if legacy_type == new_type:
                comparison['matches'].append({
                    'field': field_name,
                    'type': legacy_type
                })
            else:
                comparison['differences'].append({
                    'field': field_name,
                    'legacy_type': legacy_type,
                    'new_type': new_type
                })
        else:
            comparison['missing_in_new'].append(field_name)
    
    # Find fields in new but not in legacy
    for field_name in new_fields:
        if field_name not in legacy_fields:
            comparison['missing_in_legacy'].append(field_name)
    
    # Generate summary
    comparison['summary'] = {
        'total_legacy_fields': len(legacy_fields),
        'total_new_fields': len(new_fields),
        'exact_matches': len(comparison['matches']),
        'differences': len(comparison['differences']),
        'missing_in_new': len(comparison['missing_in_new']),
        'missing_in_legacy': len(comparison['missing_in_legacy'])
    }
    
    return comparison


# Export main functions
__all__ = [
    'analyze_existing_mappings',
    'create_compatibility_layer', 
    'validate_migration_readiness',
    'generate_migration_script',
    'backup_legacy_files',
    'compare_mappings',
    'MigrationError'
]
