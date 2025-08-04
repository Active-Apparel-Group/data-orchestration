-- TASK030 Phase 3.1: Add api_error_message column to FACT_ORDER_LIST
-- Purpose: Store extracted error messages from Monday.com API responses
-- Author: TASK030 Implementation
-- Date: 2025-08-03

USE [ORDERS];
GO

-- Check if column already exists
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'FACT_ORDER_LIST' 
    AND COLUMN_NAME = 'api_error_message'
)
BEGIN
    PRINT 'Adding api_error_message column to FACT_ORDER_LIST table...'
    
    ALTER TABLE FACT_ORDER_LIST 
    ADD api_error_message NVARCHAR(2000) NULL;
    
    PRINT 'Successfully added api_error_message column'
END
ELSE
BEGIN
    PRINT 'api_error_message column already exists in FACT_ORDER_LIST table'
END
GO

-- Create index for efficient error message queries
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'IX_FACT_ORDER_LIST_api_error_message'
)
BEGIN
    PRINT 'Creating index on api_error_message column...'
    
    CREATE NONCLUSTERED INDEX IX_FACT_ORDER_LIST_api_error_message
    ON FACT_ORDER_LIST (api_error_message)
    WHERE api_error_message IS NOT NULL;
    
    PRINT 'Successfully created index IX_FACT_ORDER_LIST_api_error_message'
END
ELSE
BEGIN
    PRINT 'Index IX_FACT_ORDER_LIST_api_error_message already exists'
END
GO

-- Validation query
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'FACT_ORDER_LIST' 
AND COLUMN_NAME = 'api_error_message';

PRINT 'TASK030 Phase 3.1 database schema update completed successfully'
