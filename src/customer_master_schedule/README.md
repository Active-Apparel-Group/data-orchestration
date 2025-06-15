# Monday.com Board Groups Sync

This module provides functionality to sync board groups from Monday.com boards to the ORDERS database.

## Files

- `sync_board_groups.py` - Main sync script
- `test_sync.py` - Test script to verify functionality
- `__init__.py` - Module initialization

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
