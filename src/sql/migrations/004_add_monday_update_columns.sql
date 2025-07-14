-- Migration: Add Monday.com update columns to subitems staging table  
-- Date: 2025-06-19
-- Purpose: Add all Monday.com update fields for robust API payload generation

-- Add Monday.com columns that are missing from staging table
-- Based on monday_column_ids.json and board_9200517329_metadata.json

-- Add [Order Qty] column (primary Monday.com field)
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Order Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Order Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Order Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Order Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Shipped Qty] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Shipped Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Shipped Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Shipped Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Shipped Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Packed Qty] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Packed Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Packed Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Packed Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Packed Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Cut Qty] column  
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Cut Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Cut Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Cut Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Cut Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Sew Qty] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Sew Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Sew Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Sew Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Sew Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Finishing Qty] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Finishing Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Finishing Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Finishing Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Finishing Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Received not Shipped Qty] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Received not Shipped Qty'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Received not Shipped Qty] NVARCHAR(MAX) NULL;
    
    PRINT 'Added [Received not Shipped Qty] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Received not Shipped Qty] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [ORDER LINE STATUS] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'ORDER LINE STATUS'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [ORDER LINE STATUS] NVARCHAR(200) NULL;
    
    PRINT 'Added [ORDER LINE STATUS] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[ORDER LINE STATUS] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add [Item ID] column
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'Item ID'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD [Item ID] NVARCHAR(200) NULL;
    
    PRINT 'Added [Item ID] column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT '[Item ID] column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Verify final schema
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CASE 
        WHEN COLUMN_NAME LIKE 'stg_%' THEN 'SYSTEM'
        WHEN COLUMN_NAME IN ('parent_source_uuid') THEN 'UUID_TRACKING'
        WHEN COLUMN_NAME IN ('Size', '[Order Qty]') THEN 'API_ESSENTIAL' 
        WHEN COLUMN_NAME IN ('[Shipped Qty]', '[Packed Qty]', '[Cut Qty]', '[Sew Qty]', '[Finishing Qty]', '[Received not Shipped Qty]', '[ORDER LINE STATUS]', '[Item ID]') THEN 'API_UPDATE'
        WHEN COLUMN_NAME IN ('AAG_ORDER_NUMBER', 'STYLE', 'COLOR', 'CUSTOMER', 'PO_NUMBER', 'CUSTOMER_ALT_PO', 'UNIT_OF_MEASURE', 'ORDER_QTY') THEN 'AUDIT_DEBUG'
        ELSE 'OTHER'
    END as COLUMN_CATEGORY
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'
ORDER BY ORDINAL_POSITION;

PRINT 'Monday.com update columns migration completed successfully';
