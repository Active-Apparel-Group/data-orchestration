UPDATE swp
SET [CUSTOMER NAME] = fn.fill_name
FROM [swp_ORDER_LIST] swp
INNER JOIN [v_order_list_customer_name_fill] fn
    ON swp.[_SOURCE_TABLE] = fn.[_SOURCE_TABLE]
WHERE swp.[CUSTOMER NAME] IS NULL OR LTRIM(RTRIM(swp.[CUSTOMER NAME])) = '';
