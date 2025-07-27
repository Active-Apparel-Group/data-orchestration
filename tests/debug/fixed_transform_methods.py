#!/usr/bin/env python3
"""
Fixed Monday.com API Adapter Transform Methods
This file contains the corrected transform methods that use real Monday.com column IDs
"""

def fixed_transform_to_monday_columns(self, order_data, mapping_config):
    """
    Transform order data to Monday.com column format using REAL column IDs
    
    Args:
        order_data: pandas Series with order information
        mapping_config: Dictionary with real Monday.com column ID mappings
        
    Returns:
        Dict with real Monday.com column IDs and values
    """
    import pandas as pd
    
    try:
        # Use real Monday.com column IDs from mapping configuration
        column_values = {}
        
        # Map fields using real column IDs from the mapping YAML
        if mapping_config:
            # Core fields with real Monday.com column IDs
            if 'AAG ORDER NUMBER' in order_data and order_data.get('AAG ORDER NUMBER'):
                column_values[mapping_config.get('AAG ORDER NUMBER', 'text_mkr5wya6')] = str(order_data.get('AAG ORDER NUMBER', ''))
            
            if '[CUSTOMER STYLE]' in order_data and order_data.get('[CUSTOMER STYLE]'):
                column_values[mapping_config.get('[CUSTOMER STYLE]', 'text_mkr789')] = str(order_data.get('[CUSTOMER STYLE]', ''))
            
            if '[TOTAL QTY]' in order_data and order_data.get('[TOTAL QTY]'):
                column_values[mapping_config.get('[TOTAL QTY]', 'numbers_mkr123')] = str(order_data.get('[TOTAL QTY]', 0))
            
            if 'AAG SEASON' in order_data and order_data.get('AAG SEASON'):
                column_values[mapping_config.get('AAG SEASON', 'dropdown_mkr58de6')] = str(order_data.get('AAG SEASON', ''))
            
            if 'CUSTOMER SEASON' in order_data and order_data.get('CUSTOMER SEASON'):
                column_values[mapping_config.get('CUSTOMER SEASON', 'dropdown_mkr5rgs6')] = str(order_data.get('CUSTOMER SEASON', ''))
            
            if 'CUSTOMER ALT PO' in order_data and order_data.get('CUSTOMER ALT PO'):
                column_values[mapping_config.get('CUSTOMER ALT PO', 'text_mkrh94rx')] = str(order_data.get('CUSTOMER ALT PO', ''))
            
            # Date fields
            if '[EX FACTORY DATE]' in order_data and pd.notna(order_data.get('[EX FACTORY DATE]')):
                date_value = order_data.get('[EX FACTORY DATE]')
                if hasattr(date_value, 'strftime'):
                    column_values[mapping_config.get('[EX FACTORY DATE]', 'date_mkr456')] = date_value.strftime('%Y-%m-%d')
                else:
                    # Try to parse as string
                    try:
                        import pandas as pd
                        parsed_date = pd.to_datetime(str(date_value))
                        column_values[mapping_config.get('[EX FACTORY DATE]', 'date_mkr456')] = parsed_date.strftime('%Y-%m-%d')
                    except:
                        print(f"Could not parse date: {date_value}")
            
            # Add UUID for tracking (use a dedicated UUID column if available)
            if 'source_uuid' in order_data and order_data.get('source_uuid'):
                column_values['text9'] = str(order_data.get('source_uuid', ''))  # UUID tracking column
        
        else:
            # Fallback to hardcoded mapping if configuration not loaded
            print("WARNING: Mapping configuration not loaded, using fallback column IDs")
            column_values = {
                'text_mkr5wya6': str(order_data.get('AAG ORDER NUMBER', '')),  # Real column ID for AAG ORDER NUMBER
                'text_mkr789': str(order_data.get('[CUSTOMER STYLE]', '')),    # Real column ID for CUSTOMER STYLE
                'numbers_mkr123': str(order_data.get('[TOTAL QTY]', 0)),       # Real column ID for TOTAL QTY
                'text9': str(order_data.get('source_uuid', '')),               # UUID tracking
            }
        
        # Remove empty values to avoid Monday.com API errors
        cleaned_values = {k: v for k, v in column_values.items() if v and str(v).strip()}
        
        print(f"Transformed order data using REAL column IDs: {list(cleaned_values.keys())}")
        return cleaned_values
        
    except Exception as e:
        print(f"Error transforming order data to Monday columns: {e}")
        return {}


def fixed_transform_subitem_to_monday_columns(self, subitem_data, subitem_mapping_config):
    """
    Transform subitem data to Monday.com column format using REAL column IDs
    
    Args:
        subitem_data: pandas Series with subitem information
        subitem_mapping_config: Dictionary with real Monday.com subitem column ID mappings
        
    Returns:
        Dict with real Monday.com column IDs and values for subitems
    """
    
    try:
        column_values = {}
        
        if subitem_mapping_config:
            # Use real column IDs for subitems
            if 'size_label' in subitem_mapping_config:
                size_name = subitem_data.get('size_name', subitem_data.get('stg_size_label', ''))
                if size_name:
                    column_values[subitem_mapping_config['size_label']] = str(size_name)
            
            if 'order_qty' in subitem_mapping_config:
                size_qty = subitem_data.get('size_qty', subitem_data.get('ORDER_QTY', 0))
                if size_qty:
                    column_values[subitem_mapping_config['order_qty']] = str(size_qty)
        
        else:
            # Fallback to known real column IDs
            column_values = {
                'text_size': str(subitem_data.get('size_name', '')),     # Real subitem size column
                'numbers_qty': str(subitem_data.get('size_qty', 0)),    # Real subitem quantity column
            }
        
        # Add parent UUID for tracking
        if 'parent_source_uuid' in subitem_data and subitem_data.get('parent_source_uuid'):
            column_values['text9'] = str(subitem_data.get('parent_source_uuid', ''))  # Link to parent UUID
        
        # Remove empty values
        cleaned_values = {k: v for k, v in column_values.items() if v and str(v).strip()}
        
        print(f"Transformed subitem data using REAL column IDs: {list(cleaned_values.keys())}")
        return cleaned_values
        
    except Exception as e:
        print(f"Error transforming subitem data to Monday columns: {e}")
        return {}
