

-- v_order_list_customer_name_fill.sql
-- 4. View: First Non-Blank CUSTOMER NAME Per Source Table
-- vw_first_nonblank_customer_name
CREATE OR ALTER VIEW [dbo].[v_order_list_customer_name_fill]
AS
SELECT
    [_SOURCE_TABLE],
    MIN([CUSTOMER NAME]) AS fill_name
FROM [ORDER_LIST]
WHERE [CUSTOMER NAME] IS NOT NULL AND LTRIM(RTRIM([CUSTOMER NAME])) <> ''
GROUP BY [_SOURCE_TABLE];
