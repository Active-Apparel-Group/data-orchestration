

-- update order type --
-- match ORDER TYPE column in Monday.com Customer Master Schedule --
UPDATE swp_ORDER_LIST_SYNC 
    SET [ORDER TYPE] = 'RECEIVED' where [ORDER TYPE] = 'ACTIVE'