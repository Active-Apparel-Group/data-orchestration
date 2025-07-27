-- Fix ORDER_LIST_DELTA sync_state from NEW to PENDING
-- Purpose: Prepare ORDER_LIST_DELTA for Monday.com sync engine processing
-- Both DELTA tables should have sync_state='PENDING' for two-pass sync

-- Show current state before correction
SELECT 'BEFORE UPDATE' as stage, sync_state, COUNT(*) as count
FROM dbo.ORDER_LIST_DELTA 
GROUP BY sync_state
ORDER BY sync_state

-- Update ORDER_LIST_DELTA from NEW to PENDING
UPDATE dbo.ORDER_LIST_DELTA 
SET sync_state = 'PENDING'
WHERE sync_state = 'NEW'

-- Show updated state after correction
SELECT 'AFTER UPDATE' as stage, sync_state, COUNT(*) as count
FROM dbo.ORDER_LIST_DELTA 
GROUP BY sync_state
ORDER BY sync_state

-- Verification: Both tables should now have PENDING status
SELECT 
    'FINAL STATUS' as verification,
    'ORDER_LIST_DELTA' as table_name,
    sync_state, 
    COUNT(*) as count
FROM dbo.ORDER_LIST_DELTA 
GROUP BY sync_state

UNION ALL

SELECT 
    'FINAL STATUS' as verification,
    'ORDER_LIST_LINES_DELTA' as table_name,
    sync_state, 
    COUNT(*) as count
FROM dbo.ORDER_LIST_LINES_DELTA 
GROUP BY sync_state
ORDER BY table_name, sync_state
