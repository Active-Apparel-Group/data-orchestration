-- Check DELTA Tables Sync State Status
-- Purpose: Validate sync_state values in ORDER_LIST_DELTA and ORDER_LIST_LINES_DELTA
-- Expected: DIFFERENT states by design for two-pass Monday.com sync architecture
--   - ORDER_LIST_DELTA: sync_state='NEW' (for Monday items creation - Pass 1)
--   - ORDER_LIST_LINES_DELTA: sync_state='PENDING' (for Monday subitems creation - Pass 2)

PRINT 'DELTA Tables Sync State Analysis'
PRINT '=================================='

-- ORDER_LIST_DELTA Status
PRINT ''
PRINT 'ORDER_LIST_DELTA Status:'
SELECT 
    sync_state,
    COUNT(*) as record_count,
    MIN([AAG ORDER NUMBER]) as first_order,
    MAX([AAG ORDER NUMBER]) as last_order,
    MIN(sync_completed_at) as earliest_sync,
    MAX(sync_completed_at) as latest_sync
FROM dbo.ORDER_LIST_DELTA 
GROUP BY sync_state
ORDER BY sync_state

-- ORDER_LIST_LINES_DELTA Status  
PRINT ''
PRINT 'ORDER_LIST_LINES_DELTA Status:'
SELECT 
    sync_state,
    COUNT(*) as record_count,
    COUNT(DISTINCT record_uuid) as unique_orders,
    MIN(qty) as min_qty,
    MAX(qty) as max_qty,
    MIN(sync_completed_at) as earliest_sync,
    MAX(sync_completed_at) as latest_sync
FROM dbo.ORDER_LIST_LINES_DELTA 
GROUP BY sync_state
ORDER BY sync_state

-- Summary Analysis
PRINT ''
PRINT 'DELTA Tables Summary:'
SELECT 
    'ORDER_LIST_DELTA' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_state = 'NEW' THEN 1 END) as new_count,
    COUNT(CASE WHEN sync_state = 'PENDING' THEN 1 END) as pending_count,
    COUNT(CASE WHEN sync_state = 'SYNCED' THEN 1 END) as synced_count,
    COUNT(CASE WHEN sync_state = 'ERROR' THEN 1 END) as error_count
FROM dbo.ORDER_LIST_DELTA

UNION ALL

SELECT 
    'ORDER_LIST_LINES_DELTA' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_state = 'NEW' THEN 1 END) as new_count,
    COUNT(CASE WHEN sync_state = 'PENDING' THEN 1 END) as pending_count,
    COUNT(CASE WHEN sync_state = 'SYNCED' THEN 1 END) as synced_count,
    COUNT(CASE WHEN sync_state = 'ERROR' THEN 1 END) as error_count
FROM dbo.ORDER_LIST_LINES_DELTA

-- Expected State Validation
PRINT ''
PRINT 'Expected State Validation (Two-Pass Sync Architecture):'
PRINT 'ORDER_LIST_DELTA should have sync_state = ''NEW'' (Monday items creation - Pass 1)'
PRINT 'ORDER_LIST_LINES_DELTA should have sync_state = ''PENDING'' (Monday subitems creation - Pass 2)'

-- Check architecture alignment
IF EXISTS (SELECT 1 FROM dbo.ORDER_LIST_DELTA WHERE sync_state = 'NEW')
BEGIN
    PRINT 'CORRECT: ORDER_LIST_DELTA has sync_state = ''NEW'' - ready for Monday items sync (Pass 1)'
END
ELSE
BEGIN
    PRINT 'WARNING: ORDER_LIST_DELTA missing sync_state = ''NEW'' records'
END

IF EXISTS (SELECT 1 FROM dbo.ORDER_LIST_LINES_DELTA WHERE sync_state = 'PENDING')
BEGIN
    PRINT 'CORRECT: ORDER_LIST_LINES_DELTA has sync_state = ''PENDING'' - ready for Monday subitems sync (Pass 2)'
END
ELSE
BEGIN
    PRINT 'WARNING: ORDER_LIST_LINES_DELTA missing sync_state = ''PENDING'' records'
END

PRINT ''
PRINT 'Next Action: Proceed to Task 8.0 Monday Sync Engine - Two-Pass GraphQL Implementation'
