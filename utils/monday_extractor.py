"""
Monday.com Type-Driven Data Extraction and Coercion Utility

This module implements a maintainable, type-driven approach to Monday.com data extraction
that eliminates keyword-based guessing and supports dynamic column naming via item_terminology.

Key Features:
- Type-driven extraction using centralized mapping rules
- Dynamic item name column handling via item_terminology
- Robust data coercion with fallback handling
- Support for all Monday.com column types
- Integration with existing YAML mapping configuration

Author: Data Orchestration Team
Created: 2024-06-24
"""

import sys
from pathlib import Path
import json
import yaml
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
import requests
import logging

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

logger = logger_helper.get_logger(__name__)

# Monday.com Type-to-Field Extraction Rules
# This lookup table maps monday_type to the correct JSON field to extract
EXTRACTION_RULES = {
    # Text-based types - use 'text' field
    "text": "text",
    "long_text": "text", 
    "email": "text",
    "phone": "text",
    "link": "text",
    
    # Numeric types - use 'number' field
    "numbers": "number",
    "rating": "number",
    
    # Date/Time types - use 'text' field (formatted dates)
    "date": "text",
    "datetime": "text",
    "timeline": "text",
    
    # Choice types - use specific fields
    "status": "label",  # Use 'label' for status columns
    "dropdown": "text",
    "checkbox": "text",
    "color_picker": "text",
    
    # Relationship types - use 'display_value' (usually contains processed text)
    "people": "text",
    "dependency": "display_value",
    "board_relation": "display_value", 
    "mirror": "display_value",
    "formula": "display_value",
    
    # File and special types
    "file": "text",
    "tags": "text",
    
    # System types
    "item_id": "item_id",  # Special handling
    "creation_log": "text",
    "last_updated": "text"
}

# Data Type Coercion Rules
# Maps monday_type to pandas/SQL data types
COERCION_RULES = {
    # Numeric coercion
    "numbers": "numeric",
    "rating": "numeric", 
    
    # Date coercion  
    "date": "date",
    "datetime": "datetime",
    "timeline": "date",
    "creation_log": "datetime",
    "last_updated": "datetime",
    
    # Everything else stays as text
    "text": "text",
    "long_text": "text",
    "email": "text", 
    "phone": "text",
    "link": "text",
    "status": "text",
    "dropdown": "text",
    "checkbox": "text",
    "color_picker": "text",
    "people": "text",
    "dependency": "text",
    "board_relation": "text",
    "mirror": "text", 
    "formula": "text",
    "file": "text",
    "tags": "text",
    "item_id": "numeric"
}

class MondayExtractor:
    """
    Type-driven Monday.com data extraction and coercion utility
    """
    
    def __init__(self, config_path: str = "utils/config.yaml"):
        """
        Initialize the Monday.com extractor
        
        Args:
            config_path: Path to configuration file
        """
        self.config = db.load_config()
        
        # Fix: Access nested Monday configuration
        monday_config = self.config.get('monday', {})
        self.api_token = monday_config.get('api_key')
        self.api_url = monday_config.get('api_url', "https://api.monday.com/v2")
        self.rate_limit_delay = monday_config.get('rate_limit_delay', 0.1)
        
        if not self.api_token:
            raise ValueError("Monday.com API token not found in configuration")
    
    def fetch_board_schema(self, board_id: int) -> Dict[str, Any]:
        """
        Fetch complete board schema including item_terminology
        
        Args:
            board_id: Monday.com board ID
            
        Returns:
            Dictionary with board schema including item_terminology
        """
        logger.info(f"Fetching schema for board {board_id}")
        
        query = f'''
        query GetBoardSchema {{
          boards(ids: {board_id}) {{
            id
            name
            item_terminology
            columns {{
              id
              title
              type
              settings_str
            }}
            items(limit: 1) {{
              id
              name
              column_values {{
                id
                text
                value
              }}
            }}
          }}
        }}
        '''
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_token
        }
        
        response = requests.post(
            self.api_url,
            json={'query': query},
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Monday.com API error: {response.status_code} - {response.text}")
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        boards = data.get('data', {}).get('boards', [])
        if not boards:
            raise Exception(f"Board {board_id} not found")
        
        board_schema = boards[0]
        logger.info(f"Found board: '{board_schema['name']}' with item_terminology: '{board_schema.get('item_terminology', 'items')}'")
        
        return board_schema
    
    def build_column_metadata(self, schema: Dict[str, Any], yaml_mapping: Dict[str, Any]) -> Tuple[Dict[str, Dict], str]:
        """
        Build column metadata combining Monday.com schema with YAML mapping
        
        Args:
            schema: Board schema from Monday.com
            yaml_mapping: YAML mapping configuration
            
        Returns:
            Tuple of (column_metadata_dict, item_column_name)
        """
        logger.info("Building column metadata from schema and YAML mapping")
        
        # Get item terminology to determine dynamic column name
        item_terminology = schema.get('item_terminology', 'Item')
        # Capitalize first letter to match common naming conventions
        item_column_name = item_terminology.capitalize()
        
        logger.info(f"Using item column name: '{item_column_name}' (from item_terminology: '{item_terminology}')")
        
        # Build mapping from Monday column ID to title and type
        monday_columns = {}
        for col in schema.get('columns', []):
            monday_columns[col['id']] = {
                'title': col['title'],
                'type': col['type'],
                'settings': col.get('settings_str', '{}')
            }
        
        # Build metadata dictionary
        col_meta = {}
        
        # Add item name column (special handling)
        col_meta[item_column_name] = {
            'monday_id': 'name',
            'monday_type': 'text',
            'sql_column': item_column_name,  # Use dynamic column name
            'extraction_field': 'text',
            'coercion_type': 'text'
        }
        
        # Process YAML mapping columns
        for yaml_col in yaml_mapping.get('columns', []):
            monday_id = yaml_col.get('monday_id')
            sql_column = yaml_col.get('sql_column')
            
            if not monday_id or not sql_column:
                continue
                
            # Skip name column (already handled above)
            if monday_id == 'name':
                # Update the item column mapping to use YAML sql_column if specified
                col_meta[item_column_name]['sql_column'] = sql_column
                continue
            
            # Get Monday.com column details
            if monday_id in monday_columns:
                monday_col = monday_columns[monday_id]
                monday_type = monday_col['type']
                
                # Get extraction field from rules
                extraction_field = EXTRACTION_RULES.get(monday_type, 'text')
                
                # Get coercion type (YAML override or default)
                sql_type = yaml_col.get('sql_type', '').lower()
                if 'datetime' in sql_type or 'timestamp' in sql_type:
                    coercion_type = 'datetime'
                elif 'date' in sql_type:
                    coercion_type = 'date'
                elif 'int' in sql_type or 'numeric' in sql_type or 'decimal' in sql_type:
                    coercion_type = 'numeric'
                else:
                    coercion_type = COERCION_RULES.get(monday_type, 'text')
                
                col_meta[monday_col['title']] = {
                    'monday_id': monday_id,
                    'monday_type': monday_type,
                    'sql_column': sql_column,
                    'extraction_field': extraction_field,
                    'coercion_type': coercion_type
                }
        
        logger.info(f"Built metadata for {len(col_meta)} columns")
        return col_meta, item_column_name
    
    def extract_column_value(self, column_value: Dict[str, Any], extraction_field: str) -> Any:
        """
        Extract value from Monday.com column_value using type-driven field selection
        
        Args:
            column_value: Monday.com column value object
            extraction_field: Field to extract ('text', 'number', 'label', etc.)
            
        Returns:
            Extracted value or None
        """
        if not column_value:
            return None
            
        # Handle special case for item_id
        if extraction_field == 'item_id':
            return column_value.get('id')
            
        # Extract using specified field with fallbacks
        value = column_value.get(extraction_field)
        
        # Fallback to 'text' if primary field is empty
        if value is None or (isinstance(value, str) and value.strip() == ''):
            value = column_value.get('text')
            
        # Final fallback to 'value' (raw JSON)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            raw_value = column_value.get('value')
            if raw_value:
                try:
                    # Try to parse JSON and extract useful data
                    if isinstance(raw_value, str):
                        parsed = json.loads(raw_value)
                        # Look for common value fields
                        for key in ['label', 'text', 'name', 'title']:
                            if key in parsed and parsed[key]:
                                return parsed[key]
                    return raw_value
                except (json.JSONDecodeError, TypeError):
                    return raw_value
        
        return value
    
    def coerce_dataframe_types(self, df: pd.DataFrame, col_meta: Dict[str, Dict]) -> pd.DataFrame:
        """
        Apply type coercion to DataFrame columns based on metadata
        
        Args:
            df: DataFrame to coerce
            col_meta: Column metadata with coercion rules
            
        Returns:
            DataFrame with coerced types
        """
        logger.info("Applying type coercion to DataFrame")
        
        df_coerced = df.copy()
        
        for col_name, meta in col_meta.items():
            if col_name not in df_coerced.columns:
                continue
                
            coercion_type = meta.get('coercion_type', 'text')
            
            try:
                if coercion_type == 'numeric':
                    df_coerced[col_name] = pd.to_numeric(df_coerced[col_name], errors='coerce')
                elif coercion_type == 'date':
                    df_coerced[col_name] = pd.to_datetime(df_coerced[col_name], errors='coerce').dt.date
                elif coercion_type == 'datetime':
                    df_coerced[col_name] = pd.to_datetime(df_coerced[col_name], errors='coerce')
                else:
                    # Keep as text/string
                    df_coerced[col_name] = df_coerced[col_name].astype(str)
                    
            except Exception as e:
                logger.warning(f"Failed to coerce column '{col_name}' to {coercion_type}: {e}")
                # Keep original data type on coercion failure
        
        logger.info("Type coercion completed")
        return df_coerced
    
    def process_items_with_metadata(self, items: List[Dict], col_meta: Dict[str, Dict], item_column_name: str) -> pd.DataFrame:
        """
        Process Monday.com items using column metadata for extraction and coercion
        
        Args:
            items: List of Monday.com items
            col_meta: Column metadata
            item_column_name: Name of the item/name column
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing {len(items)} items with metadata-driven extraction")
        
        data_rows = []
        
        for item in items:
            row = {}
            
            # Handle item name (special case)
            if item_column_name in col_meta:
                row[item_column_name] = item.get('name', '')
            
            # Process all column values
            for col_value in item.get('column_values', []):
                col_title = col_value.get('column', {}).get('title', '')
                
                if col_title in col_meta:
                    meta = col_meta[col_title]
                    extraction_field = meta['extraction_field']
                    value = self.extract_column_value(col_value, extraction_field)
                    row[col_title] = value
            
            data_rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Apply type coercion
        df_coerced = self.coerce_dataframe_types(df, col_meta)
        
        logger.info(f"Created DataFrame with {len(df_coerced)} rows and {len(df_coerced.columns)} columns")
        return df_coerced

def get_yaml_board_mapping(board_key: str) -> Dict[str, Any]:
    """
    Load YAML mapping for specified board
    
    Args:
        board_key: Board key in YAML mapping (e.g., 'customer_master_schedule')
        
    Returns:
        Board mapping configuration
    """
    logger.info(f"Loading YAML mapping for board: {board_key}")
    
    # Load data mapping YAML
    mapping_path = repo_root / "utils" / "data_mapping.yaml"
    
    with open(mapping_path, 'r') as f:
        data_mapping = yaml.safe_load(f)
    
    board_mapping = data_mapping.get('boards', {}).get(board_key)
    
    if not board_mapping:
        raise ValueError(f"Board mapping '{board_key}' not found in data_mapping.yaml")
    
    logger.info(f"Loaded mapping for board: {board_mapping.get('board_name', 'Unknown')}")
    return board_mapping

# Factory function for easy usage
def create_monday_extractor() -> MondayExtractor:
    """Factory function to create MondayExtractor instance"""
    return MondayExtractor()