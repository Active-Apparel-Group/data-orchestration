

-- v_order_list_hash_nulls.sql
-- 2. View: Hash Rows by Ordinal Position (Columns 3-10)
-- vw_order_list_ord3_10_hash
-- Purpose: Generate a hash for ORDER_LIST rows based on specific columns
CREATE OR ALTER VIEW [dbo].[v_order_list_hash_nulls]
AS
SELECT
    *,
    CONVERT(VARCHAR(32), HASHBYTES('MD5',
        CONCAT(
            COALESCE([PLANNED DELIVERY METHOD], ''),
            COALESCE([CUSTOMER STYLE], ''),
            COALESCE([PO NUMBER], ''),
            COALESCE([CUSTOMER ALT PO], ''),
            COALESCE([AAG SEASON], ''),
            COALESCE([CUSTOMER SEASON], ''),
            COALESCE(CONVERT(VARCHAR(20), [ORDER DATE PO RECEIVED], 120), ''),
            COALESCE([CUSTOMER COLOUR DESCRIPTION], ''),
            COALESCE([TOTAL QTY], '')
        )
    ), 2) AS [hash_ord_3_10]
FROM [swp_ORDER_LIST];
