# Configuration Update Tracking

This folder contains tools for tracking and managing the migration from hardcoded configurations to the centralized master mapping system.

## Purpose

- **📊 Quantify** all files that need configuration updates
- **📅 Schedule** migration work based on priorities  
- **📋 Track** progress as files are updated
- **🤖 Enable AI agent automation** for systematic cleanup

## Files Generated

### `scan_codebase_config.py`
**Main audit script** that scans the entire codebase for:
- Database connections
- YAML mapping file references  
- Hardcoded board IDs, table names, column IDs
- Configuration patterns that should use the master mapping system

### `config_audit_report.md`
**Comprehensive tracking table** with:
- File paths (with backlinks)
- Folder organization
- DB connection checkboxes ☑️☐
- YAML mapping checkboxes ☑️☐  
- Migration priorities (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)
- Effort estimates
- Detailed findings for high-priority files

### `config_audit_data.json`
**Structured data for AI agents** containing:
- File-by-file analysis results
- Pattern matches and configurations found
- Migration metadata for automation

### `migration_priorities.md`
**Migration planning document** with:
- Recommended migration order
- Phase-based implementation plan
- AI agent automation opportunities
- Specific pattern replacement guidance

## Usage

### Run the Audit
```bash
cd dev/config_update
python scan_codebase_config.py
```

### Review Results
1. **Start with** `config_audit_report.md` - main tracking table
2. **Plan migration** using `migration_priorities.md` 
3. **Use JSON data** for AI agent automation scripts

### Track Progress
- Use checkboxes in the tracking table to mark completed files
- Update migration priorities as files are converted
- Re-run audit periodically to catch new files

## Integration with Master Mapping System

This audit tool is designed to work with the master mapping system located in `utils/`:

- **Master mapping**: `utils/data_mapping.yaml`
- **Helper functions**: `utils/mapping_helper.py`
- **Migration utilities**: `utils/mapping_migration_helper.py`

## AI Agent Guidelines

When using this data for automated cleanup:

1. **Follow priorities**: Start with Critical/High priority files
2. **Use mapping helpers**: Replace hardcoded values with `mapping_helper` function calls
3. **Test thoroughly**: Validate changes don't break existing functionality
4. **Update documentation**: Keep mapping files current as changes are made
5. **Coordinate changes**: Some files may be interdependent

## Migration Patterns

### Board ID Replacement
```python
# Before
BOARD_ID = "8709134353"

# After  
import mapping_helper as mapping
BOARD_ID = mapping.get_board_config('coo_planning')['board_id']
```

### Table Name Replacement
```python
# Before
table_name = "MON_CustMasterSchedule"

# After
table_name = mapping.get_board_config('customer_master_schedule')['table_name']
```

### Type Conversion Replacement
```python
# Before
if field_type == "text":
    sql_type = "NVARCHAR(MAX)"

# After
sql_type = mapping.get_sql_type('text')
```

### YAML File Migration
```python
# Before
config = load_mapping_config('orders_unified_monday_mapping.yaml')

# After  
config = mapping.get_board_config('customer_master_schedule')
```

## Maintenance

- **Re-run audit** after significant code changes
- **Update patterns** in the scanner as new configuration types are added
- **Archive completed migrations** by updating priority to "Complete"
- **Monitor new files** to ensure they follow mapping system guidelines

## Benefits

- **Visibility**: Complete picture of configuration cleanup needed
- **Planning**: Data-driven migration scheduling
- **Automation**: Structured data for AI agent assistance  
- **Quality**: Systematic approach reduces missed configurations
- **Maintenance**: Ongoing tracking prevents configuration drift
