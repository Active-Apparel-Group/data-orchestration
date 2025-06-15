-- Monday.com Board Groups - Query Examples
-- Useful queries for working with the MON_Board_Groups views
-- Created: June 15, 2025

-- ===========================================
-- BASIC QUERIES
-- ===========================================

-- 1. View all active board groups
SELECT * FROM [dbo].[v_MON_Board_Groups_Simple]
ORDER BY group_title;

-- 2. View comprehensive group information
SELECT 
    board_name,
    group_title,
    customer_name,
    season_category,
    group_year,
    status_text,
    days_since_created
FROM [dbo].[v_MON_Board_Groups]
WHERE is_active = 1
ORDER BY group_year DESC, customer_name, group_title;

-- 3. Get board summary statistics
SELECT * FROM [dbo].[v_MON_Board_Groups_Summary];

-- ===========================================
-- FILTERING QUERIES
-- ===========================================

-- 4. Groups by customer
SELECT 
    customer_name,
    group_title,
    season_category,
    group_year
FROM [dbo].[v_MON_Board_Groups]
WHERE customer_name = 'JOHNNIE O'
    AND is_active = 1
ORDER BY group_year DESC;

-- 5. Groups by season category
SELECT 
    customer_name,
    group_title,
    group_year
FROM [dbo].[v_MON_Board_Groups]
WHERE season_category = 'Spring/Summer'
    AND is_active = 1
ORDER BY group_year DESC, customer_name;

-- 6. Groups for specific year
SELECT 
    customer_name,
    group_title,
    season_category
FROM [dbo].[v_MON_Board_Groups]
WHERE group_year = 2025
    AND is_active = 1
ORDER BY customer_name, season_category;

-- ===========================================
-- ANALYTICS QUERIES
-- ===========================================

-- 7. Count groups by customer
SELECT 
    customer_name,
    COUNT(*) as total_groups,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_groups
FROM [dbo].[v_MON_Board_Groups]
GROUP BY customer_name
ORDER BY total_groups DESC;

-- 8. Count groups by season and year
SELECT 
    group_year,
    season_category,
    COUNT(*) as group_count
FROM [dbo].[v_MON_Board_Groups]
WHERE group_year IS NOT NULL
    AND is_active = 1
GROUP BY group_year, season_category
ORDER BY group_year DESC, season_category;

-- 9. Recently updated groups (last 7 days)
SELECT 
    board_name,
    group_title,
    customer_name,
    updated_date_formatted,
    days_since_updated
FROM [dbo].[v_MON_Board_Groups]
WHERE days_since_updated <= 7
ORDER BY updated_date DESC;

-- ===========================================
-- MAINTENANCE QUERIES
-- ===========================================

-- 10. Check for duplicate groups (same title, different IDs)
SELECT 
    group_title,
    COUNT(*) as count,
    STRING_AGG(group_id, ', ') as group_ids
FROM [dbo].[v_MON_Board_Groups]
GROUP BY group_title
HAVING COUNT(*) > 1;

-- 11. Find groups without clear customer or year
SELECT 
    group_title,
    customer_name,
    group_year,
    season_category
FROM [dbo].[v_MON_Board_Groups]
WHERE (customer_name IS NULL OR customer_name = '' OR group_year IS NULL)
    AND is_active = 1
ORDER BY group_title;

-- 12. Inactive groups (for cleanup review)
SELECT 
    group_title,
    customer_name,
    updated_date_formatted,
    days_since_updated
FROM [dbo].[v_MON_Board_Groups]
WHERE is_active = 0
ORDER BY updated_date DESC;

-- ===========================================
-- EXPORT/REPORTING QUERIES
-- ===========================================

-- 13. Customer schedule overview (great for reports)
SELECT 
    customer_name,
    group_year,
    season_category,
    COUNT(*) as group_count,
    STRING_AGG(group_title, ' | ') as group_titles
FROM [dbo].[v_MON_Board_Groups]
WHERE is_active = 1
    AND group_year >= 2025
GROUP BY customer_name, group_year, season_category
ORDER BY customer_name, group_year DESC, season_category;

-- 14. Full board groups export (CSV-friendly)
SELECT 
    board_id,
    board_name,
    group_id,
    group_title,
    customer_name,
    season_category,
    group_year,
    status_text,
    created_date_formatted,
    updated_date_formatted
FROM [dbo].[v_MON_Board_Groups]
ORDER BY customer_name, group_year DESC, group_title;

-- ===========================================
-- USAGE NOTES
-- ===========================================

/*
View Descriptions:

1. v_MON_Board_Groups_Simple: 
   - Basic view with essential fields
   - Only shows active groups
   - Good for quick lookups

2. v_MON_Board_Groups:
   - Comprehensive view with calculated fields
   - Includes customer extraction and categorization
   - Best for detailed analysis

3. v_MON_Board_Groups_Summary:
   - Aggregated statistics by board
   - Shows counts and breakdowns
   - Perfect for dashboards and reporting

Common Patterns:
- Use customer_name for filtering by specific customers
- Use season_category to group by season types
- Use group_year for year-based filtering
- Use is_active = 1 to exclude deactivated groups
- Use days_since_updated for finding stale data
*/
