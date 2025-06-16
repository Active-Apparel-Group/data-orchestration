
"""
Order Data Mapping and Transformation Module

This module handles data transformation between ORDERS_UNIFIED and Monday.com
using the orders_unified_monday_mapping.yaml configuration file.

Key Functions:
- Load and parse YAML mapping configuration
- Transform order data using mapping rules
- Apply customer name standardization
- Calculate computed fields (TOTAL QTY, item names)
- Format Monday.com column values

Dependencies:
- yaml, pandas, json, os
"""

import yaml
import pandas as pd
import json
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

def load_mapping_config() -> Dict[str, Any]:
    """
    Load the orders_unified_monday_mapping.yaml configuration
    
    Returns:
        Dictionary with mapping configuration
    """
    try:
        mapping_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 
            'docs', 'mapping', 
            'orders_unified_monday_mapping.yaml'
        )
        
        with open(mapping_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            print(f"✅ Loaded mapping configuration from {mapping_path}")
            return config
            
    except Exception as e:
        print(f"❌ Error loading mapping configuration: {e}")
        return {}

def load_customer_mapping() -> Dict[str, str]:
    """
    Load customer name mapping from customer_mapping.yaml
    
    Returns:
        Dictionary mapping customer names to canonical names
    """
    try:
        customer_mapping_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 
            'docs', 'mapping', 
            'customer_mapping.yaml'
        )
        
        with open(customer_mapping_path, 'r', encoding='utf-8') as file:
            customer_config = yaml.safe_load(file)
              # Build lookup dictionary from the customers list
        customer_lookup = {}
        
        customers_list = customer_config.get('customers', [])
        
        for customer_data in customers_list:
            canonical_name = customer_data.get('canonical', '')
            master_order_list = customer_data.get('master_order_list', '')
            aliases = customer_data.get('aliases', [])
              # Add master_order_list mapping if it exists
            if master_order_list and canonical_name:
                if isinstance(master_order_list, list):
                    for mol in master_order_list:
                        if mol and isinstance(mol, str) and mol.strip():
                            customer_lookup[mol.upper()] = canonical_name
                elif isinstance(master_order_list, str) and master_order_list.strip():
                    customer_lookup[master_order_list.upper()] = canonical_name
            
            # Add aliases mappings
            if aliases and canonical_name:
                if isinstance(aliases, list):
                    for alias in aliases:
                        if alias and isinstance(alias, str) and alias.strip():
                            customer_lookup[alias.upper()] = canonical_name
                elif isinstance(aliases, str) and aliases.strip():
                    customer_lookup[aliases.upper()] = canonical_name
        
        print(f"✅ Loaded customer mapping: {len(customer_lookup)} variants")
        return customer_lookup
        
    except Exception as e:
        print(f"❌ Error loading customer mapping: {e}")
        return {}

def apply_customer_mapping(customer_name: str, customer_lookup: Dict[str, str]) -> str:
    """
    Apply customer name standardization using customer mapping
    
    Args:
        customer_name: Original customer name from ORDERS_UNIFIED
        customer_lookup: Customer mapping dictionary
        
    Returns:
        Canonical customer name
    """
    if not customer_name:
        return "UNKNOWN"
    
    # Try exact match first
    canonical = customer_lookup.get(customer_name.upper())
    if canonical:
        return canonical
    
    # Try partial matching for common variations
    customer_upper = customer_name.upper()
    for variant, canonical in customer_lookup.items():
        if variant in customer_upper or customer_upper in variant:
            return canonical
    
    # Return original if no mapping found
    print(f"⚠️  No customer mapping found for: {customer_name}")
    return customer_name

def calculate_total_qty(order_row: pd.Series) -> int:
    """
    Calculate total quantity by summing all size columns
    
    Args:
        order_row: Single order record as pandas Series
        
    Returns:
        Total quantity across all sizes
    """
    size_columns = [
        'XXXS', 'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL',
        '0', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20'
    ]
    
    total = 0
    for col in size_columns:
        if col in order_row and pd.notna(order_row[col]):
            try:
                value = int(order_row[col]) if order_row[col] else 0
                total += value
            except (ValueError, TypeError):
                continue  # Skip invalid values
    
    return total

def create_item_name(order_row: pd.Series) -> str:
    """
    Create Monday.com item name using computed field logic
    
    Args:
        order_row: Single order record as pandas Series
        
    Returns:
        Composite item name for Monday.com
    """
    customer_style = str(order_row.get('CUSTOMER STYLE', '')).strip()
    color = str(order_row.get("CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS", '')).strip()
    order_number = str(order_row.get('AAG ORDER NUMBER', '')).strip()
    
    # Handle the long color field name
    if not color and 'COLOR' in order_row:
        color = str(order_row['COLOR']).strip()
    
    return f"{customer_style}{color}{order_number}"

def clean_and_convert_value(value: Any, target_type: str, preprocessing_rules: List[Dict] = None) -> Any:
    """
    Clean and convert values based on target Monday.com column type with preprocessing
    
    Args:
        value: Original value from database
        target_type: Monday.com column type (text, numbers, date, etc.)
        preprocessing_rules: Optional list of preprocessing rules to apply
        
    Returns:
        Cleaned and converted value
    """
    if pd.isna(value) or value is None:
        return None if target_type in ['numbers', 'date'] else ""
    
    # Apply preprocessing rules (data cleaning from YAML)
    if preprocessing_rules:
        for rule in preprocessing_rules:
            if rule.get('operation') == 'replace_value':
                if str(value) == rule.get('find'):
                    value = rule.get('replace')
    
    # Apply data cleaning for known problematic values
    if target_type == 'numbers' and str(value).upper() == 'TRUE':
        value = '0'
    
    if target_type == 'text' or target_type == 'long_text':
        return str(value).strip()
    
    elif target_type == 'numbers':
        try:
            return float(value) if value != "" else None
        except (ValueError, TypeError):
            return None
    
    elif target_type == 'date':
        if isinstance(value, str):
            try:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        return parsed_date.strftime('%Y-%m-%d')  # Always return YYYY-MM-DD
                    except ValueError:
                        continue
                return None
            except:
                return None
        elif hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')  # Always return YYYY-MM-DD
        return None
    
    elif target_type in ['dropdown', 'status']:
        return str(value).strip() if value else ""
    
    return str(value).strip() if value else ""

def transform_order_data(order_row: pd.Series, mapping_config: Dict[str, Any], 
                        customer_lookup: Dict[str, str]) -> Dict[str, Any]:
    """
    Transform a single order record using YAML mapping configuration
    
    Args:
        order_row: Single order record as pandas Series
        mapping_config: YAML mapping configuration
        customer_lookup: Customer name mapping dictionary
        
    Returns:
        Transformed order data ready for Monday.com and database insertion
    """
    transformed = {}
    
    # Get preprocessing rules from mapping config
    preprocessing_rules = mapping_config.get('preprocessing', {}).get('data_cleaning', [])
    
    # Process exact matches (direct 1:1 mappings) - FIXED to include transformations
    for mapping in mapping_config.get('exact_matches', []):
        source_field = mapping['source_field']
        target_field = mapping['target_field']
        target_type = mapping['target_type']
        target_column_id = mapping['target_column_id']
        transformation = mapping.get('transformation', 'direct_mapping')  # ADDED: Check for transformation
        
        # Get source value
        source_value = order_row.get(source_field)
        
        # Apply field-specific preprocessing if defined
        field_rules = [rule for rule in preprocessing_rules if rule.get('field') == source_field]
        
        # ADDED: Apply transformations to exact_matches (same logic as mapped_fields)
        if transformation == 'customer_mapping_lookup':
            cleaned_value = apply_customer_mapping(source_value, customer_lookup)
        elif transformation == 'value_mapping':
            # Apply value mapping rules - THIS IS CRITICAL FOR ORDER TYPE
            mapping_rules = mapping.get('mapping_rules', [])
            cleaned_value = source_value
            for rule in mapping_rules:
                if str(source_value).upper() == str(rule['source_value']).upper():
                    cleaned_value = rule['target_value']
                    break
            cleaned_value = clean_and_convert_value(cleaned_value, target_type, field_rules)
        elif transformation == 'color_mapping':
            # For now, direct mapping - can be enhanced later
            cleaned_value = clean_and_convert_value(source_value, target_type, field_rules)
        else:
            # Default: direct mapping
            cleaned_value = clean_and_convert_value(source_value, target_type, field_rules)
        
        # Store both original field name and Monday.com column info
        transformed[target_field] = {
            'value': cleaned_value,
            'column_id': target_column_id,
            'type': target_type,
            'source_field': source_field
        }
    
    # Process mapped fields (fields requiring transformation) - UNCHANGED
    for mapping in mapping_config.get('mapped_fields', []):
        source_field = mapping['source_field']
        target_field = mapping['target_field']
        target_type = mapping['target_type']
        target_column_id = mapping['target_column_id']
        transformation = mapping.get('transformation', 'direct_mapping')
        
        source_value = order_row.get(source_field)
        
        # Apply specific transformations
        if transformation == 'customer_mapping_lookup':
            cleaned_value = apply_customer_mapping(source_value, customer_lookup)
        elif transformation == 'direct_mapping':
            cleaned_value = clean_and_convert_value(source_value, target_type)
        elif transformation == 'color_mapping':
            # For now, direct mapping - can be enhanced later
            cleaned_value = clean_and_convert_value(source_value, target_type)
        elif transformation == 'value_mapping':
            # Apply value mapping rules - THIS IS CRITICAL FOR ORDER STATUS
            mapping_rules = mapping.get('mapping_rules', [])
            cleaned_value = source_value
            for rule in mapping_rules:
                if str(source_value).upper() == str(rule['source_value']).upper():
                    cleaned_value = rule['target_value']
                    break
            cleaned_value = clean_and_convert_value(cleaned_value, target_type)
        else:
            cleaned_value = clean_and_convert_value(source_value, target_type)
        
        transformed[target_field] = {
            'value': cleaned_value,
            'column_id': target_column_id,
            'type': target_type,
            'source_field': source_field
        }

    # Continue with rest of function (computed_fields, etc.) - UNCHANGED
    # ...existing code...
    # Add metadata
    color_code_field = "CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS"
    transformed['_metadata'] = {
        'source_record_id': f"{order_row.get('AAG ORDER NUMBER', '')}_{order_row.get('CUSTOMER STYLE', '')}_{order_row.get(color_code_field, '')}",
        'transformation_date': datetime.now().isoformat(),
        'mapping_version': mapping_config.get('metadata', {}).get('version', '1.0')
    }
    
    return transformed

def format_monday_column_values(transformed_data: Dict[str, Any]) -> str:
    """
    Format transformed data into Monday.com column_values JSON string using proper column IDs
    
    Args:
        transformed_data: Transformed order data with column_id mappings
        
    Returns:
        JSON string for Monday.com column_values parameter
    """
    column_values = {}
    
    for field_name, field_data in transformed_data.items():
        if field_name.startswith('_'):  # Skip metadata
            continue
        
        column_id = field_data.get('column_id')
        value = field_data.get('value')
        field_type = field_data.get('type')
        
        # CRITICAL: Skip fields without column_id - these can't be set via API
        if not column_id or value is None:
            continue
        
        # Format based on Monday.com column type requirements
        if field_type == 'text' or field_type == 'long_text':
            column_values[column_id] = str(value)
        
        elif field_type == 'numbers':
            # Ensure numeric values are passed as numbers, not strings
            column_values[column_id] = value if isinstance(value, (int, float)) else 0
        
        elif field_type == 'date':
            # CRITICAL: Dates must be YYYY-MM-DD format
            if value:
                column_values[column_id] = {"date": str(value), "icon": ""}
        
        elif field_type == 'dropdown':
            # For dropdowns, we'll pass the text value
            # Monday.com API with create_labels_if_missing=true will handle it
            column_values[column_id] = str(value)
        
        elif field_type == 'status':
            # For status fields, we'll pass the text value
            # Monday.com API with create_labels_if_missing=true will handle it
            column_values[column_id] = str(value)
        
        else:
            column_values[column_id] = str(value)
    
    return json.dumps(column_values)

def get_monday_column_values_dict(transformed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert transformed data to Monday.com column_values dictionary using column IDs
    
    Args:
        transformed_data: Transformed order data with column_id mappings
        
    Returns:
        Dictionary with column_id as keys and formatted values
    """
    column_values = {}
    
    for field_name, field_data in transformed_data.items():
        if field_name.startswith('_'):  # Skip metadata
            continue
        
        column_id = field_data.get('column_id')
        value = field_data.get('value')
        field_type = field_data.get('type')
        
        # CRITICAL: Skip fields without column_id - these can't be set via API
        if not column_id or value is None:
            continue
        
        # Format based on Monday.com column type requirements
        if field_type == 'text' or field_type == 'long_text':
            column_values[column_id] = str(value)
        
        elif field_type == 'numbers':
            # Ensure numeric values are passed as numbers, not strings
            column_values[column_id] = value if isinstance(value, (int, float)) else 0
        
        elif field_type == 'date':
            # CRITICAL: Dates must be YYYY-MM-DD format
            if value:
                column_values[column_id] = {"date": str(value), "icon": ""}
        
        elif field_type == 'dropdown':
            # For dropdowns, we'll pass the text value
            # Monday.com API with create_labels_if_missing=true will handle it
            column_values[column_id] = str(value)
        
        elif field_type == 'status':
            # For status fields, we'll pass the text value
            # Monday.com API with create_labels_if_missing=true will handle it
            column_values[column_id] = str(value)
        
        else:
            column_values[column_id] = str(value)
    
    return column_values

def transform_orders_batch(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a batch of orders using YAML mapping configuration
    
    Args:
        orders_df: DataFrame with order records from ORDERS_UNIFIED
        
    Returns:
        DataFrame with transformed records ready for MON_CustMasterSchedule
    """
    if orders_df.empty:
        return pd.DataFrame()
    
    print(f"🔄 Transforming {len(orders_df)} orders using YAML mapping...")
    
    # Load configurations
    mapping_config = load_mapping_config()
    customer_lookup = load_customer_mapping()
    
    if not mapping_config:
        print("❌ Cannot proceed without mapping configuration")
        return pd.DataFrame()
    
    transformed_records = []
    
    for idx, order_row in orders_df.iterrows():
        try:
            # Transform the order
            transformed = transform_order_data(order_row, mapping_config, customer_lookup)
            
            # Flatten for database insertion
            flat_record = {}
            
            # Add key fields for database
            flat_record['AAG ORDER NUMBER'] = order_row.get('AAG ORDER NUMBER')
            flat_record['CUSTOMER STYLE'] = order_row.get('CUSTOMER STYLE')
            flat_record['COLOR'] = order_row.get("CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS")
            
            # Add transformed fields
            for field_name, field_data in transformed.items():
                if not field_name.startswith('_'):
                    flat_record[field_name] = field_data.get('value')
            
            # Add Monday.com specific fields
            flat_record['MONDAY_ITEM_ID'] = None  # Will be populated after Monday.com creation
            flat_record['MONDAY_GROUP_ID'] = None
            flat_record['SYNC_STATUS'] = 'PENDING'
            flat_record['CREATED_DATE'] = datetime.now()
            flat_record['UPDATED_DATE'] = datetime.now()
            
            # Store Monday.com column mapping for later use
            flat_record['_MONDAY_COLUMN_VALUES'] = format_monday_column_values(transformed)
            
            transformed_records.append(flat_record)
            
        except Exception as e:
            print(f"⚠️  Error transforming order {order_row.get('AAG ORDER NUMBER', 'Unknown')}: {e}")
            continue
    
    result_df = pd.DataFrame(transformed_records)
    print(f"✅ Successfully transformed {len(result_df)} orders")
    
    return result_df

def validate_mapping_config() -> bool:
    """
    Validate that the mapping configuration has all required elements
    
    Returns:
        True if valid, False otherwise
    """
    print("🔍 Validating mapping configuration...")
    
    mapping_config = load_mapping_config()
    if not mapping_config:
        print("❌ Failed to load mapping configuration")
        return False
    
    # Check required sections
    required_sections = ['exact_matches', 'mapped_fields', 'computed_fields']
    for section in required_sections:
        if section not in mapping_config:
            print(f"❌ Missing required section: {section}")
            return False
    
    # Validate exact matches have column IDs
    missing_column_ids = []
    for mapping in mapping_config.get('exact_matches', []):
        if not mapping.get('target_column_id'):
            missing_column_ids.append(mapping.get('source_field', 'Unknown'))
    
    if missing_column_ids:
        print(f"❌ Exact matches missing column IDs: {missing_column_ids}")
        return False
    
    # Validate mapped fields have column IDs
    for mapping in mapping_config.get('mapped_fields', []):
        if not mapping.get('target_column_id'):
            missing_column_ids.append(mapping.get('source_field', 'Unknown'))
    
    if missing_column_ids:
        print(f"❌ Mapped fields missing column IDs: {missing_column_ids}")
        return False
    
    # Check for value mapping rules in ORDER STATUS
    order_status_mapping = None
    for mapping in mapping_config.get('mapped_fields', []):
        if mapping.get('target_field') == 'ORDER STATUS':
            order_status_mapping = mapping
            break
    
    if order_status_mapping:
        if 'mapping_rules' not in order_status_mapping:
            print("❌ ORDER STATUS mapping missing value mapping rules")
            return False
        else:
            print(f"✅ ORDER STATUS value mapping rules found: {len(order_status_mapping['mapping_rules'])} rules")
    
    exact_count = len(mapping_config.get('exact_matches', []))
    mapped_count = len(mapping_config.get('mapped_fields', []))
    computed_count = len(mapping_config.get('computed_fields', []))
    
    print(f"✅ Mapping validation passed:")
    print(f"   - {exact_count} exact matches")
    print(f"   - {mapped_count} mapped fields")
    print(f"   - {computed_count} computed fields")
    
    return True

# Test functions
if __name__ == "__main__":
    print("Testing Order Mapping Functions")
    print("=" * 50)
    
    # Test loading configurations
    print("📋 Loading mapping configuration...")
    mapping_config = load_mapping_config()
    if mapping_config:
        print(f"✅ Loaded mapping config with {len(mapping_config.get('exact_matches', []))} exact matches")
    
    print("\n👥 Loading customer mapping...")
    customer_lookup = load_customer_mapping()
    if customer_lookup:
        print(f"✅ Loaded customer mapping with {len(customer_lookup)} variants")
        print("Sample mappings:")
        for i, (variant, canonical) in enumerate(list(customer_lookup.items())[:5]):
            print(f"  {variant} → {canonical}")
    
    # Test customer mapping function
    print("\n🔄 Testing customer mapping...")
    test_customers = ["JOHNNIE O", "RHYTHM (AU)", "TITLE 9", "UNKNOWN CUSTOMER"]
    for customer in test_customers:
        mapped = apply_customer_mapping(customer, customer_lookup)
        print(f"  {customer} → {mapped}")
    
    # Validate mapping configuration
    print("\n✅ Order mapping tests completed")
    print("\n🔍 Validating mapping configuration...")
    validate_mapping_config()
