"""
Monday.com API Integration Module

This module encapsulates all Monday.com API operations for the Customer Master Schedule workflow.
It provides clean, reusable functions for creating items, managing groups, and handling API responses.

Key Functions:
- create_monday_item: Create an item on Monday.com board
- get_board_info: Retrieve board information and structure
- validate_api_response: Standardized error handling
- format_mutation_query: Safe query formatting

Dependencies:
- requests, json, os, logging
"""

import requests
import json
import os
import logging
import warnings
from typing import Dict, Any, Optional, List
from datetime import datetime

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# Monday.com API configuration
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

# Get API key from environment
def get_monday_api_key() -> str:
    """Get Monday.com API key from environment variables"""
    api_key = os.getenv('MONDAY_API_KEY')
    if not api_key:
        # Fallback to hardcoded key (should be moved to env)
        api_key = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
        logging.warning("Using hardcoded API key. Consider setting MONDAY_API_KEY environment variable.")
    return api_key

# API Headers
def get_api_headers() -> Dict[str, str]:
    """Get Monday.com API headers"""
    return {
        "Content-Type": "application/json",
        "API-Version": API_VERSION,
        "Authorization": f"Bearer {get_monday_api_key()}"
    }

def validate_api_response(response: requests.Response, operation: str = "API call") -> Dict[str, Any]:
    """
    Validate Monday.com API response and handle errors
    
    Args:
        response: requests Response object
        operation: Description of the operation for error messages
        
    Returns:
        Dict containing the response data
        
    Raises:
        Exception: If API call failed or returned errors
    """
    if response.status_code != 200:
        error_msg = f"Monday.com API {operation} failed: {response.status_code} - {response.text}"
        logging.error(error_msg)
        raise Exception(error_msg)
    
    try:
        result = response.json()
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON response from {operation}: {e}"
        logging.error(error_msg)
        raise Exception(error_msg)
    
    # Check for GraphQL errors
    if 'errors' in result:
        error_msg = f"Monday.com API {operation} returned errors: {result['errors']}"
        logging.error(error_msg)
        raise Exception(error_msg)
    
    if 'data' not in result:
        error_msg = f"Monday.com API {operation} returned no data: {result}"
        logging.error(error_msg)
        raise Exception(error_msg)
    
    return result

def format_mutation_query(query: str) -> str:
    """
    Format GraphQL mutation query for safe transmission
    
    Args:
        query: Raw GraphQL query string
        
    Returns:
        Formatted query string with proper escaping
    """
    # Remove extra whitespace and line breaks
    formatted = ' '.join(query.split())
    
    # Basic validation
    if not query.strip().startswith(('mutation', 'query')):
        raise ValueError("Query must start with 'mutation' or 'query'")
    
    return formatted

def get_board_info(board_id: str) -> Dict[str, Any]:
    """
    Get board information including groups and columns
    
    Args:
        board_id: Monday.com board ID
        
    Returns:
        Dict containing board information
    """
    query = f'''
    query {{
        boards(ids: [{board_id}]) {{
            id
            name
            description
            groups {{
                id
                title
                color
            }}
            columns {{
                id
                title
                type
                settings_str
            }}
        }}
    }}
    '''
    
    data = {'query': format_mutation_query(query)}
    
    try:
        response = requests.post(API_URL, headers=get_api_headers(), json=data, verify=False)
        result = validate_api_response(response, f"get board info for board {board_id}")
        
        if result['data']['boards']:
            board_info = result['data']['boards'][0]
            logging.info(f"✅ Retrieved board info for {board_info['name']} (ID: {board_id})")
            return board_info
        else:
            raise Exception(f"Board {board_id} not found")
            
    except Exception as e:
        logging.error(f"❌ Failed to get board info for {board_id}: {e}")
        raise

def create_monday_item(
    board_id: str, 
    group_id: str, 
    item_name: str, 
    column_values: Dict[str, Any],
    create_labels_if_missing: bool = True
) -> str:
    """
    Create an item on Monday.com board
    
    Args:
        board_id: Monday.com board ID
        group_id: Group ID within the board
        item_name: Name for the new item
        column_values: Dictionary of column values
        create_labels_if_missing: Whether to create labels if they don't exist
        
    Returns:
        Created item ID
        
    Raises:
        Exception: If item creation fails
    """
    # Escape quotes in item name
    escaped_item_name = item_name.replace('"', '\\"')
    
    # Convert column values to JSON string and escape for GraphQL
    column_values_json = json.dumps(column_values)
    escaped_column_values = column_values_json.replace('"', '\\"')
    
    mutation = f'''
    mutation {{
        create_item(
            board_id: {board_id},
            group_id: "{group_id}",
            item_name: "{escaped_item_name}",
            column_values: "{escaped_column_values}",
            create_labels_if_missing: {str(create_labels_if_missing).lower()}
        ) {{
            id
            name
            board {{
                id
            }}
            group {{
                id
                title
            }}
        }}
    }}
    '''
    
    data = {'query': format_mutation_query(mutation)}
    
    try:
        logging.info(f"🔄 Creating Monday.com item: {item_name} in group {group_id}")
        
        response = requests.post(API_URL, headers=get_api_headers(), json=data, verify=False)
        result = validate_api_response(response, f"create item '{item_name}'")
        
        if 'create_item' in result['data'] and result['data']['create_item']:
            item_id = result['data']['create_item']['id']
            group_title = result['data']['create_item']['group']['title']
            
            logging.info(f"✅ Created Monday.com item: {item_name} (ID: {item_id}) in group '{group_title}'")
            return item_id
        else:
            raise Exception(f"Item creation returned no data: {result}")
            
    except Exception as e:
        logging.error(f"❌ Failed to create Monday.com item '{item_name}': {e}")
        raise

def update_item_column_values(
    board_id: str,
    item_id: str, 
    column_values: Dict[str, Any]
) -> bool:
    """
    Update column values for an existing Monday.com item
    
    Args:
        board_id: Monday.com board ID
        item_id: Item ID to update
        column_values: Dictionary of column values to update
        
    Returns:
        True if successful
        
    Raises:
        Exception: If update fails
    """
    # Convert column values to JSON string and escape for GraphQL
    column_values_json = json.dumps(column_values)
    escaped_column_values = column_values_json.replace('"', '\\"')
    
    mutation = f'''
    mutation {{
        change_multiple_column_values(
            board_id: {board_id},
            item_id: {item_id},
            column_values: "{escaped_column_values}"
        ) {{
            id
            name
        }}
    }}
    '''
    
    data = {'query': format_mutation_query(mutation)}
    
    try:
        logging.info(f"🔄 Updating Monday.com item {item_id} column values")
        
        response = requests.post(API_URL, headers=get_api_headers(), json=data, verify=False)
        result = validate_api_response(response, f"update item {item_id} columns")
        
        if 'change_multiple_column_values' in result['data']:
            logging.info(f"✅ Updated Monday.com item {item_id} column values")
            return True
        else:
            raise Exception(f"Column update returned no data: {result}")
            
    except Exception as e:
        logging.error(f"❌ Failed to update Monday.com item {item_id}: {e}")
        raise

def get_item_details(item_id: str) -> Dict[str, Any]:
    """
    Get details for a specific Monday.com item
    
    Args:
        item_id: Monday.com item ID
        
    Returns:
        Dict containing item details
    """
    query = f'''
    query {{
        items(ids: [{item_id}]) {{
            id
            name
            state
            board {{
                id
                name
            }}
            group {{
                id
                title
            }}
            column_values {{
                id
                title
                text
                value
                type
            }}
        }}
    }}
    '''
    
    data = {'query': format_mutation_query(query)}
    
    try:
        response = requests.post(API_URL, headers=get_api_headers(), json=data, verify=False)
        result = validate_api_response(response, f"get item details for {item_id}")
        
        if result['data']['items']:
            item_details = result['data']['items'][0]
            logging.info(f"✅ Retrieved details for item {item_id}: {item_details['name']}")
            return item_details
        else:
            raise Exception(f"Item {item_id} not found")
            
    except Exception as e:
        logging.error(f"❌ Failed to get item details for {item_id}: {e}")
        raise

def ensure_group_exists(board_id: str, group_name: str) -> str:
    """
    Ensure a group exists on the board, create if needed
    
    Args:
        board_id: Monday.com board ID
        group_name: Name of the group
        
    Returns:
        Group ID    """
    # First check if group exists
    try:
        board_info = get_board_info(board_id)
        
        # Look for existing group
        for group in board_info.get('groups', []):
            if group['title'] == group_name:
                logging.info(f"✅ Group '{group_name}' already exists with ID: {group['id']}")
                return group['id']
        
        # Group doesn't exist, create it
        logging.info(f"🔄 Creating new group: {group_name}")
        
        mutation = f'''
        mutation {{
            create_group(
                board_id: {board_id},
                group_name: "{group_name}"
            ) {{
                id
                title
            }}
        }}
        '''
        
        data = {'query': format_mutation_query(mutation)}
        response = requests.post(API_URL, headers=get_api_headers(), json=data, verify=False)
        result = validate_api_response(response, f"create group '{group_name}'")
        
        if 'create_group' in result['data'] and result['data']['create_group']:
            group_id = result['data']['create_group']['id']
            logging.info(f"✅ Created group '{group_name}' with ID: {group_id}")
            return group_id
        else:
            raise Exception(f"Group creation returned no data: {result}")
            
    except Exception as e:
        logging.error(f"❌ Failed to ensure group exists: {e}")
        # Return a default group ID as fallback
        return "new_group"

def batch_create_items(
    board_id: str,
    items_data: List[Dict[str, Any]],
    max_batch_size: int = 10
) -> List[str]:
    """
    Create multiple items in batches to avoid API limits
    
    Args:
        board_id: Monday.com board ID
        items_data: List of item data dictionaries with keys:
                   - group_id: Group ID
                   - item_name: Item name
                   - column_values: Column values dict
        max_batch_size: Maximum items per batch
        
    Returns:
        List of created item IDs
    """
    created_item_ids = []
    
    # Process items in batches
    for i in range(0, len(items_data), max_batch_size):
        batch = items_data[i:i + max_batch_size]
        
        logging.info(f"🔄 Processing batch {i//max_batch_size + 1} ({len(batch)} items)")
        
        for item_data in batch:
            try:
                item_id = create_monday_item(
                    board_id=board_id,
                    group_id=item_data['group_id'],
                    item_name=item_data['item_name'],
                    column_values=item_data['column_values']
                )
                created_item_ids.append(item_id)
                
            except Exception as e:
                logging.error(f"❌ Failed to create item '{item_data['item_name']}': {e}")
                # Continue with other items in batch
                continue
    
    logging.info(f"✅ Created {len(created_item_ids)} out of {len(items_data)} items")
    return created_item_ids

# Error handling utilities
class MondayAPIError(Exception):
    """Custom exception for Monday.com API errors"""
    
    def __init__(self, message: str, response_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.response_code = response_code
        self.response_data = response_data

# Logging configuration
def setup_logging():
    """Setup logging for Monday.com integration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('monday_integration.log')
        ]
    )

# Initialize logging when module is imported
setup_logging()
