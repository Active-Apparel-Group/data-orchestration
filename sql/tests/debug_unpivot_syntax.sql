-- Debug UNPIVOT Syntax Issue for Task 5.0
-- Test basic UNPIVOT with record_uuid and sync_state columns

-- Test UNPIVOT syntax step by step - CHECK 1: Basic UNPIVOT
SELECT TOP 10
    record_uuid,
    sync_state,
    size_code,
    qty
FROM dbo.ORDER_LIST_V2 
UNPIVOT (
    qty FOR size_code IN ([XS], [S], [M], [L], [XL])  -- Just 5 columns for testing
) AS sizes
WHERE sync_state IN ('NEW', 'CHANGED')
AND qty > 0;
