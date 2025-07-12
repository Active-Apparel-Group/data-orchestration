# VS Code Task for OPUS Update Boards Testing

Add this task to your `.vscode/tasks.json` file:

```json
{
    "label": "Test: OPUS Single Update Workflow",
    "type": "shell",
    "command": "python",
    "args": [
        "tests/debug/test_single_update_workflow.py"
    ],
    "group": "test",
    "options": {
        "cwd": "${workspaceFolder}"
    },
    "detail": "Test complete OPUS update workflow in dry-run mode (Phase 0 validation)"
}
```

## Quick Commands

### Deploy Database Schema
```bash
# Execute all DDL changes
sqlcmd -S server -d database -i "db/ddl/updates/deploy_opus_update_boards.sql"

# Or run via VS Code SQL tools
```

### Run Tests
```bash
# Full test suite
python tests/debug/test_single_update_workflow.py

# Quick validation
python -c "
from pipelines.utils.update_operations import UpdateOperations
ops = UpdateOperations(8709134353)
print('✓ UpdateOperations module working')
"
```

### Check Prerequisites
```sql
-- Verify staging table extensions
SELECT 'STG_MON_CustMasterSchedule' as table_name, COUNT(*) as update_columns
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule'
AND COLUMN_NAME IN ('update_operation', 'update_batch_id', 'validation_status')

UNION ALL

SELECT 'MON_UpdateAudit' as table_name, COUNT(*) as audit_table_exists
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'MON_UpdateAudit';
```
