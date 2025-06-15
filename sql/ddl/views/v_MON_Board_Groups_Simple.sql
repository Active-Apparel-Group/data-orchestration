-- Simple Monday.com Board Groups View
-- Quick and easy view for basic board groups queries
-- Created: June 15, 2025

CREATE VIEW [dbo].[v_mon_boards_groups_Simple] AS
SELECT 
    board_id,
    board_name,
    group_id,
    group_title,
    is_active,
    created_date,
    updated_date
FROM [dbo].[mon_boards_groups]
WHERE is_active = 1  -- Only show active groups by default

GO

-- Add documentation
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Simple view of active Monday.com board groups for quick queries', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'VIEW', @level1name = N'v_mon_boards_groups_Simple';
