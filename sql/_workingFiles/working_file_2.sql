

-- find the same style in MON_COO_Planning --
Select top 100 * from MON_COO_Planning

Select [CUSTOMER NAME], [SOURCE_CUSTOMER_NAME], count(*) 
from ORDER_LIST
where [SOURCE_CUSTOMER_NAME] is not null
group by [CUSTOMER NAME], [SOURCE_CUSTOMER_NAME]

Select count(*) from ORDER_LIST 

Select * from xJOHNNIE_O_ORDER_LIST_RAW where [CUSTOMER NAME] is null

-- count number of columns in ORDER_LIST table 
Select count(*) as [Column Count]   
from INFORMATION_SCHEMA.COLUMNS
where TABLE_NAME = 'ORDER_LIST'


-- find duplicate STYLE CODE
Select [STYLE CODE], [CUSTOMER]
from MON_COO_Planning
where [STYLE CODE] is not null
group by [STYLE CODE], [CUSTOMER]
having count(*) > 1 

-- for each duplicate style, create small array
-- STYLE, FACTORY, PARTNER PO, BULK PO QTY
-- ARRAY could be from a CTE, output would be
-- STYLE: xxx
-- FACTORIES: [factory1, factory2, ...]
-- PARTNER POs: [po1, po2, ...]
-- BULK PO QTY: [qty1, qty2, ...]
-- ONLY ORDERS WHERE COUNTRY OF ORIGIN <> CHINA
-- Distinct values in STRING_AGG
SELECT 
    p.[STYLE CODE],
    p.[CUSTOMER],
    STUFF((
        SELECT DISTINCT ', ' + f.[FACTORY]
        FROM MON_COO_Planning AS f
        WHERE f.[STYLE CODE] = p.[STYLE CODE]
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') AS Factories,
    STUFF((
        SELECT CHAR(13) + CHAR(10) + f.[PARTNER PO] + ' | ' + CAST(SUM(f.[BULK PO QTY]) AS NVARCHAR(50)) + ' | ' + po.[ALLOCATION STATUS]
        FROM MON_COO_Planning AS f
        JOIN MON_Purchase_Contracts AS po ON po.Contract = f.[PARTNER PO]
        WHERE f.[STYLE CODE] = p.[STYLE CODE]
        GROUP BY f.[PARTNER PO], po.[ALLOCATION STATUS]
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') AS PartnerPOsWithQty
FROM 
    MON_COO_Planning AS p
WHERE 
    p.[STYLE CODE] IS NOT NULL 
    AND p.[COUNTRY OF ORIGIN] <> 'CHINA'
    AND p.[PARTNER PO] IS NOT NULL
GROUP BY 
    p.[STYLE CODE], p.[CUSTOMER]
HAVING 
    COUNT(*) > 1;


SELECT 
    [Item ID] as monday_item_id,
    CASE 
        WHEN Factory = 'TBC' THEN 'TBC - COO'
        ELSE Factory 
    END AS Factory,
    [Factory (Linked)] AS [xFactory (Linked)], 
    [Factory Location] AS [xFactory Location],
    [Factory Country] AS [xFactory Country],
    [Partner Trading Entity] AS [xPartner Trading Entity],
    [PRODUCTION TYPE]
FROM MON_COO_Planning




Select top 100 * from MES_operational_performance order by closed_time_t desc


WITH status_cte AS (
    SELECT
        [MO Number] as MO_Number,
        state,
        closed_time_t,
        cut_number,
        sew_number,
        finish_number,
        PNP_Receive,
        coalesce([Cutting WIP], 0) as "QTY WIP CUT",
        coalesce([Sewing WIP], 0) as "QTY WIP SEW",
        coalesce([Finishing WIP], 0) as "QTY WIP FIN",
        coalesce([defect_number], 0) as "QTY SCRAP",
        coalesce([cut_number], 0) as "QTY CUT",
        coalesce([sew_number], 0) as "QTY SEW",
        coalesce([finish_number], 0) as "QTY FINISH",
        coalesce([prep_number], 0) as "Precut Quantity", 
        CASE
            WHEN LOWER(state) LIKE '%closed%' THEN 6
            WHEN cut_number > 0 AND sew_number = 0 THEN 5
            WHEN sew_number > 0 AND finish_number = 0 THEN 4
            WHEN finish_number > 0 AND PNP_Receive < finish_number THEN 3
            WHEN PNP_Receive > 0
                 AND finish_number > 0
                 AND PNP_Receive >= finish_number THEN 2
            ELSE 1
        END AS status_rank,
        CASE
            WHEN LOWER(state) LIKE '%closed%' THEN 'COMPLETE'
            WHEN cut_number > 0 AND sew_number = 0 THEN 'CUTTING'
            WHEN sew_number > 0 AND finish_number = 0 THEN 'SEWING'
            WHEN finish_number > 0 AND PNP_Receive < finish_number THEN 'FINISHING'
            WHEN PNP_Receive > 0
                 AND finish_number > 0
                 AND PNP_Receive >= finish_number THEN 'PNP RECEIVED'
            ELSE 'NOT STARTED'
        END AS computed_status
    FROM dbo.MES_operational_performance
),
ranked AS (
    SELECT
        MO_Number,
        state,
        closed_time_t,
        computed_status,
        cut_number,
        sew_number,
        finish_number,
        PNP_Receive,
        [QTY WIP CUT],
        [QTY WIP SEW],
        [QTY WIP FIN],
        [QTY SCRAP],
        [QTY CUT],
        [QTY SEW],
        [QTY FINISH],
        [Precut Quantity],
        ROW_NUMBER() OVER (
            PARTITION BY MO_Number
            ORDER BY status_rank DESC
        ) AS rn
    FROM status_cte
)
SELECT
    [Item ID] AS [monday_item_id],
    p.Factory,
    r.MO_Number,
    r.state as [MES MO Status],
    r.closed_time_t,
    r.computed_status as [PRODUCTION STATUS],
    r.cut_number,
    r.sew_number,
    r.finish_number,
    r.PNP_Receive,
    r.[QTY WIP CUT],
    r.[QTY WIP SEW],
    r.[QTY WIP FIN],
    r.[QTY SCRAP],
    r.[QTY SCRAP],
    r.[QTY CUT],
    r.[QTY SEW],
    r.[QTY FINISH],
    r.[Precut Quantity],
    p.[PRODUCTION STATUS] AS existing_status
FROM ranked r
JOIN dbo.MON_COO_Planning p
  ON p.[MO NUMBER] = r.MO_Number
 AND p.[ORDER TYPE] <> 'CANCELLED'
 AND p.[Factory Country] = 'China'
WHERE r.rn = 1
  AND (p.[PRODUCTION STATUS] IS NULL or p.[QTY WIP CUT] IS NULL OR p.[QTY WIP SEW] IS NULL or p.[QTY WIP FIN] IS NULL or p.[QTY SCRAP] IS NULL
       OR p.[QTY CUT] IS NULL OR p.[QTY SEW] IS NULL OR p.[QTY FINISH] IS NULL
       OR p.[PRODUCTION STATUS] <> r.computed_status
       OR r.[QTY WIP CUT] <> p.[QTY WIP CUT]
       or r.[QTY WIP SEW] <> p.[QTY WIP SEW]
       or r.[QTY WIP FIN] <> p.[QTY WIP FIN]
       or r.[QTY SCRAP] <> p.[QTY SCRAP]
       or r.[QTY CUT] <> p.[QTY CUT]
       or r.[QTY SEW] <> p.[QTY SEW]
       or r.[QTY FINISH] <> p.[QTY FINISH]
       or r.[Precut Quantity] <> p.[Precut Quantity])   
ORDER BY r.MO_Number;

