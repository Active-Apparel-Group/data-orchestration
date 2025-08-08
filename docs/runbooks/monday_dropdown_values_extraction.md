# Monday.com Dropdown Values Extraction System Runbook

## Overview
High-performance async system for extracting Monday.com dropdown values from boards and managed columns. Stores normalized data in `MON_Dropdown_Values` table for efficient querying and reporting.

## Prerequisites

### 1. Database Migration
**REQUIRED:** Run the table creation migration before first use:
```sql
-- Execute in SQL Server Management Studio or via deployment tool
-- File: db/migrations/025_create_dropdown_values_table.sql
```

### 2. Environment Setup
- Monday.com API key configured in `.env` or `config.yaml`
- Azure SQL connection to 'orders' database
- Python dependencies installed: `aiohttp`, `pandas`, `dotenv`

### 3. GraphQL Queries
Ensure these queries exist in `sql/graphql/monday/queries/`:
- `get-board-dropdowns.graphql` - Board-specific dropdown extraction
- `get-managed-dropdowns.graphql` - Global managed columns

## Usage Patterns

### Single Board Extraction
```bash
# Extract dropdown values from one specific board
python load_dropdown_values.py --board-id 9200517329
```

### Multiple Boards
```bash
# Extract from multiple boards simultaneously
python load_dropdown_values.py --board-ids 9200517329 8709134353 8446553051
```

### Workspace-Wide Extraction
```bash
# Extract from all active boards in workspace
python load_dropdown_values.py --all-boards
```

### Include Managed Columns
```bash
# Include global managed dropdown columns
python load_dropdown_values.py --all-boards --include-managed
```

### Performance Tuning
```bash
# Custom batch size and concurrency
python load_dropdown_values.py --board-id 9200517329 \
  --batch-size 50 --max-concurrency 10
```

## Database Schema

### Table: MON_Dropdown_Values
```sql
CREATE TABLE MON_Dropdown_Values (
    id INT IDENTITY(1,1) PRIMARY KEY,
    board_id NVARCHAR(50) NOT NULL,           -- Monday.com board ID or 'MANAGED'
    board_name NVARCHAR(255) NOT NULL,        -- Human-readable board name
    column_id NVARCHAR(100) NOT NULL,         -- Monday.com column ID
    column_name NVARCHAR(255) NOT NULL,       -- Human-readable column name
    label_id INT NOT NULL,                    -- Dropdown option ID
    label_name NVARCHAR(500) NOT NULL,        -- Dropdown option text
    is_deactivated BIT NOT NULL DEFAULT 0,    -- Whether option is deactivated
    source_type NVARCHAR(20) NOT NULL,        -- 'board' or 'managed'
    extracted_at DATETIME2 NOT NULL,          -- Extraction timestamp
    
    CONSTRAINT UQ_MON_Dropdown_Values UNIQUE (board_id, column_id, label_id)
)
```

### Key Indexes
- `IX_MON_Dropdown_Values_Board_Column` - Board/column lookups
- `IX_MON_Dropdown_Values_Board_Name` - Board name searches
- `IX_MON_Dropdown_Values_Source_Type` - Source filtering
- `IX_MON_Dropdown_Values_Extracted_At` - Extraction tracking

## Performance Characteristics

### MERGE/UPSERT Operation
The system uses SQL Server MERGE for optimal performance:
- **Bulk insert** to temporary table (eliminates round trips)
- **Single MERGE** operation handles all inserts/updates
- **~10-100x faster** than row-by-row operations
- **Atomic transaction** ensures data consistency

### Rate Limiting
Integrated with MondayConfig system:
- Automatic rate limit detection and compliance
- Board-specific optimization settings
- Intelligent retry with exponential backoff
- Respects Monday.com's retry_in_seconds suggestions

### Concurrency Control
- Configurable async concurrency limits
- Semaphore-based request throttling
- Optimal settings per board via MondayConfig
- Batch processing for large workspaces

## Data Flow

### 1. Board Discovery (if --all-boards)
```
GraphQL Query → Filter Active Boards → Return Board IDs
```

### 2. Dropdown Extraction
```
Board ID → GraphQL Query → JSON Parsing → Normalized Data Structure
```

### 3. Database Storage
```
Pandas DataFrame → Temp Table → MERGE Operation → Result Counts
```

## Monitoring & Logging

### Log Levels
- **INFO**: Pipeline progress, extraction counts, performance metrics
- **WARNING**: Rate limits, retries, non-critical errors
- **ERROR**: Failed extractions, database errors, critical issues

### Key Metrics
- Total dropdown values extracted
- Database operations (inserted/updated counts)
- Pipeline duration
- Rate limit encounters
- Error rates per board

### Sample Output
```
🚀 Starting dropdown extraction pipeline
📊 Settings: batch_size=25, max_concurrency=5
✅ MON_Dropdown_Values table validated
🎯 Processing 3 specific boards
🔍 Extracting dropdown values for board 9200517329
  📊 Column 'Priority' (priority): 4 dropdown values
  📊 Column 'Status' (status): 6 dropdown values
✅ Extracted 45 dropdown values from board 9200517329
💾 Storing 45 dropdown values using MERGE operation
📊 Bulk inserting to temporary table...
🔄 Executing MERGE operation...
✅ MERGE operation complete: 12 inserted, 33 updated
🎉 Extraction complete!
📊 Total dropdown values extracted: 45
💾 Total values stored/updated: 45
⏱️ Duration: 3.24 seconds
```

## Troubleshooting

### Common Issues

#### 1. Table Not Found Error
```
❌ Table validation failed: MON_Dropdown_Values table not found
```
**Solution**: Run migration `025_create_dropdown_values_table.sql`

#### 2. Monday.com Rate Limits
```
⚠️ MONDAY RATE LIMIT: retry_in_seconds=47.0s (attempt 2/3)
```
**Expected Behavior**: System automatically waits and retries

#### 3. GraphQL Query Not Found
```
❌ GraphQL query not found: sql/graphql/monday/queries/get-board-dropdowns.graphql
```
**Solution**: Ensure GraphQL query files exist in correct location

#### 4. Authentication Errors
```
❌ HTTP 401: Unauthorized
```
**Solution**: Verify `MONDAY_API_KEY` environment variable or `config.yaml` Monday.com token

### Database Issues

#### Constraint Violations
The unique constraint prevents duplicate dropdown values:
```sql
CONSTRAINT UQ_MON_Dropdown_Values UNIQUE (board_id, column_id, label_id)
```

#### Index Maintenance
Indexes auto-maintain but can be rebuilt if performance degrades:
```sql
ALTER INDEX ALL ON MON_Dropdown_Values REBUILD
```

## Integration Points

### With Other Systems
- **ORDER_LIST Pipeline**: References dropdown values for validation
- **Sync Engine**: Uses dropdown mappings for data transformation
- **Audit Pipeline**: Validates dropdown consistency across boards
- **Reporting**: Queries dropdown values for dashboard labels

### VS Code Tasks
Add to `.vscode/tasks.json` for easy execution:
```json
{
    "label": "Extract Dropdown Values - All Boards",
    "type": "shell",
    "command": "python",
    "args": ["pipelines/scripts/ingestion/load_dropdown_values.py", "--all-boards", "--include-managed"],
    "group": "build",
    "options": {"cwd": "${workspaceFolder}"}
}
```

## Maintenance

### Regular Operations
1. **Weekly Extraction**: Capture new dropdown options and changes
2. **Index Maintenance**: Monitor query performance and rebuild if needed
3. **Data Cleanup**: Archive old extraction records if needed
4. **Performance Review**: Monitor extraction times and optimize settings

### Configuration Updates
Update MondayConfig settings in `configs/monday_boards.toml`:
```toml
[boards."9200517329"]
rate_limit = { requests_per_minute = 25, burst_limit = 12 }
optimization = { batch_size = 25, max_concurrency = 5 }
```

## Advanced Usage

### Custom GraphQL Integration
For new dropdown column types, add queries to `sql/graphql/monday/queries/`:
1. Create `.graphql` file with Monday.com GraphQL syntax
2. Update `load_graphql_query()` function if needed
3. Test with single board before batch processing

### Database Query Examples
```sql
-- Get all dropdown values for a specific board
SELECT board_name, column_name, label_name, is_deactivated
FROM MON_Dropdown_Values 
WHERE board_id = '9200517329'
ORDER BY column_name, label_name;

-- Find all active dropdown options
SELECT DISTINCT column_name, label_name
FROM MON_Dropdown_Values 
WHERE is_deactivated = 0 AND source_type = 'board'
ORDER BY column_name, label_name;

-- Get extraction summary by board
SELECT 
    board_name,
    COUNT(*) as total_options,
    COUNT(CASE WHEN is_deactivated = 0 THEN 1 END) as active_options,
    MAX(extracted_at) as last_extracted
FROM MON_Dropdown_Values 
WHERE source_type = 'board'
GROUP BY board_id, board_name
ORDER BY board_name;
```

## Related Documentation
- [TASK034 Implementation Details](../../memory-bank/tasks/TASK034-monday-dropdown-values-extraction.md)
- [Database Migrations](../../db/migrations/)
- [GraphQL Queries](../../sql/graphql/)
- [Monday.com Integration Patterns](../patterns/)
