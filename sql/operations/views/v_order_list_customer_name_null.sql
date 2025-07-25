

-- v_order_list_customer_name_null.sql
-- 1. View: Find Tables with Blank CUSTOMER NAME
CREATE OR ALTER VIEW [dbo].[v_order_list_customer_name_null]
AS
SELECT
    [_SOURCE_TABLE],
    COUNT(*) AS num_nulls
FROM [swp_ORDER_LIST_SYNC]
WHERE [CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = ''
GROUP BY [_SOURCE_TABLE];



