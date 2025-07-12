


CREATE or ALTER view v_mon_planning_repeat_orders AS
SELECT 
    p.[STYLE CODE],
    p.[CUSTOMER],
    'Factories | Qty | EX-FTY Date' + CHAR(13) + CHAR(10) +
    ISNULL(STUFF((
        SELECT CHAR(13) + CHAR(10) + f.[FACTORY] 
                + ' | ' + ISNULL(CAST(SUM(f.[BULK PO QTY]) AS NVARCHAR(50)), 'No Qty') 
                + ' | ' + ISNULL(CAST(MAX(COALESCE(f.[EX-FTY DATE (Original)], f.[EX-FTY (Revised LS)])) AS NVARCHAR(50)), 'No Date')
        FROM MON_COO_Planning AS f
        WHERE f.[STYLE CODE] = p.[STYLE CODE]
        GROUP BY f.[FACTORY]
        ORDER BY ISNULL(CAST(MAX(COALESCE(f.[EX-FTY DATE (Original)], f.[EX-FTY (Revised LS)])) AS NVARCHAR(50)), 'No Date') DESC
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, ''), 'No Factories') AS Factories,
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
    AND p.[ORDER TYPE] in ('RECEIVED', 'FORECAST')
GROUP BY 
    p.[STYLE CODE], p.[CUSTOMER]
HAVING 
    COUNT(*) > 1;




