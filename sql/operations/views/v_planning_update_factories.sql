SELECT 
    [Item ID] as monday_item_id,
    CASE 
        WHEN Factory = 'TBC' THEN 'TBC - COO'
        ELSE Factory 
    END AS Factory,
    [Factory (linked)] as 'linkRef',
    [Factory] AS [Factory (linked)]
FROM MON_COO_Planning
where [Factory (linked)] is null
order by [Item ID] asc
