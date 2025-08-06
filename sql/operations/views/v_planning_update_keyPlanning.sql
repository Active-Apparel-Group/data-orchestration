SELECT 
    [Item ID] as monday_item_id,
    concat(
    [STYLE CODE], 
    COLOR, coalesce([SEASON], [CUSTOMER SEASON])) as keyCustMastSch,
    concat(
    [STYLE CODE], [COLOR],
    [BULK PO]) as keyStyleColPO
FROM MON_COO_Planning
where left([ORDER TYPE], 3) != 'FOR'
and keyCustMastSch != concat(
    [STYLE CODE], 
    COLOR, coalesce([SEASON], [CUSTOMER SEASON]))
ORDER BY [Group], [STYLE CODE], [COLOR]