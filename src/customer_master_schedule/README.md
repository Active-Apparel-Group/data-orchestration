# Customer Master Schedule Management

This module manages new and existing orders in the Monday.com Customer Master Schedule board.

## Overview

The Customer Master Schedule system handles order management through the following workflow:

### New Orders
- **Add orders to Monday.com board**: New orders are added to the appropriate group (group_id) on the Customer Master Schedule board
- **Group management**: 
  - If the target group doesn't exist, it will be created automatically
  - If the group exists, the order will be added to it
- **Order placement**: Orders are organized by logical groupings (customer, date, etc.)

### Existing Orders
- **Monitor changes**: Track updates to existing orders in the database
- **Sync updates**: Apply changes to corresponding Monday.com items
- **Status tracking**: Monitor order status and progress

## Scripts

### `add_order.py`
Main script for adding new orders to Monday.com Customer Master Schedule board.

**Key functionality:**
- Creates Monday.com items using board_id and group_id
- Handles group creation if needed
- Maps order data to Monday.com column values
- Includes error handling and logging

**Required inputs:**
- `board_id`: Target Monday.com board ID
- `group_id`: Target group within the board
- Order data from database

### Integration with Monday Boards Module
This module works closely with the `monday_boards` module:
- Uses `sync_board_groups.py` to ensure groups exist
- Uses `add_board_groups.py` to create new groups when needed

## Configuration
- Database connection details in `config.yaml`
- Monday.com API credentials and board configuration
- Column mapping for order data

## Workflow
1. Query database for new orders
2. Determine target group_id for each order
3. Check if group exists (via monday_boards module)
4. Create group if needed
5. Add order item to Monday.com board
6. Log results and handle errors

## Dependencies
- `pandas`: Data manipulation
- `pyodbc`: Database connectivity  
- `requests`: Monday.com API calls
- `yaml`: Configuration management
- `json`: API payload formatting
- `tqdm`: Progress tracking
