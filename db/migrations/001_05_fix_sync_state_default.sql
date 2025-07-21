-- Migration 001_05: Fix sync_state Column Default Value
-- Purpose: Remove DEFAULT 'NEW' to enable Python-driven NEW detection logic
-- Reason: Current DEFAULT 'NEW' bypasses merge_orchestrator.py NEW detection
-- Database: orders
-- Created: 2025-07-21
-- Author: ORDER_LIST Delta Monday Sync - Architecture Fix

-- =============================================================================
-- ISSUE ANALYSIS:
-- Current: sync_state VARCHAR(10) NOT NULL DEFAULT ('NEW') 
-- Problem: All records default to 'NEW' regardless of existence in ORDER_LIST_V2
-- Solution: Remove default, let Python merge_orchestrator.py determine sync_state
-- Architecture: NULL → Python detection → 'NEW' or 'EXISTING' based on logic
-- =============================================================================

PRINT '[*] Migration 001_05: Fixing sync_state column architecture flaw';
PRINT '';

-- Step 1: Verify current state
PRINT '[1/4] Current sync_state configuration:';

SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
  AND TABLE_SCHEMA = 'dbo'
  AND COLUMN_NAME = 'sync_state';

-- Step 2: Drop the default constraint
PRINT '[2/4] Removing DEFAULT constraint from sync_state column...';

-- Find and drop the default constraint
DECLARE @constraint_name NVARCHAR(256);
SELECT @constraint_name = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_column_id = c.column_id
JOIN sys.objects o ON dc.parent_object_id = o.object_id
WHERE o.name = 'swp_ORDER_LIST_V2' 
  AND c.name = 'sync_state';

IF @constraint_name IS NOT NULL
BEGIN
    DECLARE @sql NVARCHAR(500);
    SET @sql = 'ALTER TABLE dbo.swp_ORDER_LIST_V2 DROP CONSTRAINT ' + @constraint_name;
    EXEC sp_executesql @sql;
    PRINT 'SUCCESS: Dropped default constraint: ' + @constraint_name;
END
ELSE
BEGIN
    PRINT 'INFO: No default constraint found for sync_state column';
END

-- Step 3: Alter column to allow NULL (remove NOT NULL + DEFAULT)
PRINT '[3/4] Altering sync_state column to allow NULL values...';

ALTER TABLE dbo.swp_ORDER_LIST_V2 
ALTER COLUMN sync_state VARCHAR(10) NULL;

PRINT 'SUCCESS: sync_state column now allows NULL values';

-- Step 4: Set existing records to NULL for Python re-evaluation
PRINT '[4/4] Setting existing sync_state values to NULL for Python re-evaluation...';

DECLARE @updated_rows INT;
UPDATE dbo.swp_ORDER_LIST_V2 
SET sync_state = NULL 
WHERE sync_state = 'NEW';

SET @updated_rows = @@ROWCOUNT;
PRINT 'SUCCESS: Updated ' + CAST(@updated_rows AS VARCHAR(10)) + ' records to NULL sync_state';

-- Verification
PRINT '';
PRINT '[*] VERIFICATION: Updated sync_state column configuration:';

SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'swp_ORDER_LIST_V2' 
  AND TABLE_SCHEMA = 'dbo'
  AND COLUMN_NAME = 'sync_state';

-- Check record states
PRINT '';
PRINT '[*] VERIFICATION: Current sync_state distribution:';

SELECT 
    sync_state,
    COUNT(*) as record_count
FROM dbo.swp_ORDER_LIST_V2
GROUP BY sync_state
ORDER BY sync_state;

-- =============================================================================
-- Architecture Validation
-- =============================================================================

PRINT '';
PRINT '[*] ARCHITECTURE VALIDATION:';
PRINT '  ✅ sync_state column now allows NULL values';
PRINT '  ✅ No DEFAULT constraint - Python logic will control values';
PRINT '  ✅ Existing records reset to NULL for re-evaluation';
PRINT '';
PRINT '[*] NEXT STEPS:';
PRINT '  1. Execute merge_orchestrator.py detect_new_orders() method';
PRINT '  2. Validate Python logic sets sync_state = "NEW" or "EXISTING"';
PRINT '  3. Since ORDER_LIST_V2 is empty, all records should become "NEW"';
PRINT '  4. Continue with ConfigParser integration (Task 2.1)';

-- =============================================================================
-- Success message
-- =============================================================================

PRINT '';
PRINT 'Migration 001_05: sync_state architecture fix completed successfully';
PRINT '';
PRINT 'Column Status:';
PRINT '  - DEFAULT constraint removed';
PRINT '  - NOT NULL constraint removed (now allows NULL)';
PRINT '  - Existing records set to NULL for Python re-evaluation';
PRINT '  - Python merge_orchestrator.py will now control sync_state values';
