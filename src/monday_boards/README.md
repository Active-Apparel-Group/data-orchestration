# Monday.com Board Groups Sync

This module provides functionality to sync board groups from Monday.com boards to the ORDERS database.

## Files

- `sync_board_groups.py` - Main sync script
- `add_board_groups.py` - Create and manage board groups
- `test_sync.py` - Test script to verify functionality
- `__init__.py` - Module initialization

## Scripts Overview

### `sync_board_groups.py`
Syncs board groups from Monday.com boards to the ORDERS database. Maintains a local copy of group structure for reference and tracking.

### `add_board_groups.py`
Provides functionality to create and manage groups on Monday.com boards:
- Create new groups
- Check if groups exist
- List all groups on a board
- Ensure groups exist (create if needed)
- Delete groups

**Key Functions:**
- `ensure_group_exists(board_id, group_name)` - Most commonly used function
- `create_board_group(board_id, group_name)` - Create new group
- `check_group_exists(board_id, group_name)` - Check existence
- `list_board_groups(board_id)` - List all groups

## Usage

### Basic Usage
```bash
# Sync default board (Customer Master Schedule: 9200517329)
python sync_board_groups.py

# Sync specific board by ID
python sync_board_groups.py 1234567890

# Using flag format
python sync_board_groups.py --board-id 1234567890
```

### Test Script
```bash
# Test with default board
python test_sync.py

# Test with specific board
python test_sync.py 1234567890
```

## Configuration

- Uses `config.yaml` for database configuration
- API key is hardcoded in the script (AUTH_KEY variable)
- Follows the same patterns as customer_master_schedule_subitems scripts

## Database

Creates and maintains the `MON_Board_Groups` table with:
- board_id (NVARCHAR(20))
- board_name (NVARCHAR(255))
- group_id (NVARCHAR(50))
- group_title (NVARCHAR(255))
- created_date (DATETIME2)
- updated_date (DATETIME2)
- is_active (BIT)

## Features

- ✅ Dynamic board ID support via command line
- ✅ Hardcoded Monday.com API key
- ✅ Consistent formatting with existing scripts
- ✅ Automatic table creation with indexes
- ✅ Upsert logic with MERGE statements
- ✅ Active/inactive status tracking
- ✅ Comprehensive error handling and logging
- ✅ pyodbc integration matching existing patterns
