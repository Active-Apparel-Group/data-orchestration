-- CRITICAL MIGRATION SCRIPT: Schema Alignment for Monday.com API
-- Purpose: Safely migrate existing data to new schema structure
-- Priority: CRITICAL - Must run before production deployment

-- STEP 1: Backup existing data
PRINT 'Starting Monday.com Schema Alignment Migration...'

-- Create backup table for subitems
IF OBJECT_ID('[dbo].[STG_MON_CustMasterSchedule_Subitems_BACKUP]') IS NOT NULL
    DROP TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems_BACKUP];

SELECT * INTO [dbo].[STG_MON_CustMasterSchedule_Subitems_BACKUP]
FROM [dbo].[STG_MON_CustMasterSchedule_Subitems];

PRINT 'Backup created: STG_MON_CustMasterSchedule_Subitems_BACKUP'

-- STEP 2: Update column names and data types in staging table
-- Handle column naming standardization

-- Fix ORDER QTY column naming inconsistency
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[STG_MON_CustMasterSchedule_Subitems]') AND name = 'Order Qty')
BEGIN
    -- Add new standardized column
    ALTER TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] 
    ADD [ORDER_QTY] BIGINT NULL;
    
    -- Migrate data (convert NVARCHAR to BIGINT safely)
    UPDATE [dbo].[STG_MON_CustMasterSchedule_Subitems]
    SET [ORDER_QTY] = CASE 
        WHEN ISNUMERIC([Order Qty]) = 1 THEN CAST([Order Qty] AS BIGINT)
        ELSE NULL
    END
    WHERE [Order Qty] IS NOT NULL;
    
    -- Drop old column after data migration
    ALTER TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] 
    DROP COLUMN [Order Qty];
    
    PRINT 'Fixed: Order Qty -> ORDER_QTY (BIGINT)'
END

-- STEP 3: Add Monday.com tracking columns
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[STG_MON_CustMasterSchedule_Subitems]') AND name = 'monday_board_id')
BEGIN
    ALTER TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems] 
    ADD [monday_board_id] BIGINT NULL,
        [monday_subitem_id] BIGINT NULL,
        [monday_parent_item_id] BIGINT NULL,
        [monday_column_mapping] NVARCHAR(MAX) NULL;
    
    PRINT 'Added Monday.com tracking columns'
END

-- STEP 4: Set default board ID for existing GREYSON records
UPDATE sub
SET sub.[monday_board_id] = 4755559751
FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] sub
INNER JOIN [dbo].[STG_MON_CustMasterSchedule] master 
    ON sub.stg_parent_stg_id = master.stg_id
WHERE master.[CUSTOMER] = 'GREYSON' 
    AND sub.[monday_board_id] IS NULL;

PRINT 'Set default board ID for GREYSON records'

-- STEP 5: Validate data integrity
DECLARE @RowCount INT, @ErrorCount INT

SELECT @RowCount = COUNT(*) FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
SELECT @ErrorCount = COUNT(*) FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] 
WHERE [ORDER_QTY] IS NULL AND [stg_order_qty_numeric] IS NOT NULL

PRINT 'Migration Validation:'
PRINT 'Total rows: ' + CAST(@RowCount AS VARCHAR(10))
PRINT 'Data conversion errors: ' + CAST(@ErrorCount AS VARCHAR(10))

IF @ErrorCount > 0
BEGIN
    PRINT 'WARNING: Some quantity values could not be converted to BIGINT'
    SELECT TOP 10 stg_subitem_id, [stg_order_qty_numeric], [ORDER_QTY]
    FROM [dbo].[STG_MON_CustMasterSchedule_Subitems] 
    WHERE [ORDER_QTY] IS NULL AND [stg_order_qty_numeric] IS NOT NULL
END

PRINT 'Schema alignment migration completed successfully!'
PRINT 'Backup table available: STG_MON_CustMasterSchedule_Subitems_BACKUP'
