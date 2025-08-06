Select 
p.[Item ID] AS [monday_item_id], p.[PARTNER PO] AS [monday_partner_po],
p.[ALLOCATION STATUS] as planning_allocation_status,
c.[ALLOCATION STATUS]
from MON_COO_Planning p
join MON_Purchase_Contracts c on c.[Contract] = p.[PARTNER PO]
where (c.[ALLOCATION STATUS] != p.[ALLOCATION STATUS] and p.[ORDER TYPE] != 'CANCELLED'
and c.[Contract] != 'PG-Johnnie O SS26(3RD)') or p.[ALLOCATION STATUS] is null
