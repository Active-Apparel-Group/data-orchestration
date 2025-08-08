-- =====================================================
-- Migration: 025_create_dropdown_values_table.sql
-- Purpose: Create MON_Dropdown_Values table for storing Monday.com dropdown values
-- Date: 2025-01-27
-- Author: TASK034 - Monday.com Dropdown Values Extraction System
-- =====================================================

-- Drop table if it exists (for clean migration)
IF EXISTS (SELECT * FROM sysobjects WHERE name='MON_Dropdown_Values' AND xtype='U')
BEGIN
    PRINT 'Dropping existing MON_Dropdown_Values table...'
    DROP TABLE MON_Dropdown_Values
END

-- Create MON_Dropdown_Values table
PRINT 'Creating MON_Dropdown_Values table...'
CREATE TABLE MON_Dropdown_Values (
    id INT IDENTITY(1,1) PRIMARY KEY,
    board_id NVARCHAR(50) NOT NULL,
    board_name NVARCHAR(255) NOT NULL,
    column_id NVARCHAR(100) NOT NULL,
    column_name NVARCHAR(255) NOT NULL,
    label_id INT NOT NULL,
    label_name NVARCHAR(500) NOT NULL,
    is_deactivated BIT NOT NULL DEFAULT 0,
    source_type NVARCHAR(20) NOT NULL DEFAULT 'board', -- 'board' or 'managed'
    extracted_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- Create unique constraint to prevent duplicates
    CONSTRAINT UQ_MON_Dropdown_Values UNIQUE (board_id, column_id, label_id)
)

-- Create indexes for efficient querying
PRINT 'Creating indexes for MON_Dropdown_Values...'

-- Index for board/column lookups (most common query pattern)
CREATE INDEX IX_MON_Dropdown_Values_Board_Column 
ON MON_Dropdown_Values (board_id, column_id)

-- Index for board name searches
CREATE INDEX IX_MON_Dropdown_Values_Board_Name 
ON MON_Dropdown_Values (board_name)

-- Index for source type filtering
CREATE INDEX IX_MON_Dropdown_Values_Source_Type 
ON MON_Dropdown_Values (source_type)

-- Index for extraction tracking
CREATE INDEX IX_MON_Dropdown_Values_Extracted_At 
ON MON_Dropdown_Values (extracted_at)

PRINT 'MON_Dropdown_Values table and indexes created successfully!'

-- Validation query
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'MON_Dropdown_Values'
ORDER BY ORDINAL_POSITION
