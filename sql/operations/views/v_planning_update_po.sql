

SELECT 
    [Item ID] as monday_item_id,
    ol.[PO NUMBER] as [BULK PO]
FROM MON_COO_Planning p
join ORDER_LIST ol on ol.[AAG ORDER NUMBER] = p.[AAG ORDER NUMBER] and ol.[CUSTOMER STYLE] = p.[STYLE CODE]
where ol.[PO NUMBER] is not null
and ol.[PO NUMBER] != p.[BULK PO]