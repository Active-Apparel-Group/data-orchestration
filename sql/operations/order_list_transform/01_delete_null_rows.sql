DELETE FROM [swp_ORDER_LIST_SYNC]
where  COALESCE([PLANNED DELIVERY METHOD], '') = ''
            AND COALESCE([CUSTOMER STYLE], '') = ''
            AND COALESCE([PO NUMBER], '') = ''
            AND COALESCE([CUSTOMER ALT PO], '') = ''
            AND COALESCE([AAG SEASON], '') = ''
            AND COALESCE([CUSTOMER SEASON], '') = ''
            AND COALESCE([CUSTOMER COLOUR DESCRIPTION], '') = ''
            AND COALESCE([TOTAL QTY], 0) = 0

/*
WHERE record_uuid IN (
    SELECT record_uuid FROM [v_order_list_nulls_to_delete]
);
*/