
-- v_order_list_customer_name_fill_down
-- 5. View: Fill-Down [CUSTOMER NAME] (Preview)
-- vw_customer_name_filled_preview.sql
CREATE OR ALTER VIEW [dbo].[v_order_list_customer_name_fill_down]
AS
SELECT
    swp.[CUSTOMER NAME],
    fn.fill_name AS [CUSTOMER_NAME_FILLED]
FROM [ORDER_LIST] swp
LEFT JOIN [v_order_list_customer_name_fill] fn
    ON swp.[_SOURCE_TABLE] = fn.[_SOURCE_TABLE]
WHERE swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = '';

