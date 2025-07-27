-- Check DELTA Tables Sync State Status
-- Purpose: Validate sync_state values in ORDER_LIST_DELTA and ORDER_LIST_LINES_DELTA

-- ORDER_LIST_DELTA Status
SELECT 
    'ORDER_LIST_DELTA' as table_name,
    sync_state,
    COUNT(*) as record_count,
    MIN([AAG ORDER NUMBER]) as first_order,
    MAX([AAG ORDER NUMBER]) as last_order
FROM dbo.ORDER_LIST_DELTA 
GROUP BY sync_state
ORDER BY sync_state

-- ORDER_LIST_LINES_DELTA Status  
SELECT 
    'ORDER_LIST_LINES_DELTA' as table_name,
    sync_state,
    COUNT(*) as record_count,
    COUNT(DISTINCT record_uuid) as unique_orders,
    MIN(qty) as min_qty,
    MAX(qty) as max_qty
FROM dbo.ORDER_LIST_LINES_DELTA 
GROUP BY sync_state
ORDER BY sync_state

-- Summary Analysis
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
