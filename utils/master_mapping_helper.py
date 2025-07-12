"""
Master Field Mapping Helper

This module provides programmatic access to the master field mapping JSON
to ensure consistent field names across all systems.

Usage:
    from utils.master_mapping_helper import get_field_mapping, get_monday_column_id
    
    # Get staging field name for Monday.com
    staging_field = get_field_mapping('order_quantity', 'staging_monday')  # Returns '[Order Qty]'
    
    # Get Monday.com API column ID
    column_id = get_monday_column_id('order_quantity')  # Returns 'numeric_mkra7j8e'
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class FieldMappingError(Exception):
    """Raised when field mapping operations fail"""
    pass


def load_master_mapping() -> Dict:
    """Load the master field mapping JSON"""
    mapping_file = Path(__file__).parent / "master_field_mapping.json"
    
    if not mapping_file.exists():
        raise FieldMappingError(f"Master mapping file not found: {mapping_file}")
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise FieldMappingError(f"Failed to load master mapping: {e}")


def get_field_mapping(field_key: str, target_system: str) -> Optional[str]:
    """
    Get field name for a specific system
    
    Args:
        field_key: Key from the mapping (e.g., 'order_quantity', 'size_value')
        target_system: Target system (e.g., 'staging_monday', 'monday_api_column_id')
        
    Returns:
        Field name for the target system, or None if not found
    """
    mapping = load_master_mapping()
    
    # Search in main_order_fields
    if field_key in mapping['field_mappings']['main_order_fields']:
        field_def = mapping['field_mappings']['main_order_fields'][field_key]
        return field_def.get(target_system)
    
    # Search in subitem_essential_fields
    if field_key in mapping['field_mappings']['subitem_essential_fields']:
        field_def = mapping['field_mappings']['subitem_essential_fields'][field_key]
        return field_def.get(target_system)
    
    # Search in subitem_update_fields
    if field_key in mapping['field_mappings']['subitem_update_fields']:
        field_def = mapping['field_mappings']['subitem_update_fields'][field_key]
        return field_def.get(target_system)
    
    return None


def get_monday_column_id(field_key: str) -> Optional[str]:
    """Get Monday.com API column ID for a field"""
    return get_field_mapping(field_key, 'monday_api_column_id')


def get_monday_field_name(field_key: str) -> Optional[str]:
    """Get Monday.com staging table field name"""
    return get_field_mapping(field_key, 'staging_monday')


def get_api_format(field_key: str) -> Optional[str]:
    """Get Monday.com API format string for a field"""
    return get_field_mapping(field_key, 'monday_api_format')


def get_size_columns() -> List[str]:
    """Get list of size columns from ORDERS_UNIFIED"""
    mapping = load_master_mapping()
    return mapping['field_mappings']['size_fields']['source_columns']


def get_staging_field_names() -> Dict[str, str]:
    """
    Get all staging table field names organized by category
    
    Returns:
        Dict with staging field names for easy reference
    """
    mapping = load_master_mapping()
    
    staging_fields = {
        'essential': {
            'size_processing': get_field_mapping('size_value', 'staging_processing'),
            'size_monday': get_field_mapping('size_value', 'staging_monday'),
            'order_qty_business': get_field_mapping('order_quantity', 'staging_business'),
            'order_qty_monday': get_field_mapping('order_quantity', 'staging_monday')
        },
        'audit': {
            'customer': get_field_mapping('customer', 'staging_business'),
            'order_number': get_field_mapping('order_number', 'staging_audit'),
            'style': get_field_mapping('style', 'staging_audit'),
            'color': get_field_mapping('color', 'staging_audit'),
            'po_number': get_field_mapping('po_number', 'staging_audit')
        },
        'update_fields': {}
    }
    
    # Add all update fields
    for field_key in mapping['field_mappings']['subitem_update_fields']:
        staging_fields['update_fields'][field_key] = get_field_mapping(field_key, 'staging_monday')
    
    return staging_fields


def get_api_payload_template(operation: str) -> Dict:
    """
    Get API payload template for create or update operations
    
    Args:
        operation: 'create_subitem' or 'update_subitem'
        
    Returns:
        Template dictionary for the operation
    """
    mapping = load_master_mapping()
    templates = mapping.get('api_payload_templates', {})
    
    if operation not in templates:
        raise FieldMappingError(f"Unknown operation: {operation}")
    
    return templates[operation]


def build_column_values_json(field_data: Dict[str, Any], operation: str = 'create_subitem') -> str:
    """
    Build Monday.com column_values JSON string
    
    Args:
        field_data: Dict with field values (using our internal field names)
        operation: 'create_subitem' or 'update_subitem'
        
    Returns:
        JSON string for Monday.com API column_values parameter
    """
    mapping = load_master_mapping()
    column_values = {}
    
    if operation == 'create_subitem':
        # Size dropdown
        if 'stg_size_label' in field_data:
            size_format = get_api_format('size_value')
            column_id = get_monday_column_id('size_value')
            value = size_format.replace('{value}', field_data['stg_size_label'])
            column_values[column_id] = value
        
        # Order quantity
        if 'ORDER_QTY' in field_data:
            qty_format = get_api_format('order_quantity')
            column_id = get_monday_column_id('order_quantity')
            value = qty_format.replace('{value}', str(field_data['ORDER_QTY']))
            column_values[column_id] = value
    
    elif operation == 'update_subitem':
        # Handle update fields conditionally
        update_fields = mapping['field_mappings']['subitem_update_fields']
        for field_key, field_def in update_fields.items():
            staging_field = field_def['staging_monday']
            if staging_field in field_data and field_data[staging_field] is not None:
                column_id = field_def['monday_api_column_id']
                format_str = field_def['monday_api_format']
                value = format_str.replace('{value}', str(field_data[staging_field]))
                column_values[column_id] = value
    
    return json.dumps(column_values).replace('"', '\\"')


def validate_required_fields(field_data: Dict[str, Any], operation: str) -> List[str]:
    """
    Validate that all required fields are present for an operation
    
    Args:
        field_data: Field data to validate
        operation: 'create_subitem' or 'update_subitem'
        
    Returns:
        List of missing field names (empty if all required fields present)
    """
    mapping = load_master_mapping()
    validation_rules = mapping.get('validation_rules', {})
    
    if operation == 'create_subitem':
        required_keys = ['stg_monday_parent_item_id', 'Size', 'ORDER_QTY']
    elif operation == 'update_subitem':
        required_keys = ['stg_monday_subitem_id', 'stg_monday_subitem_board_id']
    else:
        raise FieldMappingError(f"Unknown operation: {operation}")
    
    missing = []
    for key in required_keys:
        if key not in field_data or field_data[key] is None:
            missing.append(key)
    
    return missing


# Export main functions
__all__ = [
    'load_master_mapping',
    'get_field_mapping',
    'get_monday_column_id',
    'get_monday_field_name',
    'get_api_format',
    'get_size_columns',
    'get_staging_field_names',
    'get_api_payload_template',
    'build_column_values_json',
    'validate_required_fields',
    'FieldMappingError'
]
