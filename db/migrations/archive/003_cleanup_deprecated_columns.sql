-- Migration: Clean up deprecated columns from subitems staging table
-- Date: 2025-06-19
-- Purpose: Remove unused columns identified in mapping analysis

-- Remove CUSTOMER_STYLE column (not used in API or business logic)
IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'CUSTOMER_STYLE'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    DROP COLUMN CUSTOMER_STYLE;
    
    PRINT 'Removed CUSTOMER_STYLE column from STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT 'CUSTOMER_STYLE column does not exist in STG_MON_CustMasterSchedule_Subitems';
END

-- Remove GROUP_NAME column (not used anywhere)
IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'GROUP_NAME'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    DROP COLUMN GROUP_NAME;
    
    PRINT 'Removed GROUP_NAME column from STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT 'GROUP_NAME column does not exist in STG_MON_CustMasterSchedule_Subitems';
END

-- Remove ITEM_NAME column (not used anywhere)
IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'ITEM_NAME'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    DROP COLUMN ITEM_NAME;
    
    PRINT 'Removed ITEM_NAME column from STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT 'ITEM_NAME column does not exist in STG_MON_CustMasterSchedule_Subitems';
END

-- Verify final schema
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CASE 
        WHEN COLUMN_NAME LIKE 'stg_%' THEN 'SYSTEM'
        WHEN COLUMN_NAME IN ('parent_source_uuid', 'stg_monday_subitem_board_id') THEN 'UUID_TRACKING'
        WHEN COLUMN_NAME IN ('Size', 'ORDER_QTY', 'stg_size_label') THEN 'API_ESSENTIAL'
        WHEN COLUMN_NAME IN ('AAG_ORDER_NUMBER', 'STYLE', 'COLOR', 'CUSTOMER', 'PO_NUMBER', 'CUSTOMER_ALT_PO', 'UNIT_OF_MEASURE') THEN 'AUDIT_DEBUG'
        ELSE 'OTHER'
    END as COLUMN_CATEGORY
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
ORDER BY ORDINAL_POSITION;

PRINT 'Schema cleanup completed successfully';
