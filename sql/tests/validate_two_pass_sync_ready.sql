-- DELTA Tables Two-Pass Sync Architecture Validation
-- Validates ORDER_LIST_DELTA and ORDER_LIST_LINES_DELTA are ready for Monday.com two-pass sync

SELECT 
    'ORDER_LIST_DELTA' as table_name,
    ISNULL(sync_state, 'NULL') as sync_state,
    COUNT(*) as record_count,
    MIN([AAG ORDER NUMBER]) as first_order,
    MAX([AAG ORDER NUMBER]) as last_order,
    CASE 
        WHEN sync_state = 'NEW' THEN 'CORRECT - Ready for Monday items sync (Pass 1)'
        WHEN sync_state = 'PENDING' THEN 'Lines state - should be NEW for headers'
        WHEN sync_state = 'SYNCED' THEN 'Already synced to Monday'
        WHEN sync_state = 'ERROR' THEN 'Error state - needs investigation'
        ELSE 'Unexpected state for two-pass sync'
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
        WHEN sync_state = 'PENDING' THEN 'CORRECT - Ready for Monday subitems sync (Pass 2)'
        WHEN sync_state = 'NEW' THEN 'Headers state - should be PENDING for lines'
        WHEN sync_state = 'SYNCED' THEN 'Already synced to Monday'
        WHEN sync_state = 'ERROR' THEN 'Error state - needs investigation'
        ELSE 'Unexpected state for two-pass sync'
    END as status_comment
FROM dbo.ORDER_LIST_LINES_DELTA 
GROUP BY sync_state
ORDER BY table_name, sync_state
