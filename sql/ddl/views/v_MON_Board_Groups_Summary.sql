-- Monday.com Board Groups Summary View
-- Provides summary statistics and analytics for board groups
-- Created: June 15, 2025

CREATE VIEW [dbo].[v_MON_Board_Groups_Summary] AS
SELECT 
    board_id,
    board_name,
    
    -- Group counts
    COUNT(*) AS total_groups,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_groups,
    SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) AS inactive_groups,
    
    -- Date statistics
    MIN(created_date) AS first_group_created,
    MAX(created_date) AS last_group_created,
    MAX(updated_date) AS last_updated,
    
    -- Season/Category breakdown
    SUM(CASE WHEN group_title LIKE '%SPRING%' OR group_title LIKE '%SS%' THEN 1 ELSE 0 END) AS spring_summer_groups,
    SUM(CASE WHEN group_title LIKE '%FALL%' OR group_title LIKE '%WINTER%' OR group_title LIKE '%FW%' THEN 1 ELSE 0 END) AS fall_winter_groups,
    SUM(CASE WHEN group_title LIKE '%HOLIDAY%' THEN 1 ELSE 0 END) AS holiday_groups,
    SUM(CASE WHEN group_title LIKE '%Q1%' OR group_title LIKE '%Q2%' OR group_title LIKE '%Q3%' OR group_title LIKE '%Q4%' THEN 1 ELSE 0 END) AS quarterly_groups,
    SUM(CASE WHEN group_title LIKE '%PO %' THEN 1 ELSE 0 END) AS po_groups,
    
    -- Year breakdown
    SUM(CASE WHEN group_title LIKE '%2024%' THEN 1 ELSE 0 END) AS groups_2024,
    SUM(CASE WHEN group_title LIKE '%2025%' THEN 1 ELSE 0 END) AS groups_2025,
    SUM(CASE WHEN group_title LIKE '%2026%' THEN 1 ELSE 0 END) AS groups_2026,
    
    -- Activity metrics
    AVG(DATEDIFF(day, created_date, GETDATE())) AS avg_days_since_created,
    AVG(DATEDIFF(day, updated_date, GETDATE())) AS avg_days_since_updated

FROM [dbo].[MON_Board_Groups]
GROUP BY board_id, board_name

GO

-- Add documentation
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Summary analytics view for Monday.com board groups with counts and statistics', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'VIEW', @level1name = N'v_MON_Board_Groups_Summary';
