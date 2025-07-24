

-- update group_name for all records
-- this will be used to validate and/or create groups in Customer Master Schedule Board when orders are loaded into Monday.com
    Update swp_ORDER_LIST
        set group_name = 
        case 
            when [CUSTOMER SEASON] is not null
                then CONCAT([CUSTOMER NAME], ' ', [CUSTOMER SEASON])
            when [CUSTOMER SEASON] is null and [AAG SEASON] is not null
                then CONCAT([CUSTOMER NAME], ' ', [AAG SEASON])
            else 'check'
        end
    WHERE group_name IS NULL OR group_name = '';