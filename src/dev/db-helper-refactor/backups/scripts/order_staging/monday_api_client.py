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
