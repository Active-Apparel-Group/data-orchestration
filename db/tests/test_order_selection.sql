-- Test Order Identification Script
-- Purpose: Find a single new order from ORDERS_UNIFIED for isolated testing
-- Created: June 15, 2025

-- =============================================================================
-- STEP 1: FIND NEW ORDERS NOT YET IN STAGING
-- =============================================================================

-- Get a preview of available new orders
SELECT TOP 10
    ou.[AAG ORDER NUMBER],
    ou.[CUSTOMER NAME],
    ou.[CUSTOMER STYLE],
    ou.[CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] as COLOR_CODE,
    ou.[ORDER DATE PO RECEIVED],
    ou.[SHIP DATE],
    'NEW' as STATUS
FROM [dbo].[ORDERS_UNIFIED] ou
LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
    ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
    AND ou.[CUSTOMER STYLE] = cms.[CUSTOMER STYLE] 
    AND ou.[CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] = cms.[COLOR]
WHERE cms.[AAG ORDER NUMBER] IS NULL
    AND ou.[AAG ORDER NUMBER] IS NOT NULL
    AND ou.[CUSTOMER STYLE] IS NOT NULL
    AND ou.[CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] IS NOT NULL
    AND ou.[CUSTOMER NAME] IS NOT NULL
ORDER BY ou.[ORDER DATE PO RECEIVED] DESC, ou.[CUSTOMER NAME];

-- =============================================================================
-- STEP 2: SELECT ONE SPECIFIC ORDER FOR TESTING
-- =============================================================================

-- Pick one order for isolated testing (modify the WHERE clause as needed)
SELECT TOP 1
    ou.*,
    'SELECTED_FOR_TEST' as TEST_STATUS
FROM [dbo].[ORDERS_UNIFIED] ou
LEFT JOIN [dbo].[MON_CustMasterSchedule] cms 
    ON ou.[AAG ORDER NUMBER] = cms.[AAG ORDER NUMBER]
    AND ou.[CUSTOMER STYLE] = cms.[CUSTOMER STYLE] 
    AND ou.[CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] = cms.[COLOR]
WHERE cms.[AAG ORDER NUMBER] IS NULL
    AND ou.[AAG ORDER NUMBER] IS NOT NULL
    AND ou.[CUSTOMER STYLE] IS NOT NULL
    AND ou.[CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] IS NOT NULL
    AND ou.[CUSTOMER NAME] IS NOT NULL
    -- Add specific filters here to pick a good test order:
    -- AND ou.[CUSTOMER NAME] LIKE '%SPECIFIC_CUSTOMER%'
    -- AND ou.[AAG ORDER NUMBER] = 'SPECIFIC_ORDER_NUMBER'
ORDER BY ou.[ORDER DATE PO RECEIVED] DESC;

-- =============================================================================
-- STEP 3: VERIFY SELECTED ORDER IS NOT IN STAGING
-- =============================================================================

-- Double-check our selected order is not already in MON_CustMasterSchedule
SELECT 
    cms.[AAG ORDER NUMBER],
    cms.[CUSTOMER STYLE],
    cms.[COLOR],
    cms.[MONDAY_ITEM_ID],
    cms.[SYNC_STATUS],
    cms.[CREATED_DATE],
    'ALREADY_IN_STAGING' as WARNING
FROM [dbo].[MON_CustMasterSchedule] cms
WHERE cms.[AAG ORDER NUMBER] = 'REPLACE_WITH_SELECTED_ORDER_NUMBER'  -- Update this
    AND cms.[CUSTOMER STYLE] = 'REPLACE_WITH_SELECTED_STYLE'          -- Update this
    AND cms.[COLOR] = 'REPLACE_WITH_SELECTED_COLOR';                  -- Update this

-- =============================================================================
-- STEP 4: GET COMPREHENSIVE ORDER DETAILS FOR TESTING
-- =============================================================================

-- Get full details of the selected test order
DECLARE @TestOrderNumber NVARCHAR(50) = 'REPLACE_WITH_SELECTED_ORDER_NUMBER';  -- Update this
DECLARE @TestCustomerStyle NVARCHAR(50) = 'REPLACE_WITH_SELECTED_STYLE';       -- Update this
DECLARE @TestColor NVARCHAR(50) = 'REPLACE_WITH_SELECTED_COLOR';               -- Update this

SELECT 
    -- Primary identifiers
    [AAG ORDER NUMBER],
    [CUSTOMER STYLE],
    [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] as COLOR,
    
    -- Customer info
    [CUSTOMER NAME],
    [CUSTOMER],
    
    -- Order details
    [ORDER DATE PO RECEIVED],
    [SHIP DATE],
    [QTY ORDERED],
    [QTY SHIPPED],
    
    -- Product details
    [PRODUCT DESCRIPTION],
    [SIZE],
    [UPC],
    
    -- All other columns for mapping verification
    *
FROM [dbo].[ORDERS_UNIFIED]
WHERE [AAG ORDER NUMBER] = @TestOrderNumber
    AND [CUSTOMER STYLE] = @TestCustomerStyle
    AND [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] = @TestColor;

-- =============================================================================
-- STEP 5: STAGING TABLE STATUS CHECK
-- =============================================================================

-- Check current status of MON_CustMasterSchedule table
SELECT 
    COUNT(*) as TOTAL_RECORDS,
    COUNT(CASE WHEN [MONDAY_ITEM_ID] IS NOT NULL AND [MONDAY_ITEM_ID] != '' THEN 1 END) as WITH_MONDAY_ID,
    COUNT(CASE WHEN [MONDAY_ITEM_ID] IS NULL OR [MONDAY_ITEM_ID] = '' THEN 1 END) as PENDING_MONDAY_SYNC,
    COUNT(CASE WHEN [SYNC_STATUS] = 'SYNCED' THEN 1 END) as SYNCED,
    COUNT(CASE WHEN [SYNC_STATUS] = 'PENDING' THEN 1 END) as PENDING,
    COUNT(CASE WHEN [SYNC_STATUS] = 'ERROR' THEN 1 END) as ERRORS
FROM [dbo].[MON_CustMasterSchedule];

-- =============================================================================
-- STEP 6: CUSTOMER ANALYSIS FOR GROUP DETERMINATION
-- =============================================================================

-- Analyze customers to understand grouping patterns
SELECT TOP 10
    [CUSTOMER NAME],
    [CUSTOMER],
    COUNT(*) as ORDER_COUNT,
    MIN([ORDER DATE PO RECEIVED]) as EARLIEST_ORDER,
    MAX([ORDER DATE PO RECEIVED]) as LATEST_ORDER
FROM [dbo].[ORDERS_UNIFIED]
WHERE [CUSTOMER NAME] IS NOT NULL
GROUP BY [CUSTOMER NAME], [CUSTOMER]
ORDER BY COUNT(*) DESC;

-- =============================================================================
-- INSTRUCTIONS FOR TESTING
-- =============================================================================

/*
TESTING WORKFLOW:

1. Run STEP 1 to see available new orders
2. Pick one order and note its details:
   - AAG ORDER NUMBER
   - CUSTOMER STYLE  
   - COLOR CODE
   
3. Update STEP 2, 3, and 4 with the selected order details

4. Run STEP 4 to get full order details for mapping verification

5. Use this order as input for testing:
   - order_mapping.py transformation
   - monday_integration.py item creation
   - order_queries.py database operations

6. Monitor the order through the complete workflow:
   ORDERS_UNIFIED → Transform → MON_CustMasterSchedule → Monday.com → Update Item ID

EXAMPLE ORDER SELECTION:
After running STEP 1, you might select:
- AAG ORDER NUMBER: 'JOH123456'
- CUSTOMER STYLE: 'POLO-SHIRT-001'  
- COLOR: 'NAVY'

Then update the script variables and proceed with testing.
*/
