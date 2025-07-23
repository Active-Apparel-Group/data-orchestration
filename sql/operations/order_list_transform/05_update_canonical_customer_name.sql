UPDATE tgt
SET [CUSTOMER NAME] = map.[canonical]
FROM [swp_ORDER_LIST] tgt
INNER JOIN [canonical_customer_map] map
    ON tgt.[SOURCE_CUSTOMER_NAME] = map.[name]
WHERE tgt.[CUSTOMER NAME] <> map.[canonical];
