-- Monday.com Board Groups View
-- Provides a comprehensive view of all board groups with useful metadata
-- Created: June 15, 2025

CREATE VIEW [dbo].[v_mon_boards_groups] AS
SELECT 
    bg.board_id,
    bg.board_name,
    bg.group_id,
    bg.group_title,
    bg.created_date,
    bg.updated_date,
    bg.is_active,
    
    -- Calculated fields
    DATEDIFF(day, bg.created_date, GETDATE()) AS days_since_created,
    DATEDIFF(day, bg.updated_date, GETDATE()) AS days_since_updated,
    
    -- Status indicators
    CASE 
        WHEN bg.is_active = 1 THEN 'Active'
        ELSE 'Inactive'
    END AS status_text,
    
    -- Group categorization based on title patterns
    CASE 
        WHEN bg.group_title LIKE '%SPRING%' OR bg.group_title LIKE '%SS%' THEN 'Spring/Summer'
        WHEN bg.group_title LIKE '%FALL%' OR bg.group_title LIKE '%WINTER%' OR bg.group_title LIKE '%FW%' THEN 'Fall/Winter'
        WHEN bg.group_title LIKE '%HOLIDAY%' THEN 'Holiday'
        WHEN bg.group_title LIKE '%Q1%' OR bg.group_title LIKE '%Q2%' OR bg.group_title LIKE '%Q3%' OR bg.group_title LIKE '%Q4%' THEN 'Quarterly'
        WHEN bg.group_title LIKE '%PO %' THEN 'Purchase Order'
        ELSE 'Other'
    END AS season_category,
    
    -- Extract year from group title if available
    CASE 
        WHEN bg.group_title LIKE '%2024%' THEN 2024
        WHEN bg.group_title LIKE '%2025%' THEN 2025
        WHEN bg.group_title LIKE '%2026%' THEN 2026
        WHEN bg.group_title LIKE '%2027%' THEN 2027
        ELSE NULL
    END AS group_year,
    
    -- Extract customer name from group title
    CASE 
        WHEN bg.group_title LIKE 'DSSLR%' THEN 'DSSLR'
        WHEN bg.group_title LIKE 'GREYSON%' THEN 'GREYSON'
        WHEN bg.group_title LIKE 'JOHNNIE O%' THEN 'JOHNNIE O'
        WHEN bg.group_title LIKE 'SEISSENSE%' THEN 'SEISSENSE'
        WHEN bg.group_title LIKE 'TAYLOR MADE%' THEN 'TAYLOR MADE'
        WHEN bg.group_title LIKE 'TRACKSMITH%' THEN 'TRACKSMITH'
        WHEN bg.group_title LIKE 'TITLE NINE%' THEN 'TITLE NINE'
        WHEN bg.group_title LIKE 'UNE PIECE%' THEN 'UNE PIECE'
        ELSE SUBSTRING(bg.group_title, 1, CHARINDEX(' ', bg.group_title + ' ') - 1)
    END AS customer_name,
    
    -- Formatting for display
    FORMAT(bg.created_date, 'yyyy-MM-dd HH:mm') AS created_date_formatted,
    FORMAT(bg.updated_date, 'yyyy-MM-dd HH:mm') AS updated_date_formatted

FROM [dbo].[mon_boards_groups] bg

-- Add metadata about the view
GO

-- Add extended properties for documentation
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Comprehensive view of Monday.com board groups with calculated fields and categorization', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'VIEW', @level1name = N'v_mon_boards_groups';

EXEC sp_addextendedproperty 
    @name = N'Created', 
    @value = N'2025-06-15', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'VIEW', @level1name = N'v_mon_boards_groups';

EXEC sp_addextendedproperty 
    @name = N'Purpose', 
    @value = N'Provides enhanced querying capabilities for Monday.com board groups data', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'VIEW', @level1name = N'v_mon_boards_groups';
