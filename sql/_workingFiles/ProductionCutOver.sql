
-- truncate all these tables --
TRUNCATE TABLE swp_ORDER_LIST_V2;
Delete from  ORDER_LIST_V2;
TRUNCATE TABLE ORDER_LIST_LINES;

SELECT * INTO swp_ORDER_LIST_V2 from ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755';

Select count(*) from ORDER_LIST WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755' 
Select count(*) from swp_ORDER_LIST_SYNC WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755' 
Select count(*) from FACT_ORDER_LIST  WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755' 

SELECT TOP 5
            [AAG ORDER NUMBER],
            api_operation_type,
            api_request_payload,
            api_response_payload
        FROM [FACT_ORDER_LIST]
        WHERE api_status = 'ERROR'
        AND api_response_payload IS NOT NULL
        ORDER BY sync_completed_at DESC


SELECT TOP 5 COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FACT_ORDER_LIST' AND COLUMN_NAME LIKE '%api%' ORDER BY COLUMN_NAME

Select record_uuid, monday_item_id, [api_request_payload], [api_response_payload], count(*) 
from FACT_ORDER_LIST L 
group by record_uuid, monday_item_id, [api_request_payload], [api_response_payload]
having monday_item_id is not null

Select  count(*) 
from FACT_ORDER_LIST L 
where sync_state = 'ERROR'

Select api_status, sync_state, count(*)
from swp_ORDER_LIST_SYNC L 
group by api_status, sync_state


Select * from swp_ORDER_LIST_SYNC where group_id is null
Select count(*) from swp_ORDER_LIST_SYNC;
Select count(*) from FACT_ORDER_LIST;
Select count(*) from ORDER_LIST_LINES;
Select count(*) from ORDER_LIST_API_LOG;

Select api_request_payload, api_response_payload from FACT_ORDER_LIST where record_uuid = '5683C886-ABBB-4D16-BF43-48E12D963ED2'


Select L.record_uuid, [AAG ORDER NUMBER], sum(ol.qty) from FACT_ORDER_LIST L
    join ORDER_LIST_LINES ol on ol.record_uuid = L.record_uuid
    group by L.record_uuid, [AAG ORDER NUMBER]
    having (sum(ol.qty) - max([TOTAL QTY])) > 0

-- reset before new migration run
UPDATE swp_ORDER_LIST_SYNC
set group_id = null,
    sync_state = 'PENDING'

    select group_id, count(*)
    from FACT_ORDER_LIST
    group by group_id

    SELECT TOP 10
    [Item ID] as monday_item_id,
    concat(
    [STYLE CODE], 
    COLOR, coalesce([SEASON], [CUSTOMER SEASON])) as keyCustMastSch
FROM MON_COO_Planning;

    Select [CUSTOMER NAME], [sync_state], [ORDER TYPE], count(*)
    from FACT_ORDER_LIST
    group by [CUSTOMER NAME], [sync_state], [ORDER TYPE]

    Select  [sync_state], [action_type], count(*), count(case when api_response_payload is not null then 1 end) as api_response_count, 
    count(case when monday_item_id is not null then 1 end) as monday_item_count
    from FACT_ORDER_LIST
    group by [action_type], [sync_state]

    Select record_uuid, group_id, group_name, sync_state, api_status, api_error_message, monday_item_id, 
    [FREIGHT],
    [CUSTOMER NAME], [AAG ORDER NUMBER], [ORDER TYPE], [CUSTOMER STYLE], api_request_payload, api_response_payload
    from FACT_ORDER_LIST 
    --where [AAG ORDER NUMBER] = 'PEL-05116'
    where record_uuid = '13EE3DDA-0FFF-4D51-AF99-6C00B50BD280'
    where sync_state = 'PENDING' and api_status = 'SUCCESS'

    Select monday_item_id from FACT_ORDER_LIST where [AAG ORDER NUMBER] = 'GRE-04968'

UPDATE FACT_ORDER_LIST
set monday_item_id = '9731115416',
    sync_state = 'SYNCED'
where record_uuid = '8b27283d-4cc1-4c63-b6f5-4662626ce385'

UPDATE FACT_ORDER_LIST
set group_id = 'group_mktf2ef3'
where group_id = 'group_mktednyw'

UPDATE FACT_ORDER_LIST
set monday_item_id = null,
    group_id = null,
    sync_state = 'PENDING',
    action_type = 'INSERT',
    api_request_payload = null,
    api_response_payload = null
where monday_item_id is not null
and group_id not in ( 'group_mkt9z71k')

Delete from FACT_ORDER_LIST;
Delete from ORDER_LIST_LINES;
Delete from ORDER_LIST_API_LOG;
Delete from MON_Boards_Groups where board_id = 9609317401 and group_id not in ( 'group_mkt9z71k')


DELETE from swp_ORDER_LIST_SYNC
where NOT ([CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755') or [CUSTOMER NAME] is null

Delete from swp_ORDER_LIST_SYNC where record_uuid not in (
SELECT record_uuid
FROM swp_ORDER_LIST_SYNC -- CHANGE TO ORDER_LIST (7513 records not 7405)
WHERE 
    [AAG ORDER NUMBER] IN (
        SELECT [AAG ORDER NUMBER] 
        FROM MON_COO_Planning
        WHERE [AAG ORDER NUMBER] IS NOT NULL
    )
    OR 
    [PO NUMBER] IN (
        SELECT DISTINCT [PO NUMBER]
        FROM swp_ORDER_LIST_SYNC
        WHERE [AAG ORDER NUMBER] IN (
            SELECT [AAG ORDER NUMBER] 
            FROM MON_COO_Planning
            WHERE [AAG ORDER NUMBER] IS NOT NULL 
        )
        AND [PO NUMBER] IS NOT NULL
    )
    );

-- check orders not yet merged
select [CUSTOMER NAME], [ORDER DATE PO RECEIVED], count(*)
from swp_ORDER_LIST_SYNC where [AAG ORDER NUMBER] not in (Select [AAG ORDER NUMBER] from 
    FACT_ORDER_LIST)
    group by [CUSTOMER NAME], [ORDER DATE PO RECEIVED]
    order by 1, 2


DELETE from swp_ORDER_LIST_SYNC
where NOT ([CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755') or [CUSTOMER NAME] is null

-- update index and delete null records or records we don't need
    CREATE INDEX idx_orderlist_customer_po 
    ON swp_ORDER_LIST_SYNC ([CUSTOMER NAME], [PO NUMBER]);

    CREATE INDEX idx_orderlist_customer 
    ON swp_ORDER_LIST_SYNC ([CUSTOMER NAME]);

    SELECT [record_uuid] INTO #ToDelete
    FROM swp_ORDER_LIST_SYNC
    WHERE NOT ([CUSTOMER NAME] LIKE 'GREYSON%' AND [PO NUMBER] = '4755') 
    OR [CUSTOMER NAME] IS NULL;

    DELETE FROM swp_ORDER_LIST_SYNC
    WHERE [record_uuid] IN (SELECT [record_uuid] FROM #ToDelete);

    Drop Table #ToDelete;

UPDATE swp_ORDER_LIST_SYNC
        SET [ORDER TYPE] = UPPER([ORDER TYPE])

-- update status so records will sync
    UPDATE swp_ORDER_LIST_SYNC
    SET [sync_state] = 'PENDING',
        [action_type] = 'NONE'
    where NOT ([CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755')

Select * from MON_Boards_Groups

UPDATE FACT_ORDER_LIST
SET [sync_state] = 'COMPLETED',
    [action_type] = 'NONE'
where NOT ([CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755')

Select * from ORDER_LIST_LINES

Select * from swp_ORDER_LIST_SYNC

Select distinct [item_name], [AAG SEASON], [CUSTOMER SEASON], group_name, group_id from swp_ORDER_LIST_SYNC


Select distinct [AAG SEASON], [CUSTOMER SEASON], group_name, group_id from FACT_ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755';


Select distinct [AAG SEASON], [CUSTOMER SEASON], group_name, group_id from swp_ORDER_LIST_SYNC
WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755';

Select * INTO swp_ORDER_LIST_SYNC FROM ORDER_LIST
WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755' 

update swp_ORDER_LIST_SYNC set group_id = null

Select [RANGE / COLLECTION], * from swp_ORDER_LIST_SYNC
WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755' 

DELETE FROM FACT_ORDER_LIST
DELETE FROM ORDER_LIST_LINES
INSERT INTO FACT_ORDER_LIST SELECT * FROM ORDER_LIST
--Select * from swp_ORDER_LIST_SYNC 
WHERE [CUSTOMER NAME] like 'GREYSON%' AND [PO NUMBER] = '4755' 

 SELECT COUNT(*) FROM ORDER_LIST 
            WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755'

Select * from swp_ORDER_LIST_SYNC WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755'
Select * from ORDER_LIST WHERE [CUSTOMER NAME] = 'GREYSON' AND [PO NUMBER] = '4755' and [XL] > 0

DROP TABLE swp_ORDER_LIST_V2;

SELECT COUNT(*) FROM ORDER_LIST_V2 
            WHERE [CUSTOMER NAME] = 'GREYSON' AND sync_state = 'PENDING'

UPDATE ORDER_LIST
set  [CUSTOMER NAME] = 'GREYSON'
-- SET [ORDER TYPE] ='RECEIVED' where [ORDER TYPE] = 'ACTIVE' 
where [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755'

UPDATE FACT_ORDER_LIST SET [ORDER TYPE] = 'CANCELLED' where [ORDER TYPE] = 'Cancelled'

DROP TABLE swp_ORDER_LIST_V2


INSERT INTO swp_ORDER_LIST_V2 Select * from ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755';

Select count(*) 
from ORDER_LIST
WHERE [CUSTOMER NAME] = 'GREYSON CLOTHIERS' AND [PO NUMBER] = '4755' and [XL] > 0;


Select * FROM swp_ORDER_LIST_SYNC
Select * from FACT_ORDER_LIST

Select * from swp_ORDER_LIST_V2


   swp_ORDER_LIST_V2         69    Source table - NEW order detection completed (Task 4.0)  STEP 0 â†’ STEP 1           1
         ORDER_LIST_V2         69 Target table exists - awaiting merge_headers.j2 (Task 5.1)             STEP 1           2
      ORDER_LIST_LINES        317  Lines table exists - awaiting unpivot_sizes.j2 (Task 5.2)             STEP 2           3
      ORDER_LIST_DELTA         69             Delta table exists - awaiting Step 1 execution STEP 1 â†’ STEP 4A           4
ORDER_LIST_LINES_DELTA          0       Lines delta table exists - awaiting Step 3 execution STEP 3 â†’ STEP 4B           5



Select [S], [S+], * from ORDER_LIST_V2 where [PO NUMBER] = '4755'
Select * from ORDER_LIST_DELTA;
Select * from ORDER_LIST_LINES;
Select * from ORDER_LIST_LINES_DELTA;

Select [S], [S+], * from ORDER_LIST where [PO NUMBER] = '4755'

Select [S],  * from xGREYSON_ORDER_LIST_RAW where [PO NUMBER] = '4755'


SELECT TOP (5) [AAG ORDER NUMBER], [CUSTOMER NAME], 
[CUSTOMER STYLE], [LAST_MODIFIED], [LINE NUMBER], 
[MONDAY_ITEM_ID], [MONDAY_SUBITEM_ID], [PO NUMBER], 
[SYNC_STATUS], [SYNC_TIMESTAMP], [TOTAL QTY], [qty], [size_code]
FROM [ORDER_LIST]
WHERE [LAST_MODIFIED] >= '2025-07-21 11:00:15' AND ([SYNC_STATUS] IS NULL OR [SYNC_STATUS] IN ('PENDING', 'ERROR'))
ORDER BY [AAG ORDER NUMBER], [LINE NUMBER]


SELECT TOP (5) [AAG ORDER NUMBER], [CUSTOMER NAME], 
[CUSTOMER STYLE], 
[monday_item_id], [PO NUMBER], 
[sync_state], [TOTAL QTY]
FROM [ORDER_LIST_DELTA]
WHERE ([sync_state] IS NULL OR [sync_state] IN ('PENDING', 'ERROR'))
ORDER BY [AAG ORDER NUMBER]

[SYNC_STATUS] -> [sync_state]
[MONDAY_ITEM_ID] -> [monday_item_id]
[MONDAY_SUBITEM_ID] -- only for lines
SYNC_TIMESTAMP -> last_synced_at
qty -- only for lines
size_code -- only for lines
[LAST_MODIFIED] >= '2025-07-21 11:00:15' -- not required
[LINE NUMBER],  -- what it this!

Select count(*) from MON_Fabric_Library

SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_V2' 
AND COLUMN_NAME NOT IN (
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_V2' 
    AND ORDINAL_POSITION <= (
        SELECT ORDINAL_POSITION 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDER_LIST_V2' AND COLUMN_NAME = 'UNIT OF MEASURE'
    )
    UNION
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'ORDER_LIST_V2' 
    AND ORDINAL_POSITION >= (
        SELECT ORDINAL_POSITION 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDER_LIST_V2' AND COLUMN_NAME = 'TOTAL QTY'
    )
)
ORDER BY ORDINAL_POSITION

Select * from ORDER_LIST_V2




    MERGE dbo.ORDER_LIST_LINES AS target
    USING (
        SELECT
            unpivoted.record_uuid,
            unpivoted.size_code,
            unpivoted.qty,
            CONVERT(CHAR(64), HASHBYTES('SHA2_256',
                CONCAT_WS('|', unpivoted.record_uuid, unpivoted.size_code, unpivoted.qty)), 2) as row_hash,
            'NEW' as sync_state,
            GETUTCDATE() as created_at,
            GETUTCDATE() as updated_at
        FROM (
            SELECT
                record_uuid,
                sync_state,
                size_code,
                qty
            FROM dbo.ORDER_LIST_V2
            UNPIVOT (
                qty FOR size_code IN (
[2T],[3T],[4T],[5T],[6T],[0],[0-3M],[1],[2],[2/3],[3/6 MTHS],[3-6M],[3-4 years],[3],[3-4],[4],[4/5],[04/XXS],[5],[5-6 years],[5-6],[6],[6-12M],[6/7],[6/12 MTHS],[6-9M],[6-10],[S(6-8)],[7],[7-8 years],[7-8],[8],[08/S],[8/9],[M(8-10)],[9],[9-12M],[9-10 years],[9-10],[10],[10/M],[10/11],[10-12],[M(10-12)],[L(10-12)],[11-12 years],[11-14],[12],[12/18 MTHS],[12-18M],[12/L],[12/13],[12-14],[13-14 years],[14],[L(14-16)],[16],[XXXS],[XXS],[XXS/XS],[XS],[XS/S],[S],[M],[L],[XS-PETITE],[06/XS],[CD/XS],[C/XS],[D/XS],[XL],[L/XL],[14/XL],[L-XL],[AB/XL],[CD/XL],[C/XL],[D/XL],[XXL],[2XL],[XL/XXL],[16/XXL],[XL/2XL],[XXL/3XL],[D/XXL],[3XL],[4XL],[18],[18/24 MTHS],[18-24M],[18/XXXL],[20],[22],[24],[25],[26],[27],[28],[28-30L],[29],[30],[30-30L],[30-31L],[30/32],[30-32L],[30/30],[31],[31-30L],[31-31L],[31/32],[31-32L],[31/30],[32],[32-30L],[32-31L],[32/32],[32-32L],[32/34],[32/36],[32/30],[33],[33-30L],[33-31L],[33/32],[33-32L],[33/30],[34],[34-30L],[34-31L],[34/32],[34-32L],[34/34],[34/30],[35],[35-30L],[35-31L],[35/32],[35-32L],[35/30],[36],[36-30L],[36-31L],[36/32],[36-32L],[36/34],[36/30],[38],[38-30L],[38-31L],[38/32],[38-32L],[38/34],[38/36],[38/30],[40],[40-30L],[40-31L],[40/32],[40/30],[42],[43],[44],[45],[46],[48],[50],[52],[54],[56],[58],[60],[OS],[ONE SIZE],[One_Size],[One Sz],[S/M],[M/L],[XXXL],[2X],[3X],[1X],[4X],[S/P],[S+],[1Y],[2Y],[3Y],[4Y],[S-PETITE],[S-M],[32C],[32D],[4XT],[32DD],[30x30],[32DDD],[34C],[30x32],[0w],[2w],[32x30],[One_Sz],[34D],[34DD],[4w],[32x32],[6w],[34DDD],[32x34],[36C],[8w],[34x30],[10w],[O/S],[34x32],[31x30],[36D],[12w],[34x34],[36DD],[36DDD],[36x32],[38C],[36x30],[38D],[36x34],[38x30],[40x30],[38DD],[38x32],[38DDD],[38x34],[40x32],[40x34],[AB/S],[AB/M],[CD/S],[CD/M],[CD/L],[C/S],[C/M],[C/L],[D/S],[D/M],[D/L])
            ) AS sizes
        ) AS unpivoted
        WHERE unpivoted.sync_state = 'PENDING'  -- Only process pending sync records
        AND unpivoted.qty > 0  -- Exclude zero quantities
    ) AS source    
    ON target.record_uuid = source.record_uuid
       AND target.size_code = source.size_code  -- Business key: record + size

    -- Handle NOT MATCHED records (INSERT) - Simplified to match working version
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            record_uuid,
            size_code,
            qty,
            row_hash,
            sync_state,
            created_at,
            updated_at
        )
        VALUES (
            source.record_uuid,
            source.size_code,
            source.qty,
            source.row_hash,
            source.sync_state,
            source.created_at,
            source.updated_at
        );




