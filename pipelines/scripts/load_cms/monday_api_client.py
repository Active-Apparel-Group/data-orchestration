"""
Monday.com API client with retry logic and error handling
"""

import requests
import json
import time
import math
from typing import Dict, Any, Optional, Tuple
import logging
import urllib3

from .staging_config import get_config, get_monday_headers, MONDAY_CONFIG

# Suppress SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class MondayApiClient:
    """Monday.com API client with comprehensive error handling and retry logic"""
    
    def __init__(self):
        self.config = get_config()
        self.api_url = MONDAY_CONFIG['api_url']
        self.headers = get_monday_headers()
        self.verify_ssl = MONDAY_CONFIG['verify_ssl']
        self.timeout = MONDAY_CONFIG['timeout_seconds']
        
        # Retry configuration
        self.max_retries = self.config['batch']['retry_config']['max_retries']
        self.base_delay = self.config['batch']['retry_config']['base_delay_seconds']
        self.max_delay = self.config['batch']['retry_config']['max_delay_seconds']
        self.exponential_base = self.config['batch']['retry_config']['exponential_base']
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        # Add some jitter to prevent thundering herd
        jitter = delay * 0.1 * (0.5 - hash(str(time.time())) % 1000 / 1000)
        return delay + jitter
    
    def _classify_error(self, response: requests.Response, exception: Optional[Exception] = None) -> str:
        """Classify error type for appropriate handling"""
        
        if exception:
            if isinstance(exception, requests.exceptions.Timeout):
                return 'TIMEOUT_ERROR'
            elif isinstance(exception, requests.exceptions.ConnectionError):
                return 'NETWORK_ERROR'
            else:
                return 'REQUEST_ERROR'
        
        if response.status_code == 401:
            return 'AUTHENTICATION_ERROR'
        elif response.status_code == 403:
            return 'AUTHORIZATION_ERROR'
        elif response.status_code == 404:
            return 'BOARD_NOT_FOUND'
        elif response.status_code == 429:
            return 'RATE_LIMIT_ERROR'
        elif 400 <= response.status_code < 500:
            return 'VALIDATION_ERROR'
        elif 500 <= response.status_code < 600:
            return 'TEMPORARY_SERVER_ERROR'
        else:
            return 'UNKNOWN_ERROR'
    
    def _is_retryable_error(self, error_type: str) -> bool:
        """Determine if error is retryable"""
        retryable_errors = self.config['error']['retryable_errors']
        return error_type in retryable_errors
    
    def _make_api_call(self, query: str, variables: Optional[Dict] = None) -> Tuple[bool, Any, str]:
        """Make API call with comprehensive error handling"""
        
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_type = self._classify_error(response)
                    error_message = f"HTTP {response.status_code}: {response.text}"
                    
                    if not self._is_retryable_error(error_type) or attempt == self.max_retries:
                        logger.error(f"API call failed with non-retryable error: {error_message}")
                        return False, None, f"{error_type}: {error_message}"
                    
                    # Wait before retry
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Retryable error (attempt {attempt + 1}/{self.max_retries + 1}), waiting {delay:.2f}s: {error_message}")
                    time.sleep(delay)
                    continue
                
                # Parse JSON response
                result = response.json()
                
                # Check for GraphQL errors
                if 'errors' in result:
                    error_message = '; '.join([err.get('message', str(err)) for err in result['errors']])
                    
                    # Determine if GraphQL errors are retryable
                    if any('rate limit' in str(err).lower() for err in result['errors']):
                        error_type = 'RATE_LIMIT_ERROR'
                    elif any('timeout' in str(err).lower() for err in result['errors']):
                        error_type = 'TIMEOUT_ERROR'
                    else:
                        error_type = 'VALIDATION_ERROR'
                    
                    if not self._is_retryable_error(error_type) or attempt == self.max_retries:
                        logger.error(f"GraphQL errors: {error_message}")
                        return False, result, f"{error_type}: {error_message}"
                    
                    # Wait before retry
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Retryable GraphQL error (attempt {attempt + 1}/{self.max_retries + 1}), waiting {delay:.2f}s: {error_message}")
                    time.sleep(delay)
                    continue
                
                # Success
                logger.debug(f"API call succeeded on attempt {attempt + 1}")
                return True, result, None
                
            except requests.exceptions.RequestException as e:
                error_type = self._classify_error(None, e)
                error_message = str(e)
                
                if not self._is_retryable_error(error_type) or attempt == self.max_retries:
                    logger.error(f"Request failed with non-retryable error: {error_message}")
                    return False, None, f"{error_type}: {error_message}"
                
                # Wait before retry
                delay = self._calculate_retry_delay(attempt)
                logger.warning(f"Retryable request error (attempt {attempt + 1}/{self.max_retries + 1}), waiting {delay:.2f}s: {error_message}")
                time.sleep(delay)
                continue
            
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                logger.error(error_message)
                return False, None, f"UNEXPECTED_ERROR: {error_message}"
        
        # Should not reach here, but just in case
        return False, None, "MAX_RETRIES_EXCEEDED"
    
    def ensure_group_exists(self, group_name: str, board_id: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Ensure group exists on board, create if needed"""
        
        if board_id is None:
            board_id = MONDAY_CONFIG['board_id']
        
        # Get board info to check existing groups
        query = f"""
        query {{
            boards(ids: [{board_id}]) {{
                groups {{
                    id
                    title
                }}
            }}
        }}
        """
        
        success, result, error = self._make_api_call(query)
        if not success:
            return False, None, f"Failed to get board groups: {error}"
        
        if not result.get('data', {}).get('boards'):
            return False, None, f"Board {board_id} not found"
        
        groups = result['data']['boards'][0]['groups']
        
        # Check if group exists
        for group in groups:
            if group['title'] == group_name:
                logger.debug(f"Group '{group_name}' already exists with ID {group['id']}")
                return True, group['id'], None
        
        # Create new group
        sanitized_group_name = group_name.replace('"', '\\"')
        query = f"""
        mutation {{
            create_group(
                board_id: {board_id},
                group_name: "{sanitized_group_name}"
            ) {{
                id
            }}
        }}
        """
        
        success, result, error = self._make_api_call(query)
        if not success:
            return False, None, f"Failed to create group: {error}"
        
        group_id = result['data']['create_group']['id']
        logger.info(f"Created new group '{group_name}' with ID {group_id}")
        return True, group_id, None
    
    def create_item(self, item_name: str, group_id: str, column_values: Optional[Dict] = None, 
                   board_id: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Create item on Monday.com board"""
        
        if board_id is None:
            board_id = MONDAY_CONFIG['board_id']
        
        # Sanitize item name
        sanitized_name = item_name.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
        
        # Handle column values
        if column_values is None:
            column_values = {}
        
        # Convert column values to JSON and escape for GraphQL
        column_values_json = self._safe_json(column_values)
        escaped_column_values = column_values_json.replace('\\', '\\\\').replace('"', '\\"')
        
        # Build mutation
        mutation = f"""
        mutation {{
            create_item(
                board_id: {board_id},
                group_id: "{group_id}",
                item_name: "{sanitized_name}",
                column_values: "{escaped_column_values}",
                create_labels_if_missing: true
            ) {{
                id
            }}
        }}
        """
        
        success, result, error = self._make_api_call(mutation)
        if not success:
            return False, None, f"Failed to create item: {error}"
        
        item_id = result['data']['create_item']['id']
        logger.info(f"Created item '{item_name}' with ID {item_id}")
        return True, item_id, None
    
    def create_subitem(self, parent_item_id: str, subitem_name: str, 
                      column_values: Optional[Dict] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Create subitem under parent item"""
        
        # Sanitize subitem name
        sanitized_name = subitem_name.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
        
        # Handle column values
        if column_values is None:
            column_values = {}
        
        # Convert column values to JSON and escape for GraphQL
        column_values_json = self._safe_json(column_values)
        escaped_column_values = column_values_json.replace('\\', '\\\\').replace('"', '\\"')
        
        # Build mutation
        mutation = f"""
        mutation {{
            create_subitem(
                parent_item_id: {parent_item_id},
                item_name: "{sanitized_name}",
                column_values: "{escaped_column_values}",
                create_labels_if_missing: true
            ) {{
                id
                board {{ id }}
                parent_item {{ id }}
            }}
        }}
        """
        
        success, result, error = self._make_api_call(mutation)
        if not success:
            return False, None, f"Failed to create subitem: {error}"
        
        subitem_data = result['data']['create_subitem']
        subitem_result = {
            'subitem_id': subitem_data['id'],
            'subitem_board_id': subitem_data['board']['id'],
            'parent_item_id': subitem_data['parent_item']['id']
        }
        
        logger.info(f"Created subitem '{subitem_name}' with ID {subitem_result['subitem_id']}")
        return True, subitem_result, None
    
    def update_item(self, board_id: str, item_id: str, column_values: dict) -> dict:
        """
        Update existing Monday.com item with validated column values
        
        Args:
            board_id: Monday.com board ID
            item_id: Monday.com item ID  
            column_values: Dict of {column_id: value} to update
            
        Returns:
            Dict with update result and item details
        """
        mutation = """
        mutation UpdateItem($boardId: ID!, $itemId: ID!, $columnValues: JSON!) {
            change_multiple_column_values(
                board_id: $boardId,
                item_id: $itemId,
                column_values: $columnValues
            ) {
                id
                name
                updated_at
                column_values {
                    id
                    text
                    value
                }
            }
        }
        """
        variables = {
            'boardId': str(board_id),
            'itemId': str(item_id),
            'columnValues': json.dumps(column_values)
        }
        
        result = self._execute_mutation_with_retry(mutation, variables)
        self._log_update_audit(board_id, item_id, column_values, result)
        return result
    
    def update_subitem(self, item_id: str, subitem_id: str, column_values: dict) -> dict:
        """Update existing Monday.com subitem"""
        mutation = """
        mutation UpdateSubitem($itemId: ID!, $subitemId: ID!, $columnValues: JSON!) {
            change_subitem_column_values(
                item_id: $itemId,
                subitem_id: $subitemId,
                column_values: $columnValues
            ) {
                id
                name
                column_values {
                    id
                    text
                    value
                }
            }
        }
        """
        variables = {
            'itemId': str(item_id),
            'subitemId': str(subitem_id), 
            'columnValues': json.dumps(column_values)
        }
        
        return self._execute_mutation_with_retry(mutation, variables)
    
    def update_group(self, board_id: str, group_id: str, group_title: str) -> dict:
        """Update Monday.com group title"""
        mutation = """
        mutation UpdateGroup($boardId: ID!, $groupId: String!, $groupTitle: String!) {
            update_group(
                board_id: $boardId,
                group_id: $groupId,
                group_attribute: title,
                new_value: $groupTitle
            ) {
                id
                title
            }
        }
        """
        variables = {
            'boardId': str(board_id),
            'groupId': group_id,
            'groupTitle': group_title
        }
        
        return self._execute_mutation_with_retry(mutation, variables)
    
    def batch_update_items(self, updates: List[dict], batch_size: int = 10) -> List[dict]:
        """
        Execute batch updates with rate limiting and error handling
        
        Args:
            updates: List of update operations
            batch_size: Number of updates per batch
            
        Returns:
            List of results with success/error status
        """
        results = []
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_results = []
            
            for update in batch:
                try:
                    if update['operation'] == 'update_item':
                        result = self.update_item(
                            update['board_id'],
                            update['item_id'], 
                            update['column_values']
                        )
                        batch_results.append({
                            'success': True,
                            'update': update,
                            'result': result
                        })
                    elif update['operation'] == 'update_subitem':
                        result = self.update_subitem(
                            update['item_id'],
                            update['subitem_id'],
                            update['column_values']
                        )
                        batch_results.append({
                            'success': True,
                            'update': update,
                            'result': result
                        })
                        
                except Exception as e:
                    logger.error(f"Update failed: {e}")
                    batch_results.append({
                        'success': False,
                        'update': update,
                        'error': str(e)
                    })
                
                # Rate limiting between requests
                time.sleep(self.rate_limit_delay)
            
            results.extend(batch_results)
            
            # Batch-level delay
            if i + batch_size < len(updates):
                time.sleep(1.0)
        
        return results
    
    def _execute_mutation_with_retry(self, mutation: str, variables: dict, max_retries: int = 3) -> dict:
        """Execute mutation with retry logic for transient failures"""
        for attempt in range(max_retries):
            try:
                return self.client.execute(gql(mutation), variable_values=variables)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Mutation attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _log_update_audit(self, board_id: str, item_id: str, updates: dict, result: dict):
        """Log update operation for audit trail and rollback capability"""
        # Implementation for audit logging
        pass

    def _safe_json(self, column_values: Dict) -> str:
        """Drop None/empty values and return a JSON string Monday accepts"""
        cleaned = {}
        for k, v in column_values.items():
            if v is None:
                continue
            if isinstance(v, float) and math.isnan(v):
                continue
            if hasattr(v, '__iter__') and hasattr(v, 'isna') and v.isna():  # pandas NA
                continue
            if isinstance(v, str) and not v.strip():
                continue
            cleaned[k] = v
        
        return json.dumps(cleaned, ensure_ascii=False, allow_nan=False)
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test API connection and authentication"""
        query = "query { me { name } }"
        
        success, result, error = self._make_api_call(query)
        if not success:
            return False, f"Connection test failed: {error}"
        
        user_name = result.get('data', {}).get('me', {}).get('name', 'Unknown')
        logger.info(f"Connection test successful. Authenticated as: {user_name}")
        return True, None
