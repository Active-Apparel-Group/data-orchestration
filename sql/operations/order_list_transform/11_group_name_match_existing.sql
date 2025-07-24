

-- update group_id in swp_ORDER_LIST table
-- we already have existing Groups in Monday.com Customer Master Schedule - we will match these records to our Board
-- update using MON_Boards_Groups where group_name = group_name update group_id
    Update swp_ORDER_LIST
    SET group_id = mbg.group_id
    FROM MON_Boards_Groups mbg
    WHERE swp_ORDER_LIST.group_name = mbg.group_name
    and mbg.board_id = @variable