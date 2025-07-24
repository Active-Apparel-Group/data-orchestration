
Select distinct [CUSTOMER NAME], [PO NUMBER], [AAG SEASON], [CUSTOMER SEASON], [RANGE / COLLECTION], [DROP] from ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755';

Select * from canonical_customer_map

SELECT TOP 10000 * INTO swp_ORDER_LIST from ORDER_LIST


-- 1. View: Find Tables with Blank CUSTOMER NAME
Select * from v_order_list_customer_name_null

-- v_order_list_hash_nulls.sql
-- 2. View: Hash Rows by Ordinal Position (Columns 3-10)
-- vw_order_list_ord3_10_hash
-- Purpose: Generate a hash for ORDER_LIST rows based on specific columns
Select * from [dbo].[v_order_list_hash_nulls]


-- v_order_list_nulls_to_delete.sql
-- 3. View: All-Blank Key Rows (For Deletion)
-- vw_blank_rows_by_ord3_10
Select * from [dbo].[v_order_list_nulls_to_delete]

-- 4. View: First Non-Blank CUSTOMER NAME Per Source Table
-- vw_first_nonblank_customer_name
Select * from v_order_list_customer_name_fill


-- queries
    WITH filled AS (
        SELECT
            *,
            -- Carry down the last non-null CUSTOMER NAME
            MAX(NULLIF([CUSTOMER NAME], '')) OVER (
                ORDER BY record_uuid
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS [CUSTOMER_NAME_FILLED]
        FROM [ORDER_LIST]
    ) 
    Select swp.*
    FROM [ORDER_LIST] swp
    INNER JOIN filled f
        ON swp.record_uuid = f.record_uuid
    WHERE swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = ''

    -- Fill down CUSTOMER NAME from the filled view
    UPDATE swp
    SET [CUSTOMER NAME] = f.[CUSTOMER_NAME_FILLED]
    FROM [swp_ORDER_LIST] swp
    INNER JOIN filled f
        ON swp.record_uuid = f.record_uuid
    WHERE swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = ''


    SELECT [_SOURCE_TABLE], count(*)
    from [ORDER_LIST] swp
    WHERE swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = ''
    group by [_SOURCE_TABLE]

    SELECT 
        CONVERT(VARCHAR(32), HASHBYTES('MD5', 
            CONCAT(
                COALESCE([PLANNED DELIVERY METHOD], ''),
                COALESCE([CUSTOMER STYLE], ''),
                COALESCE([PO NUMBER], ''),
                COALESCE([CUSTOMER ALT PO], ''),
                COALESCE([AAG SEASON], ''),
                COALESCE([CUSTOMER SEASON], ''),
                COALESCE([TOTAL QTY], '')
            )
        ), 2) AS [hash_ord_3_10], *
    from [ORDER_LIST] swp
    WHERE _SOURCE_TABLE = 'xGREYSON_ORDER_LIST_RAW'
    and swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = '';



-- new stored procs or functions in TRANSFORM.py

    -- delete null records from swp_ORDER_LIST before atomic swap
    DELETE FROM [swp_ORDER_LIST]
    WHERE record_uuid IN (
        SELECT record_uuid FROM [v_order_list_nulls_to_delete]
    );

    -- fill down customer name where customer = NULL
    UPDATE swp
    SET [CUSTOMER NAME] = fn.fill_name
    FROM [swp_ORDER_LIST] swp
    INNER JOIN [v_order_list_customer_name_fill] fn
        ON swp.[_SOURCE_TABLE] = fn.[_SOURCE_TABLE]
    WHERE swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = '';

    -- check there are no blank [CUSTOMER NAME] records - CONTINUE 
    SELECT COUNT(*) AS blank_count
    FROM [swp_ORDER_LIST]
    WHERE [CUSTOMER NAME] IS NULL OR LTRIM(RTRIM([CUSTOMER NAME])) = '';

    -- copy customer name to SOURCE_CUSTOMER_NAME
    UPDATE [swp_ORDER_LIST]
    SET [SOURCE_CUSTOMER_NAME] = [CUSTOMER NAME];

    -- update CUSTOMER NAME with canonical_customer name
    UPDATE tgt
    SET [CUSTOMER NAME] = map.[canonical]
    FROM [swp_ORDER_LIST] tgt
    INNER JOIN [canonical_customer_map] map
        ON tgt.[SOURCE_CUSTOMER_NAME] = map.[name]
    WHERE tgt.[CUSTOMER NAME] <> map.[canonical];

    -- validate that all [CUSTOMER NAME] records match a canonical reference
    -- create summary for all customers, confirm all have a matching canonical name
    SELECT 
        [CUSTOMER NAME],
        COUNT(*) AS record_count,
        COUNT(DISTINCT [SOURCE_CUSTOMER_NAME]) AS unique_source_names
    FROM [swp_ORDER_LIST]
    GROUP BY [CUSTOMER NAME]

    -- update group_name for all records
    Update swp_ORDER_LIST
        set group_name = 
        case 
            when [CUSTOMER SEASON] is not null
                then CONCAT([CUSTOMER NAME], ' ', [CUSTOMER SEASON])
            when [CUSTOMER SEASON] is null and [AAG SEASON] is not null
                then CONCAT([CUSTOMER NAME], ' ', [AAG SEASON])
            else 'check'
        end
    WHERE group_name IS NULL OR group_name = '';

    -- update group_id in swp_ORDER_LIST table
    -- update using MON_Boards_Groups where group_name = group_name update group_id
    Update swp_ORDER_LIST
    SET group_id = mbg.group_id
    FROM MON_Boards_Groups mbg
    WHERE swp_ORDER_LIST.group_name = mbg.group_name;

-- validation queries only ---

    Select group_name, count(*) as record_count
    from swp_ORDER_LIST
    group by group_name;

    Select [CUSTOMER NAME], group_name, [ORDER TYPE], 
        sum([TOTAL QTY]) as total_qty, count(*) as record_count, 
        max([ORDER DATE PO RECEIVED]) as max_order_date
    from swp_ORDER_LIST
    where group_name = 'check'
    group by [CUSTOMER NAME], group_name, [ORDER TYPE]
    order by [CUSTOMER NAME], group_name, [ORDER TYPE]; 

    Select CONVERT(VARCHAR(32), HASHBYTES('MD5', 
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
        ), 2) AS [hash_ord_3_10], * from swp_ORDER_LIST
    where group_name = 'check'
    and [CUSTOMER NAME] in ('TRACK SMITH', 'MACK WELDON', 'GREYSON')

    Select group_name, count(*) as record_count
    from swp_ORDER_LIST
    group by group_name;

    Select group_id, count(*) as record_count
    from swp_ORDER_LIST
    group by group_id;

