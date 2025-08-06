SELECT 
    [Item ID] AS [monday_item_id],
    CAST([Agreed Process Time] AS int) as   [Agreed Process time],
    CONVERT(nvarchar(10), TRY_CAST(DATEADD(DAY, [Agreed Process Time]+1, [Start Date])  AS date), 23) AS [Baseline Date]
FROM MON_Purchase_Contracts_Subitems
WHERE [Due Date] IS NOT NULL 
