#!/usr/bin/env python3
"""
Monday.com API Adapter - UUID-Based Integration

Integrates the existing Monday.com API modules with our UUID-based staging workflow.
Provides clean interfaces for creating master schedule items and subitems with UUID tracking.

Features:
- UUID-based tracking of Monday.com items
- Integration with existing Monday.com API modules
- Master schedule and subitems creation
- Error handling and retry logic
"""

import os
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import requests

# Add utils and scripts to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import logger_helper
# Import from utils/ following project standards - no customer_master_schedule references
import mapping_helper

# Import real Monday.com integration from utils/ following project standards
import monday_integration

# Initialize Monday.com integration
_monday_client = monday_integration.create_monday_integration()

def create_monday_item(board_id: str, item_name: str, group_id: str = None, column_values: dict = None, **kwargs) -> dict:
    """Create Monday.com item using real API integration"""
    logger = logger_helper.get_logger(__name__)
    
    # Convert column_values dict to JSON string if needed
    column_values_json = None
    if column_values:
        import json
        column_values_json = json.dumps(column_values)
    
    success, result, error = _monday_client.create_item(
        board_id=board_id,
        item_name=item_name,
        group_id=group_id,
        column_values=column_values_json
    )
    
    if success and result and 'data' in result:
        item_data = result['data'].get('create_item', {})
        logger.info(f"Successfully created Monday.com item: {item_name}")
        return {
            'id': item_data.get('id'),
            'name': item_data.get('name'),
            'status': 'success',
            'created_at': item_data.get('created_at')
        }
    else:
        logger.error(f"Failed to create Monday.com item: {error}")
        return {
            'id': None,
            'status': 'failed',
            'error': error
        }

def update_item_column_values(item_id: str, board_id: str, column_values: dict) -> bool:
    """Update Monday.com item column values using real API integration"""
    logger = logger_helper.get_logger(__name__)
    
    # TODO: Implement update functionality in monday_integration.py
    logger.warning(f"Monday.com item update not yet implemented for item {item_id}")
    return True  # Placeholder for now

def load_mapping_config():
    """Load mapping configuration from utils/mapping_helper"""
    return mapping_helper.get_orders_field_mappings()

def load_subitem_mapping_config():
    """Load subitem mapping configuration from utils/mapping_helper"""
    return mapping_helper.get_orders_subitem_mappings()

def load_customer_mapping():
    """Load customer mapping configuration"""
    try:
        return mapping_helper.get_customer_mapping('GREYSON')  # Default for now
    except Exception as e:
        logger = logger_helper.get_logger(__name__)
        logger.warning(f"Could not load customer mapping: {e}")
        return {'customer': 'GREYSON', 'canonical_name': 'GREYSON'}  # Fallback

class MondayApiAdapter:
    """Monday.com API adapter with UUID tracking"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        
        # Initialize Monday.com client
        self.monday_client = monday_integration.create_monday_integration()
        
        # Initialize customer mapper
        try:
            from customer_mapper import CustomerMapper
            self.customer_mapper = CustomerMapper()
        except ImportError:
            # Fallback - create simple mapper if import fails
            self.customer_mapper = None
            self.logger.warning("Could not import CustomerMapper, using fallback")
        
          # Monday.com configuration
        self.board_id = "9200517329"  # Customer Master Schedule board
        self.subitems_board_id = "4449871138"  # Subitems board
        self.default_group_id = "group_mkranjfa"  # GREYSON 2026 SPRING
          # Load mapping configuration
        self.mapping_config = load_mapping_config()
        self.subitem_mapping_config = load_subitem_mapping_config()
        self.customer_mapping = load_customer_mapping()
    
    def load_graphql_template(self, template_name: str) -> str:
        """Load GraphQL template from sql/graphql/ folder"""
        template_path = repo_root / "sql" / "graphql" / "mutations" / f"{template_name}.graphql"
        if not template_path.exists():
            self.logger.error(f"GraphQL template not found: {template_path}")
            raise FileNotFoundError(f"GraphQL template not found: {template_path}")
        
        with open(template_path, 'r') as f:
            return f.read()
    
    def execute_graphql(self, query: str, variables: dict) -> dict:
        """Execute GraphQL query against Monday.com API"""
        headers = {
            "Authorization": self.monday_client.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "variables": variables
        }
        
        self.logger.info(f"Executing GraphQL mutation with variables: {list(variables.keys())}")
        
        try:
            response = requests.post(
                "https://api.monday.com/v2",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            if 'errors' in result:
                self.logger.error(f"GraphQL errors: {result['errors']}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GraphQL request failed: {e}")
            return {'errors': [{'message': str(e)}]}
    
    def create_item_graphql(self, order_data: pd.Series) -> Dict[str, Any]:
        """
        Create Monday.com item using GraphQL API
        
        Args:
            order_data: Order record with all fields
            
        Returns:
            dict: Creation result with Monday.com item_id
        """
        try:
            # Load GraphQL template
            mutation_query = self.load_graphql_template("create-master-item")
            
            # Create item name and column values
            item_name = self._create_item_name(order_data)
            column_values = self._transform_to_monday_columns(order_data)
            
            # Prepare variables for GraphQL
            variables = {
                "boardId": self.board_id,
                "itemName": item_name,
                "columnValues": json.dumps(column_values)
            }
            
            # Execute GraphQL mutation
            result = self.execute_graphql(mutation_query, variables)
            
            if 'errors' in result:
                self.logger.error(f"Failed to create item via GraphQL: {result['errors']}")
                return {
                    'id': None,
                    'status': 'failed',
                    'error': result['errors']
                }
            
            # Extract item data from GraphQL response
            item_data = result.get('data', {}).get('create_item', {})
            
            if item_data and item_data.get('id'):
                self.logger.info(f"Successfully created item via GraphQL: {item_name} (ID: {item_data['id']})")
                return {
                    'id': item_data['id'],
                    'name': item_data['name'],
                    'status': 'success',
                    'board_id': self.board_id,
                    'column_values': item_data.get('column_values', [])
                }
            else:
                self.logger.error(f"No item data returned from GraphQL")
                return {
                    'id': None,
                    'status': 'failed',
                    'error': 'No item data returned'
                }
                
        except Exception as e:
            self.logger.error(f"Exception in create_item_graphql: {e}")
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def create_subitem_graphql(self, parent_monday_id: str, subitem_data: pd.Series) -> Dict[str, Any]:
        """
        Create Monday.com subitem using GraphQL API
        
        Args:
            parent_monday_id: Monday.com ID of the parent item
            subitem_data: Series with subitem record data
            
        Returns:
            dict: Creation result with Monday.com subitem_id
        """
        try:
            # Load GraphQL template
            mutation_query = self.load_graphql_template("create-subitem")
            
            # Create subitem name
            size_name = subitem_data.get('stg_size_label', subitem_data.get('Size', 'Unknown Size'))
            subitem_name = f"Size {size_name}"
            
            # Transform subitem data to Monday.com column values using YAML mapping
            column_values = self._transform_subitem_to_monday_columns(subitem_data)
            
            # Prepare variables for GraphQL
            variables = {
                "parentItemId": parent_monday_id,
                "itemName": subitem_name,
                "columnValues": json.dumps(column_values)
            }
            
            self.logger.info(f"Creating subitem via GraphQL: {subitem_name} for parent {parent_monday_id}")
            
            # Execute GraphQL mutation
            result = self.execute_graphql(mutation_query, variables)
            
            if 'errors' in result:
                self.logger.error(f"Failed to create subitem via GraphQL: {result['errors']}")
                return {
                    'id': None,
                    'status': 'failed',
                    'error': result['errors']
                }
            
            # Extract subitem data from GraphQL response
            subitem_data_result = result.get('data', {}).get('create_subitem', {})
            
            if subitem_data_result and subitem_data_result.get('id'):
                self.logger.info(f"Successfully created subitem via GraphQL: {subitem_name} (ID: {subitem_data_result['id']})")
                return {
                    'id': subitem_data_result['id'],
                    'name': subitem_data_result['name'],
                    'status': 'success',
                    'parent_item_id': parent_monday_id,
                    'size_name': size_name,
                    'column_values': subitem_data_result.get('column_values', [])
                }
            else:
                self.logger.error(f"No subitem data returned from GraphQL")
                return {
                    'id': None,
                    'status': 'failed',
                    'error': 'No subitem data returned'
                }
                
        except Exception as e:
            self.logger.error(f"Exception in create_subitem_graphql: {e}")
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def create_master_schedule_item(self, order_data: pd.Series) -> Dict[str, Any]:
        """
        Create a master schedule item on Monday.com
        
        Args:
            order_data: Order record with UUID and all fields
            
        Returns:
            dict: Creation result with Monday.com item_id
        """
        
        try:            # Get customer and group from staging data
            customer = order_data.get('CUSTOMER', 'Unknown Customer')
            group_id = order_data.get('Group', self.default_group_id)  # Use default group if not specified
            
            # Create item name
            item_name = self._create_item_name(order_data)
            
            # Transform order data to Monday.com column format
            column_values = self._transform_to_monday_columns(order_data)
            
            self.logger.info(f"Creating Monday.com master schedule item: {item_name}")
            self.logger.info(f"   Customer: {customer}, Group: {group_id}")
            self.logger.info(f"   Source UUID: {order_data.get('source_uuid', 'N/A')}")
              # Create the Monday.com item
            monday_result = create_monday_item(
                board_id=self.board_id,
                item_name=item_name,
                group_id=group_id,
                column_values=column_values
            )
            
            if monday_result.get('status') == 'success':
                monday_item_id = monday_result.get('id')
                
                result = {
                    'success': True,
                    'monday_item_id': monday_item_id,
                    'item_name': item_name,
                    'customer': customer,
                    'group_id': group_id,
                    'source_uuid': order_data.get('source_uuid'),
                    'created_at': datetime.now(),
                    'monday_created_at': monday_result.get('created_at')
                }
                
                self.logger.info(f"SUCCESS: Created master schedule item: {monday_item_id}")
                return result
            else:
                error_msg = f"Monday.com API error: {monday_result.get('error', 'Unknown error')}"
                self.logger.error(f"ERROR: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'source_uuid': order_data.get('source_uuid'),
                    'failed_at': datetime.now()
                }
            
        except Exception as e:
            error_msg = f"Failed to create master schedule item: {str(e)}"
            self.logger.error(f"ERROR: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'source_uuid': order_data.get('source_uuid'),
                'failed_at': datetime.now()            }
    
    def create_subitems(self, parent_monday_id: str, subitems_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Create subitems for a master schedule item using GraphQL
        
        Args:
            parent_monday_id: Monday.com ID of the parent item
            subitems_data: DataFrame with subitem records
            
        Returns:
            List of creation results with board IDs captured
        """
        
        results = []
        
        try:
            self.logger.info(f"Creating {len(subitems_data)} subitems for parent {parent_monday_id}")
            
            for _, subitem in subitems_data.iterrows():
                try:
                    # Create subitem using GraphQL
                    result = self.create_subitem_graphql(parent_monday_id, subitem)
                    
                    if result.get('status') == 'success':
                        success_result = {
                            'success': True,
                            'monday_subitem_id': result.get('id'),
                            'monday_subitem_board_id': self.subitems_board_id,
                            'monday_parent_item_id': parent_monday_id,
                            'size_name': result.get('size_name', 'Unknown'),
                            'size_qty': subitem.get('ORDER_QTY', 0),
                            'parent_source_uuid': subitem.get('parent_source_uuid'),
                            'created_at': datetime.now(),
                            'monday_created_at': result.get('created_at')
                        }
                        
                        results.append(success_result)
                        self.logger.info(f"   SUCCESS: Created subitem: {result.get('name')}")
                        self.logger.info(f"      Subitem ID: {result.get('id')}")
                        self.logger.info(f"      Board ID: {self.subitems_board_id}")
                        
                    else:
                        error_result = {
                            'success': False,
                            'error': result.get('error', 'Unknown subitem creation error'),
                            'size_name': result.get('size_name', 'Unknown'),
                            'parent_source_uuid': subitem.get('parent_source_uuid'),
                            'failed_at': datetime.now()
                        }
                        results.append(error_result)
                        self.logger.error(f"   ERROR: Failed to create subitem: {result.get('error')}")
                        
                except Exception as e:
                    error_result = {
                        'success': False,
                        'error': str(e),
                        'size_name': subitem.get('size_name', 'Unknown'),
                        'parent_source_uuid': subitem.get('parent_source_uuid'),
                        'failed_at': datetime.now()
                    }
                    results.append(error_result)
                    self.logger.error(f"   ERROR: Failed to create subitem: {str(e)}")
                    
            successful = sum(1 for r in results if r['success'])
            self.logger.info(f"SUCCESS: Created {successful}/{len(results)} subitems successfully")
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to create subitems: {str(e)}")
            # Return empty results list on failure to prevent NoneType iteration errors
            return []
        
        return results
    
    def _create_item_name(self, order_data: pd.Series) -> str:
        """Create a Monday.com item name from order data"""
        
        customer = order_data.get('CUSTOMER NAME', 'Unknown Customer')
        po_number = order_data.get('AAG ORDER NUMBER', 'Unknown PO')
        style = order_data.get('CUSTOMER STYLE', '')
        
        if style:
            return f"{customer} - {po_number} - {style}"
        else:
            return f"{customer} - {po_number}"
    
    def _transform_to_monday_columns(self, order_data: pd.Series) -> Dict[str, Any]:
        """Transform order data to Monday.com column format using orders-unified-monday-mapping.yaml"""
        
        try:
            column_values = {}
            
            # Load comprehensive mapping from YAML file
            mapping_data = self._load_mapping_data()
            
            if mapping_data:
                # Process exact_matches
                exact_matches = mapping_data.get('exact_matches', [])
                self.logger.info(f"Processing {len(exact_matches)} exact match mappings")
                
                for field_mapping in exact_matches:
                    source_field = field_mapping.get('source_field')
                    target_column_id = field_mapping.get('target_column_id')
                    
                    if source_field and target_column_id and source_field in order_data:
                        value = self._extract_clean_value(order_data.get(source_field))
                        if value:
                            column_values[target_column_id] = value
                            self.logger.debug(f"Exact match: {source_field} -> {target_column_id}: {value}")
                
                # Process mapped_fields (transformations)
                mapped_fields = mapping_data.get('mapped_fields', [])
                self.logger.info(f"Processing {len(mapped_fields)} mapped field transformations")
                
                for field_mapping in mapped_fields:
                    source_field = field_mapping.get('source_field')
                    target_field = field_mapping.get('target_field')
                    target_column_id = field_mapping.get('target_column_id')
                    transformation = field_mapping.get('transformation')
                    
                    if source_field and target_column_id and source_field in order_data:
                        value = self._apply_transformation(
                            order_data.get(source_field), 
                            transformation, 
                            field_mapping
                        )
                        if value:
                            column_values[target_column_id] = value
                            self.logger.debug(f"Mapped field: {source_field} -> {target_field}: {value}")
                
                # Process computed_fields
                computed_fields = mapping_data.get('computed_fields', [])
                self.logger.info(f"Processing {len(computed_fields)} computed fields")
                
                for computed_field in computed_fields:
                    target_field = computed_field.get('target_field')
                    source_fields = computed_field.get('source_fields', [])
                    transformation = computed_field.get('transformation')
                    
                    if target_field == 'Title' and transformation == 'concatenation':
                        # Special handling for Title field
                        title_value = self._create_title_field(order_data, source_fields)
                        if title_value:
                            # Title is the item name, not a column value
                            self.logger.info(f"Computed Title: {title_value}")
                
                # Remove empty values to avoid Monday.com API errors
                cleaned_values = {k: v for k, v in column_values.items() if v and str(v).strip()}
                
                # Task FY3: Add debug logging to track field mapping
                self.logger.info(f"Mapped {len(cleaned_values)} fields from YAML")
                self.logger.debug(f"Sample fields: {list(cleaned_values.keys())[:5]}")
                
                self.logger.info(f"Prepared master item data with {len(cleaned_values)} fields")
                return cleaned_values
                
            else:
                self.logger.warning("No mapping data loaded, using fallback mappings")
                return self._get_fallback_mappings(order_data)
            
        except Exception as e:
            self.logger.error(f"Failed to transform order data: {str(e)}")
            return self._get_fallback_mappings(order_data)
    
    def create_subitem_graphql(self, parent_monday_id: str, subitem_data: pd.Series) -> Dict[str, Any]:
        """
        Create Monday.com subitem using GraphQL API
        
        Args:
            parent_monday_id: Monday.com ID of the parent item
            subitem_data: Series with subitem record data
            
        Returns:
            dict: Creation result with Monday.com subitem_id
        """
        try:
            # Load GraphQL template
            mutation_query = self.load_graphql_template("create-subitem")
            
            # Create subitem name
            size_name = subitem_data.get('stg_size_label', subitem_data.get('Size', 'Unknown Size'))
            subitem_name = f"Size {size_name}"
            
            # Transform subitem data to Monday.com column values using YAML mapping
            column_values = self._transform_subitem_to_monday_columns(subitem_data)
            
            # Prepare variables for GraphQL
            variables = {
                "parentItemId": parent_monday_id,
                "itemName": subitem_name,
                "columnValues": json.dumps(column_values)
            }
            
            self.logger.info(f"Creating subitem via GraphQL: {subitem_name} for parent {parent_monday_id}")
            
            # Execute GraphQL mutation
            result = self.execute_graphql(mutation_query, variables)
            
            if 'errors' in result:
                self.logger.error(f"Failed to create subitem via GraphQL: {result['errors']}")
                return {
                    'id': None,
                    'status': 'failed',
                    'error': result['errors']
                }
            
            # Extract subitem data from GraphQL response
            subitem_data_result = result.get('data', {}).get('create_subitem', {})
            
            if subitem_data_result and subitem_data_result.get('id'):
                self.logger.info(f"Successfully created subitem via GraphQL: {subitem_name} (ID: {subitem_data_result['id']})")
                return {
                    'id': subitem_data_result['id'],
                    'name': subitem_data_result['name'],
                    'status': 'success',
                    'parent_item_id': parent_monday_id,
                    'size_name': size_name,
                    'column_values': subitem_data_result.get('column_values', [])
                }
            else:
                self.logger.error(f"No subitem data returned from GraphQL")
                return {
                    'id': None,
                    'status': 'failed',
                    'error': 'No subitem data returned'
                }
                
        except Exception as e:
            self.logger.error(f"Exception in create_subitem_graphql: {e}")
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def _transform_subitem_to_monday_columns(self, subitem_data: pd.Series) -> Dict[str, Any]:
        """
        Transform subitem data to Monday.com column values using YAML mapping
        
        Args:
            subitem_data: Series with subitem data
            
        Returns:
            dict: Monday.com column values
        """
        try:
            # Build column values using subitem YAML mapping
            column_values = {}
            
            # Size dropdown (required)
            size_name = subitem_data.get('stg_size_label', subitem_data.get('Size', ''))
            if size_name:
                column_values["dropdown_mkrak7qp"] = {"labels": [str(size_name)]}
            
            # Order quantity (required)
            order_qty = subitem_data.get('ORDER_QTY', subitem_data.get('[Order Qty]', 0))
            if pd.notna(order_qty):
                column_values["numeric_mkra7j8e"] = str(int(order_qty))
            
            # Received quantity (default 0)
            column_values["numeric_mkraepx7"] = 0
            
            # Shipped quantity (default 0)
            column_values["numeric_mkrapgwv"] = 0
            
            self.logger.info(f"Prepared subitem column values with {len(column_values)} fields")
            return column_values
            
        except Exception as e:
            self.logger.error(f"Error transforming subitem data: {e}")
            return {}
    
    def update_item_with_uuid(self, monday_item_id: str, source_uuid: str) -> bool:
        """Update Monday.com item with source UUID for tracking"""
        
        try:
            column_values = {
                'text9': source_uuid  # Store UUID in text column
            }
            
            success = update_item_column_values(
                board_id=self.board_id,
                item_id=monday_item_id,
                column_values=column_values
            )
            
            if success:
                self.logger.info(f"SUCCESS: Updated Monday item {monday_item_id} with UUID {source_uuid}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to update Monday item with UUID: {str(e)}")
            return False
    
    def get_existing_item_by_uuid(self, source_uuid: str) -> Optional[str]:
        """Get existing Monday.com item ID by source UUID"""
        
        # This would query Monday.com to find items with matching UUID
        # For now, return None (assuming no existing items)
        # In production, this would use the Monday.com query API
        
        try:
            # TODO: Implement Monday.com query to find items by UUID
            # query = f'''
            # query {{
            #     items_by_column_values(
            #         board_id: {self.board_id},
            #         column_id: "text9",
            #         column_value: "{source_uuid}"
            #     ) {{
            #         id
            #         name
            #     }}
            # }}            # '''
            
            self.logger.info(f"INFO: Checking for existing Monday item with UUID: {source_uuid}")
            return None  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Error checking for existing Monday item: {e}")
            return None

    def _get_board_info(self) -> Optional[Dict[str, Any]]:
        """Get Monday.com board information for connectivity testing"""
        
        try:
            # Placeholder implementation - should use proper Monday.com API
            self.logger.warning("Monday.com board info retrieval not implemented - using placeholder")
            
            board_info = {
                'id': self.board_id,
                'name': f'Board {self.board_id}',
                'description': 'Placeholder board info',
                'groups': [
                    {'id': 'new_group', 'title': 'New Group'},
                    {'id': '2024_q1', 'title': '2024 Q1'}
                ]
            }
            
            self.logger.info(f"Retrieved board info: {board_info.get('name', 'Unknown Board')}")
            return board_info
                
        except Exception as e:
            self.logger.error(f"Failed to get board info: {str(e)}")
            return None

    def _prepare_master_item_data(self, order_data: pd.Series) -> Dict[str, Any]:
        """Prepare master item data for API testing"""
        
        try:
            # Extract key fields for validation
            mapped_data = {
                'customer': order_data.get('CUSTOMER', order_data.get('CUSTOMER NAME', 'Unknown')),
                'aag_order_number': order_data.get('AAG ORDER NUMBER', order_data.get('AAG_ORDER_NUMBER', '')),
                'po_number': order_data.get('PO NUMBER', order_data.get('po_number', '')),
                'customer_style': order_data.get('CUSTOMER STYLE', ''),
                'total_qty': order_data.get('TOTAL QTY', 0),
                'order_date': order_data.get('ORDER DATE PO RECEIVED', ''),
                'source_uuid': order_data.get('source_uuid', order_data.get('uuid', ''))
            }
            
            self.logger.info(f"Prepared master item data with {len(mapped_data)} fields")
            return mapped_data
            
        except Exception as e:
            self.logger.error(f"Failed to prepare master item data: {str(e)}")
            return {}
    
    def _load_mapping_data(self) -> Dict[str, Any]:
        """Load complete mapping data from orders-unified-monday-mapping.yaml"""
        try:
            import yaml
            from pathlib import Path
            
            # Find the repository root
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "utils").exists():
                    repo_root = current
                    break
                current = current.parent
            else:
                raise FileNotFoundError("Could not find repository root")
            
            mapping_file = repo_root / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
            
            if not mapping_file.exists():
                self.logger.error(f"Field mapping file not found: {mapping_file}")
                return {}
            
            with open(mapping_file, 'r') as f:
                mapping_data = yaml.safe_load(f)
            
            self.logger.info(f"Loaded complete mapping configuration from orders-unified-monday-mapping.yaml")
            
            return mapping_data
            
        except Exception as e:
            self.logger.error(f"Failed to load field mapping: {e}")
            return {}

    def _load_comprehensive_mapping(self) -> List[Dict[str, Any]]:
        """Legacy method - Load exact matches for compatibility"""
        mapping_data = self._load_mapping_data()
        return mapping_data.get('exact_matches', [])
    
    def _extract_clean_value(self, value):
        """Extract and clean a value from pandas Series or raw data"""
        if value is None:
            return None
            
        # Extract scalar value if it's a pandas Series
        if hasattr(value, 'iloc'):
            value = value.iloc[0] if len(value) > 0 else None
        elif hasattr(value, 'values'):
            value = value.values[0] if len(value.values) > 0 else None
            
        # Clean string values
        if value is not None:
            clean_value = str(value).strip()
            return clean_value if clean_value else None
        
        return None

    def _apply_transformation(self, value, transformation, field_mapping):
        """Apply transformation to a field value"""
        clean_value = self._extract_clean_value(value)
        if not clean_value:
            return None
            
        if transformation == "customer_mapping_lookup":
            # Use customer mapper for normalization
            if self.customer_mapper:
                return self.customer_mapper.normalize_customer_name(clean_value)
            else:
                # Fallback: simple canonicalization
                return clean_value.upper() if clean_value else clean_value
            
        elif transformation == "direct_mapping":
            return clean_value
            
        elif transformation == "color_mapping":
            # Simple color mapping - could be enhanced with lookup table
            return clean_value.upper()
            
        elif transformation == "value_mapping":
            # Apply value mapping rules
            mapping_rules = field_mapping.get('mapping_rules', [])
            for rule in mapping_rules:
                if clean_value == rule.get('source_value'):
                    return rule.get('target_value')
            return clean_value
            
        else:
            return clean_value

    def _create_title_field(self, order_data, source_fields):
        """Create Title field from concatenation of source fields"""
        try:
            values = []
            for field in source_fields:
                value = self._extract_clean_value(order_data.get(field))
                if value:
                    values.append(value)
            
            if values:
                return "".join(values)  # Concatenate without separators as per mapping
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to create title field: {e}")
            return None

    def _get_fallback_mappings(self, order_data):
        """Fallback mappings when YAML loading fails"""
        return {
            'dropdown_mkr542p2': self._extract_clean_value(order_data.get('CUSTOMER', '')),     # CUSTOMER
            'dropdown_mkr5tgaa': self._extract_clean_value(order_data.get('STYLE', '')),       # STYLE  
            'dropdown_mkr5677f': self._extract_clean_value(order_data.get('COLOR', '')),       # COLOR
            'text_mkr5wya6': self._extract_clean_value(order_data.get('AAG ORDER NUMBER', '')), # AAG ORDER NUMBER
        }
