-- DELTA Tables Complete Sync State Analysis
-- Check both ORDER_LIST_DELTA and ORDER_LIST_LINES_DELTA sync states

SELECT 
    'ORDER_LIST_DELTA' as table_name,
    ISNULL(sync_state, 'NULL') as sync_state,
    COUNT(*) as record_count,
    MIN([AAG ORDER NUMBER]) as first_order,
    MAX([AAG ORDER NUMBER]) as last_order,
    CASE 
        WHEN sync_state = 'PENDING' THEN 'CORRECT - Ready for Monday sync'
        WHEN sync_state = 'NEW' THEN 'WRONG - Should be PENDING'
        WHEN sync_state = 'SYNCED' THEN 'Already synced'
        WHEN sync_state = 'ERROR' THEN 'Error state'
        ELSE 'Unknown state'
    END as status_comment
FROM dbo.ORDER_LIST_DELTA 
GROUP BY sync_state

UNION ALL

SELECT 
    'ORDER_LIST_LINES_DELTA' as table_name,
    ISNULL(sync_state, 'NULL') as sync_state,
    COUNT(*) as record_count,
    CAST(COUNT(DISTINCT record_uuid) as VARCHAR) as unique_orders,
    CAST(AVG(CAST(qty as FLOAT)) as VARCHAR(10)) as avg_qty,
    CASE 
        WHEN sync_state = 'PENDING' THEN 'CORRECT - Ready for Monday sync'
        WHEN sync_state = 'NEW' THEN 'WRONG - Should be PENDING'
        WHEN sync_state = 'SYNCED' THEN 'Already synced'
        WHEN sync_state = 'ERROR' THEN 'Error state'
        ELSE 'Unknown state'
    END as status_comment
FROM dbo.ORDER_LIST_LINES_DELTA 
GROUP BY sync_state
ORDER BY table_name, sync_state
