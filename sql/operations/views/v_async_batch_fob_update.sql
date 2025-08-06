SELECT 
    monday_item_id,
    fob_date,
    country_of_origin,
    last_updated
FROM planning_board_updates 
WHERE needs_update = 1 
    AND monday_item_id IS NOT NULL
    AND fob_date IS NOT NULL
ORDER BY last_updated DESC
