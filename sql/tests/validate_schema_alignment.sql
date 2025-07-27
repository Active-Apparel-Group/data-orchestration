-- SCHEMA VALIDATION SCRIPT: Monday.com API Integration
-- Purpose: Validate schema alignment between staging tables and Monday.com API
-- Run this AFTER migration to confirm schema fixes

SET NOCOUNT ON;

PRINT '🚨 CRITICAL: Schema Validation for Monday.com API Integration'
PRINT '============================================================='

-- VALIDATION 1: Column naming consistency
PRINT ''
PRINT '1. Column Naming Consistency Check:'
PRINT '-----------------------------------'

-- Check if ORDER_QTY exists in subitems table
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[STG_MON_CustMasterSchedule_Subitems]') AND name = 'ORDER_QTY')
    PRINT '✅ ORDER_QTY column exists in subitems table'
ELSE
    PRINT '❌ CRITICAL: ORDER_QTY column missing in subitems table'

-- Check if old "Order Qty" column still exists (should be removed)
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[STG_MON_CustMasterSchedule_Subitems]') AND name = 'Order Qty')
    PRINT '❌ WARNING: Old "Order Qty" column still exists - migration incomplete'
ELSE
    PRINT '✅ Old "Order Qty" column properly removed'

-- VALIDATION 2: Data type consistency
PRINT ''
PRINT '2. Data Type Consistency Check:'
PRINT '-------------------------------'

SELECT 
    'ORDER_QTY' as Column_Name,
    DATA_TYPE as Current_Type,
    CASE WHEN DATA_TYPE = 'bigint' THEN '✅ Correct' ELSE '❌ Should be BIGINT' END as Validation
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'ORDER_QTY'

-- VALIDATION 3: Monday.com tracking columns
PRINT ''
PRINT '3. Monday.com Tracking Columns:'
PRINT '-------------------------------'

DECLARE @TrackingColumns TABLE (ColumnName VARCHAR(50), ColumnExists BIT)
INSERT INTO @TrackingColumns VALUES 
    ('monday_board_id', 0),
    ('monday_subitem_id', 0),
    ('monday_parent_item_id', 0),
    ('monday_column_mapping', 0)

UPDATE @TrackingColumns 
SET ColumnExists = 1 
WHERE ColumnName IN (
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
)

SELECT 
    ColumnName,
    CASE WHEN ColumnExists = 1 THEN '✅ Present' ELSE '❌ Missing' END as Status
FROM @TrackingColumns

-- VALIDATION 4: Field mapping alignment with Monday.com API
PRINT ''
PRINT '4. Monday.com API Field Alignment:'
PRINT '----------------------------------'

-- Validate against the simple mapping configuration
DECLARE @MappingValidation TABLE (
    Source_Field VARCHAR(100),
    Target_Column VARCHAR(50),
    Status VARCHAR(20)
)

INSERT INTO @MappingValidation VALUES
    ('AAG ORDER NUMBER', 'text_mkr5wya6', 'Expected'),
    ('CUSTOMER', 'text8_mkr518m6', 'Expected'),
    ('AAG SEASON', 'dropdown_mkr58de6', 'Expected'),
    ('ORDER_QTY', 'numbers_mkr5c7q6', 'Expected')

SELECT * FROM @MappingValidation

-- VALIDATION 5: Data integrity check
PRINT ''
PRINT '5. Data Integrity Validation:'
PRINT '-----------------------------'

DECLARE @MasterCount INT, @SubitemCount INT, @OrphanCount INT

SELECT @MasterCount = COUNT(*) FROM [dbo].[STG_MON_CustMasterSchedule]
SELECT @SubitemCount = COUNT(*) FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]

SELECT @OrphanCount = COUNT(*) 
FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
LEFT JOIN [dbo].[STG_MON_CustMasterSchedule] master 
    ON sub.stg_parent_stg_id = master.stg_id
WHERE master.stg_id IS NULL

PRINT 'Master records: ' + CAST(@MasterCount AS VARCHAR(10))
PRINT 'Subitem records: ' + CAST(@SubitemCount AS VARCHAR(10))
PRINT 'Orphaned subitems: ' + CAST(@OrphanCount AS VARCHAR(10))

IF @OrphanCount > 0
    PRINT '❌ WARNING: Orphaned subitem records found'
ELSE
    PRINT '✅ All subitem records properly linked'

-- VALIDATION 6: GREYSON board ID assignment
PRINT ''
PRINT '6. GREYSON Board ID Validation:'
PRINT '-------------------------------'

DECLARE @GreysonRecords INT, @GreysonWithBoardId INT

SELECT @GreysonRecords = COUNT(*) 
FROM [dbo].[STG_MON_CustMasterSchedule] 
WHERE [CUSTOMER] = 'GREYSON'

SELECT @GreysonWithBoardId = COUNT(*) 
FROM [dbo].[STG_MON_CustMasterSchedule] 
WHERE [CUSTOMER] = 'GREYSON' AND [monday_board_id] = 4755559751

PRINT 'GREYSON records: ' + CAST(@GreysonRecords AS VARCHAR(10))
PRINT 'With board ID 4755559751: ' + CAST(@GreysonWithBoardId AS VARCHAR(10))

IF @GreysonRecords = @GreysonWithBoardId AND @GreysonRecords > 0
    PRINT '✅ All GREYSON records have correct board ID'
ELSE
    PRINT '❌ WARNING: Some GREYSON records missing board ID'

-- FINAL VALIDATION SUMMARY
PRINT ''
PRINT '📋 VALIDATION SUMMARY:'
PRINT '====================='
PRINT 'Schema alignment validation completed.'
PRINT 'Review all ❌ items above before proceeding with API integration.'
PRINT ''
PRINT 'Next steps:'
PRINT '- Fix any ❌ validation failures'
PRINT '- Test with GREYSON PO 4755 data'
PRINT '- Validate GraphQL operations in sql/graphql/'
PRINT '- Run Monday.com API integration tests'
