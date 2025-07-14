"""
Monday.com Integration Client - Enterprise-grade API client with retry logic
Purpose: Robust Monday.com API integration following order-staging enterprise patterns
Location: dev/customer-orders/integration_monday.py
"""
import requests
import json
import time
import math
import sys
from typing import Dict, Any, Optional, Tuple, List
import logging
import urllib3
from pathlib import Path
import yaml

# Suppress SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add utils to path using repository root method
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root (utils folder not found)")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import utilities using working production pattern
import logger_helper

class MondayIntegrationClient:
    """Monday.com API client with comprehensive error handling and retry logic"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Monday.com integration client
        
        Args:
            config_path: Path to configuration file (defaults to utils/config.yaml)
        """
        self.logger = logger_helper.get_logger(__name__)
          # Load configuration
        if config_path is None:
            config_path = str(repo_root / "utils" / "config.yaml")
        
        self._load_config(config_path)
        
        # API configuration
        self.api_url = "https://api.monday.com/v2"
        self.headers = self._build_headers()
        self.verify_ssl = False  # For corporate networks
        self.timeout = 30
        
        # Retry configuration (following order-staging patterns)
        self.max_retries = 3
        self.base_delay = 2
        self.max_delay = 60
        self.exponential_base = 2
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.error(f"Configuration file not found: {config_path}")
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Extract Monday.com configuration
            self.monday_config = self.config.get('monday', {})
            if not self.monday_config:
                self.logger.warning("No 'monday' configuration found in config file")
                self.monday_config = {}
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Use default configuration
            self.config = {}
            self.monday_config = {}
    
    def _build_headers(self) -> Dict[str, str]:
        """Build Monday.com API headers"""
        api_key = self.monday_config.get('api_key', '')
        api_version = self.monday_config.get('api_version', '2025-04')
        
        if not api_key:
            self.logger.warning("No Monday.com API key found in configuration")
        
        return {
            "Content-Type": "application/json",
            "API-Version": api_version,
            "Authorization": f"Bearer {api_key}"
        }
    
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
        retryable_errors = [
            'NETWORK_ERROR',
            'TIMEOUT_ERROR',
            'RATE_LIMIT_ERROR',
            'TEMPORARY_SERVER_ERROR'
        ]
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
                        self.logger.error(f"API call failed with non-retryable error: {error_message}")
                        return False, None, f"{error_type}: {error_message}"
                    
                    # Wait before retry
                    delay = self._calculate_retry_delay(attempt)
                    self.logger.warning(f"Retryable error (attempt {attempt + 1}/{self.max_retries + 1}), waiting {delay:.2f}s: {error_message}")
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
                        self.logger.error(f"GraphQL errors: {error_message}")
                        return False, result, f"{error_type}: {error_message}"
                    
                    # Wait before retry
                    delay = self._calculate_retry_delay(attempt)
                    self.logger.warning(f"Retryable GraphQL error (attempt {attempt + 1}/{self.max_retries + 1}), waiting {delay:.2f}s: {error_message}")
                    time.sleep(delay)
                    continue
                
                # Success
                self.logger.debug(f"API call succeeded on attempt {attempt + 1}")
                return True, result, None
                
            except requests.exceptions.RequestException as e:
                error_type = self._classify_error(None, e)
                error_message = str(e)
                
                if not self._is_retryable_error(error_type) or attempt == self.max_retries:
                    self.logger.error(f"Request failed with non-retryable error: {error_message}")
                    return False, None, f"{error_type}: {error_message}"
                
                # Wait before retry
                delay = self._calculate_retry_delay(attempt)
                self.logger.warning(f"Retryable request error (attempt {attempt + 1}/{self.max_retries + 1}), waiting {delay:.2f}s: {error_message}")
                time.sleep(delay)
                continue
        
        # Should never reach here
        return False, None, "Max retries exceeded"
    
    def create_item(self, board_id: str, item_name: str, group_id: Optional[str] = None, 
                   column_values: Optional[Dict] = None) -> Tuple[bool, Any, str]:
        """
        Create a new item in Monday.com board
        
        Args:
            board_id: Monday.com board ID
            item_name: Name for the new item
            group_id: Optional group ID for the item
            column_values: Optional column values as JSON string
            
        Returns:
            Tuple of (success: bool, result: Any, error: str)
        """
        
        # Build GraphQL mutation
        mutation = """
        mutation ($boardId: ID!, $itemName: String!, $groupId: String, $columnValues: JSON) {
            create_item (
                board_id: $BoardId
                item_name: $ItemName
                group_id: $GroupId
                column_values: $ColumnValues
            ) {
                id
                name
                group {
                    id
                    title
                }
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "itemName": item_name
        }
        
        if group_id:
            variables["groupId"] = group_id
        
        if column_values:
            variables["columnValues"] = json.dumps(column_values)
        
        self.logger.info(f"Creating item: {item_name} in board {board_id}")
        return self._make_api_call(mutation, variables)
    
    def create_subitem(self, parent_item_id: str, subitem_name: str, 
                      column_values: Optional[Dict] = None) -> Tuple[bool, Any, str]:
        """
        Create a subitem under a parent item
        
        Args:
            parent_item_id: ID of the parent item
            subitem_name: Name for the subitem
            column_values: Optional column values as JSON string
            
        Returns:
            Tuple of (success: bool, result: Any, error: str)
        """
        
        mutation = """
        mutation ($parentItemId: ID!, $subitemName: String!, $columnValues: JSON) {
            create_subitem (
                parent_item_id: $parentItemId
                item_name: $subitemName
                column_values: $columnValues
                create_labels_if_missing: true
            ) {
                id
                name
                board {
                    id
                }
            }
        }
        """
        
        variables = {
            "parentItemId": parent_item_id,
            "subitemName": subitem_name
        }
        
        if column_values:
            variables["columnValues"] = json.dumps(column_values)
        
        self.logger.info(f"Creating subitem: {subitem_name} under parent {parent_item_id}")
        return self._make_api_call(mutation, variables)
    
    def create_size_subitem(self, parent_item_id: str, size_name: str, order_qty: int) -> Tuple[bool, Any, str]:
        """
        Create a size-specific subitem with proper column mappings
        
        Args:
            parent_item_id: ID of the parent Monday.com item
            size_name: Size designation (e.g., 'XS', 'M', '2XL', '32DD')
            order_qty: Quantity ordered for this size
            
        Returns:
            Tuple of (success: bool, result: Any, error: str)
        """
        
        # Validate inputs
        if not parent_item_id or not size_name:
            return False, None, "Missing required parameters: parent_item_id and size_name"
        
        if order_qty <= 0:
            return False, None, f"Order quantity must be positive, got {order_qty}"
        
        # Create subitem name
        subitem_name = f"Size {size_name}"
        
        # Build column values using extracted field mappings
        column_values = {
            "dropdown_mkrak7qp": {"labels": [str(size_name)]},      # Size dropdown
            "numeric_mkra7j8e": str(order_qty),                    # Order quantity
            "numeric_mkraepx7": 0,                                  # Received quantity (default)
            "numeric_mkrapgwv": 0                                   # Shipped quantity (default)
        }
        
        self.logger.info(f"Creating size subitem: {subitem_name} (qty: {order_qty}) under parent {parent_item_id}")
        
        return self.create_subitem(parent_item_id, subitem_name, column_values)
    
    def get_board_groups(self, board_id: str) -> Tuple[bool, List[Dict], str]:
        """
        Get all groups from a Monday.com board
        
        Args:
            board_id: Monday.com board ID
            
        Returns:
            Tuple of (success: bool, groups: List[Dict], error: str)
        """
        
        query = """
        query ($boardId: [ID!]!) {
            boards (ids: $boardId) {
                groups {
                    id
                    title
                    color
                }
            }
        }
        """
        
        variables = {"boardId": [board_id]}
        
        success, result, error = self._make_api_call(query, variables)
        
        if success and result and 'data' in result:
            boards = result['data'].get('boards', [])
            if boards:
                groups = boards[0].get('groups', [])
                return True, groups, None
        
        return False, [], error or "Failed to retrieve board groups"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Monday.com API connection
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        query = """
        query {
            me {
                id
                name
                email
            }
        }
        """
        
        success, result, error = self._make_api_call(query)
        
        if success and result and 'data' in result:
            user_data = result['data'].get('me', {})
            user_name = user_data.get('name', 'Unknown')
            return True, f"Connected successfully as {user_name}"
        
        return False, error or "Connection test failed"

    def detect_size_columns(self, df) -> List[str]:
        """
        Detect size columns in ORDERS_UNIFIED DataFrame
        Based on working implementation: columns between 'UNIT OF MEASURE' and 'TOTAL QTY'
        
        Args:
            df: pandas DataFrame with order data
            
        Returns:
            List of size column names
        """
        
        try:
            # Find marker columns
            start_col = 'UNIT OF MEASURE'
            end_col = 'TOTAL QTY'
            
            if start_col not in df.columns:
                self.logger.warning(f"Start marker '{start_col}' not found in DataFrame columns")
                return []
            
            if end_col not in df.columns:
                self.logger.warning(f"End marker '{end_col}' not found in DataFrame columns")
                return []
            
            # Get column positions
            start_idx = df.columns.get_loc(start_col)
            end_idx = df.columns.get_loc(end_col)
            
            # Extract size columns (between markers)
            size_columns = df.columns[start_idx + 1:end_idx].tolist()
            
            self.logger.info(f"Detected {len(size_columns)} size columns between '{start_col}' and '{end_col}'")
            
            return size_columns
            
        except Exception as e:
            self.logger.error(f"Failed to detect size columns: {e}")
            return []

    def melt_size_columns(self, df, size_columns: List[str]):
        """
        Melt size columns into individual subitem records
        Based on working implementation from mon_add_customer_ms_subitems.py
        
        Args:
            df: pandas DataFrame with order data
            size_columns: List of size column names to melt
            
        Returns:
            Melted DataFrame with size/quantity pairs
        """
        
        try:
            import pandas as pd
            
            # Define ID variables (columns to keep as identifiers) 
            # Use actual column names from ORDERS_UNIFIED
            id_vars = [
                'AAG ORDER NUMBER',      # Order reference
                'CUSTOMER NAME',         # Customer name
                'CUSTOMER STYLE',        # Product style 
                'CUSTOMER COLOUR DESCRIPTION',  # Product color
            ]
            
            # Verify required columns exist
            missing_cols = [col for col in id_vars if col not in df.columns]
            if missing_cols:
                self.logger.warning(f"Missing ID columns: {missing_cols}")
                # Filter to available columns
                id_vars = [col for col in id_vars if col in df.columns]
            
            if not size_columns:
                self.logger.warning("No size columns to melt")
                return pd.DataFrame()
            
            # Perform melt operation
            melted_df = df.melt(
                id_vars=id_vars,
                value_vars=size_columns,
                var_name='Size',
                value_name='Order_Qty'
            )
            
            # Filter to positive quantities only
            melted_df = melted_df[pd.to_numeric(melted_df['Order_Qty'], errors='coerce').notnull()]
            melted_df = melted_df[melted_df['Order_Qty'] > 0]
            
            self.logger.info(f"Melted {len(df)} order rows into {len(melted_df)} size-specific subitem records")
            
            return melted_df
            
        except Exception as e:
            self.logger.error(f"Failed to melt size columns: {e}")
            import pandas as pd
            return pd.DataFrame()

    def create_subitems_from_melted_data(self, melted_df) -> Tuple[int, int, List[Dict]]:
        """
        Create Monday.com subitems from melted size data
        
        Args:
            melted_df: DataFrame with melted size/quantity data
            
        Returns:
            Tuple of (success_count, error_count, error_records)
        """
        
        success_count = 0
        error_count = 0
        error_records = []
        
        if melted_df.empty:
            self.logger.warning("No melted data to process for subitem creation")
            return success_count, error_count, error_records
        
        try:
            from tqdm import tqdm
            
            # Process each size record
            with tqdm(total=len(melted_df), desc="Creating subitems") as pbar:
                for idx, row in melted_df.iterrows():
                    try:
                        parent_item_id = str(row['Item ID'])
                        size_name = str(row['Size'])
                        order_qty = int(float(row['Order_Qty']))
                        
                        # Create the subitem
                        success, result, error = self.create_size_subitem(
                            parent_item_id, size_name, order_qty
                        )
                        
                        if success:
                            success_count += 1
                            self.logger.debug(f"Created subitem: Size {size_name} (qty: {order_qty}) for item {parent_item_id}")
                        else:
                            error_count += 1
                            error_record = {
                                'parent_item_id': parent_item_id,
                                'size_name': size_name,
                                'order_qty': order_qty,
                                'error': error,
                                'row_index': idx
                            }
                            error_records.append(error_record)
                            self.logger.error(f"Failed to create subitem for Size {size_name}: {error}")
                        
                        # Rate limiting delay (Monday.com best practice)
                        time.sleep(0.1)
                        
                        pbar.update(1)
                        
                    except Exception as e:
                        error_count += 1
                        error_record = {
                            'parent_item_id': row.get('Item ID', 'Unknown'),
                            'size_name': row.get('Size', 'Unknown'),
                            'order_qty': row.get('Order_Qty', 0),
                            'error': str(e),
                            'row_index': idx
                        }
                        error_records.append(error_record)
                        self.logger.error(f"Exception processing row {idx}: {e}")
                        pbar.update(1)
        
        except ImportError:
            # Fallback without progress bar
            self.logger.info("tqdm not available, processing without progress bar")
            for idx, row in melted_df.iterrows():
                try:
                    parent_item_id = str(row['Item ID'])
                    size_name = str(row['Size'])
                    order_qty = int(float(row['Order_Qty']))
                    
                    success, result, error = self.create_size_subitem(
                        parent_item_id, size_name, order_qty
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        error_records.append({
                            'parent_item_id': parent_item_id,
                            'size_name': size_name,
                            'order_qty': order_qty,
                            'error': error,
                            'row_index': idx
                        })
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    error_count += 1
                    error_records.append({
                        'parent_item_id': row.get('Item ID', 'Unknown'),
                        'size_name': row.get('Size', 'Unknown'),
                        'order_qty': row.get('Order_Qty', 0),
                        'error': str(e),
                        'row_index': idx
                    })
        
        self.logger.info(f"Subitem creation completed: {success_count} successful, {error_count} errors")
        
        return success_count, error_count, error_records

    def process_order_subitems(self, df) -> Dict[str, Any]:
        """
        Complete end-to-end subitem processing for order data
        
        Args:
            df: pandas DataFrame with order data
            
        Returns:
            Dictionary with processing results and statistics
        """
        
        self.logger.info("Starting complete subitem processing workflow")
        
        # Step 1: Detect size columns
        size_columns = self.detect_size_columns(df)
        if not size_columns:
            return {
                'success': False,
                'error': 'No size columns detected',
                'size_columns_detected': 0,
                'subitems_created': 0,
                'errors': 0
            }
        
        # Step 2: Melt size data
        melted_df = self.melt_size_columns(df, size_columns)
        if melted_df.empty:
            return {
                'success': False,
                'error': 'No valid size data after melting',
                'size_columns_detected': len(size_columns),
                'subitems_created': 0,
                'errors': 0
            }
        
        # Step 3: Create subitems
        success_count, error_count, error_records = self.create_subitems_from_melted_data(melted_df)
        
        # Return comprehensive results
        return {
            'success': success_count > 0,
            'size_columns_detected': len(size_columns),
            'size_columns': size_columns,
            'melted_records': len(melted_df),
            'subitems_created': success_count,
            'errors': error_count,
            'error_records': error_records,
            'processing_summary': {
                'total_size_columns': len(size_columns),
                'valid_size_records': len(melted_df),
                'success_rate': success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0
            }
        }
