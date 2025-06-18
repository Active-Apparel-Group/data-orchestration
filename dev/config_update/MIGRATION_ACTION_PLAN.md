# 🎯 Priority Migration Action Items

**Generated:** June 17, 2025  
**Based on:** Comprehensive codebase configuration audit

## 📊 Executive Summary

- **345 files scanned** across the entire codebase
- **22 script files** with hardcoded board IDs that need immediate migration
- **129 files** with database connections
- **87 files** with YAML mapping references  
- **131 files** with hardcoded configurations

## 🔴 CRITICAL: Production Scripts with Hardcoded Board IDs

These are the **highest priority** files for AI agent automation:

### Customer Master Schedule Scripts
```
📁 scripts/customer_master_schedule/
├── add_bulk_orders.py        ← BOARD_ID = "9200517329"
└── add_order.py              ← BOARD_ID = "9200517329"
```

### Monday.com Board Scripts  
```
📁 scripts/monday-boards/
├── get_board_planning.py     ← BOARD_ID = 8709134353
├── add_board_groups.py       ← Multiple 9200517329 references  
└── sync_board_groups.py      ← 5x 9200517329 references
```

### Order Staging Scripts
```
📁 scripts/order_staging/
└── staging_config.py         ← board_id: '9200517329'
```

## 🟠 HIGH: Test Files with Board IDs

These test files should be updated after production scripts:

```
📁 tests/
├── debug/test_simple_steps.py
├── debug/test_step_by_step.py  
├── monday_boards/test_sync.py
├── other/test_end_to_end_complete.py
├── other/test_end_to_end_monday_integration.py
└── other/test_monday_integration_complete.py
```

## 🟡 MEDIUM: Development and Documentation Files

These can be updated as part of ongoing maintenance:

```
📁 dev/monday-boards/
└── get_board_planning.py     ← Development version

📁 docs/ (12 documentation files)
└── Various .md files with board ID references
```

## 🤖 AI Agent Automation Script

Here's the exact replacement patterns for automated migration:

### 1. Board ID Replacements
```python
# Pattern 1: Simple assignment
# BEFORE:
BOARD_ID = "9200517329"
BOARD_ID = 8709134353

# AFTER:
import mapping_helper as mapping
BOARD_ID = mapping.get_board_config('customer_master_schedule')['board_id']  # For 9200517329
BOARD_ID = mapping.get_board_config('coo_planning')['board_id']              # For 8709134353
```

### 2. Table Name Replacements
```python  
# Pattern 2: Table references
# BEFORE:
table_name = "MON_CustMasterSchedule"
table_name = "MON_COO_Planning"

# AFTER:
table_name = mapping.get_board_config('customer_master_schedule')['table_name']
table_name = mapping.get_board_config('coo_planning')['table_name']
```

### 3. Configuration Dictionary Updates
```python
# Pattern 3: Config dictionaries  
# BEFORE:
'board_id': '9200517329'

# AFTER:
'board_id': mapping.get_board_config('customer_master_schedule')['board_id']
```

## 📋 Migration Checklist Template

For each file migration:

- [ ] **Import mapping helper**: `import mapping_helper as mapping`
- [ ] **Replace board IDs**: Use `mapping.get_board_config()` calls
- [ ] **Replace table names**: Use board config table references  
- [ ] **Test functionality**: Ensure no breaking changes
- [ ] **Update imports**: Add any missing dependencies
- [ ] **Verify data flow**: Check end-to-end pipeline still works

## 🎯 Quick Wins (1-2 hours each)

These files have simple, straightforward replacements:

1. `scripts/customer_master_schedule/add_bulk_orders.py`
2. `scripts/customer_master_schedule/add_order.py` 
3. `scripts/monday-boards/get_board_planning.py`
4. `scripts/order_staging/staging_config.py`

## 🔧 Complex Migrations (4+ hours each)

These files have multiple references and need careful review:

1. `scripts/monday-boards/sync_board_groups.py` (5 board ID references)
2. `scripts/monday-boards/add_board_groups.py` (multiple references)
3. `dev/monday-boards/get_board_planning.py` (development version)

## 📝 Before Starting Migration

1. **Backup current working state** - all scripts are functional now
2. **Test master mapping system** - run `utils/test_mapping.py` 
3. **Review mapping configs** - ensure all needed boards are in `utils/data_mapping.yaml`
4. **Set up test environment** - validate changes don't break workflows

## 🏆 Expected Benefits After Migration

- ✅ **Single source of truth** for all board configurations
- ✅ **No more hardcoded IDs** scattered across codebase
- ✅ **Easy environment management** (dev/staging/prod board switching)
- ✅ **Future-proof** board additions and changes
- ✅ **Consistent error handling** through mapping helper functions
- ✅ **Better maintainability** with centralized configuration

---

## 🚀 Ready for AI Agent Execution

This analysis provides everything needed for systematic automation:

- **Clear file list** with exact paths
- **Specific patterns** to find and replace  
- **Exact replacement code** for each pattern
- **Priority order** for safe, incremental migration
- **Test validation** requirements

The master mapping system is ready and tested - time to clean up the codebase! 🧹
