

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







