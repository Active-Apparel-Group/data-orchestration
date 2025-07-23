
--v_order_list_nulls_to_delete.sql
-- 3. View: All-Blank Key Rows (For Deletion)
-- vw_blank_rows_by_ord3_10
CREATE OR ALTER VIEW [dbo].[v_order_list_nulls_to_delete]
AS
SELECT *
FROM [v_order_list_hash_nulls]
WHERE [hash_ord_3_10] = '0BD97571DF393B910A7BB62085E15FEA'
  AND ([CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = '');
