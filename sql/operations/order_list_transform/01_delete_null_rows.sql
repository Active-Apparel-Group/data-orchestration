DELETE FROM [swp_ORDER_LIST]
WHERE record_uuid IN (
    SELECT record_uuid FROM [v_order_list_nulls_to_delete]
);
