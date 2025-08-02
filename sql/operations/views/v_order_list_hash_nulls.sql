

-- v_order_list_hash_nulls.sql
-- 2. View: Hash Rows by Ordinal Position (Columns 3-10)
-- vw_order_list_ord3_10_hash
-- Purpose: Generate a hash for ORDER_LIST rows based on specific columns
CREATE OR ALTER VIEW [dbo].[v_order_list_hash_nulls]
AS
SELECT record_uuid,
    CONVERT(VARCHAR(32), HASHBYTES('MD5',
        CONCAT(
            COALESCE([PLANNED DELIVERY METHOD], ''),
            COALESCE([CUSTOMER STYLE], ''),
            COALESCE([PO NUMBER], ''),
            COALESCE([CUSTOMER ALT PO], ''),
            COALESCE([AAG SEASON], ''),
            COALESCE([CUSTOMER SEASON], ''),
            COALESCE([CUSTOMER COLOUR DESCRIPTION], ''),
            COALESCE([TOTAL QTY], 0) 
        )
    ), 2) AS [hash_ord_3_10]
FROM [swp_ORDER_LIST_SYNC]
where  COALESCE([PLANNED DELIVERY METHOD], '') = ''
            AND COALESCE([CUSTOMER STYLE], '') = ''
            AND COALESCE([PO NUMBER], '') = ''
            AND COALESCE([CUSTOMER ALT PO], '') = ''
            AND COALESCE([AAG SEASON], '') = ''
            AND COALESCE([CUSTOMER SEASON], '') = ''
            AND COALESCE([CUSTOMER COLOUR DESCRIPTION], '') = ''
            AND COALESCE([TOTAL QTY], 0) = 0