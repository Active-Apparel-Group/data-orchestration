-- Sample master order list query for testing
-- This is a simplified version for demonstration purposes

SELECT 
    'Sample Order' as order_type,
    GETDATE() as order_date,
    'ACTIVE' as status,
    1001 as order_id,
    'Test Customer' as customer_name
UNION ALL
SELECT 
    'Sample Order 2' as order_type,
    GETDATE() as order_date,
    'PENDING' as status,
    1002 as order_id,
    'Test Customer 2' as customer_name
