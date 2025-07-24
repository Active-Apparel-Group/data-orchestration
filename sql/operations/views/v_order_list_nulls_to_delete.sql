
--v_order_list_nulls_to_delete.sql
-- 3. View: All-Blank Key Rows (For Deletion)
-- vw_blank_rows_by_ord3_10
CREATE OR ALTER VIEW [dbo].[v_order_list_nulls_to_delete]
AS
SELECT *
FROM [v_order_list_hash_nulls]
WHERE [hash_ord_3_10] in ('A46C3B54F2C9871CD81DAF7A932499C0', '774F655800BE1B7CCDFED8C4E4E697FA');


-- all null: A46C3B54F2C9871CD81DAF7A932499C0
-- TOTAL QTY is 0 = 774F655800BE1B7CCDFED8C4E4E697FA