-- Migration: Add UUID tracking columns to staging tables
-- Date: 2025-06-19
-- Purpose: Fix missing source_uuid and parent_source_uuid columns for proper UUID tracking

-- Add source_uuid to main staging table
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule' 
    AND COLUMN_NAME = 'source_uuid'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule 
    ADD source_uuid UNIQUEIDENTIFIER NULL;
    
    PRINT 'Added source_uuid column to STG_MON_CustMasterSchedule';
END
ELSE
BEGIN
    PRINT 'source_uuid column already exists in STG_MON_CustMasterSchedule';
END

-- Add parent_source_uuid to subitems staging table
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'parent_source_uuid'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD parent_source_uuid UNIQUEIDENTIFIER NULL;
    
    PRINT 'Added parent_source_uuid column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT 'parent_source_uuid column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add stg_size_label to subitems staging table (also appears to be missing)
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'stg_size_label'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD stg_size_label NVARCHAR(100) NULL;
    
    PRINT 'Added stg_size_label column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT 'stg_size_label column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add indexes for UUID columns for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_STG_MON_CustMasterSchedule_source_uuid')
BEGIN
    CREATE INDEX IX_STG_MON_CustMasterSchedule_source_uuid 
    ON STG_MON_CustMasterSchedule (source_uuid);
    
    PRINT 'Created index on source_uuid';
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_STG_MON_CustMasterSchedule_Subitems_parent_source_uuid')
BEGIN
    CREATE INDEX IX_STG_MON_CustMasterSchedule_Subitems_parent_source_uuid 
    ON STG_MON_CustMasterSchedule_Subitems (parent_source_uuid);
    
    PRINT 'Created index on parent_source_uuid';
END

PRINT 'UUID columns migration completed successfully';
