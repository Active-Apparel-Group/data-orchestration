-- Migration: Add Monday.com subitem board ID tracking column
-- Date: 2025-06-19
-- Purpose: Add stg_monday_subitem_board_id for complete subitem tracking and updates

-- Add stg_monday_subitem_board_id to subitems staging table
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems' 
    AND COLUMN_NAME = 'stg_monday_subitem_board_id'
)
BEGIN
    ALTER TABLE STG_MON_CustMasterSchedule_Subitems 
    ADD stg_monday_subitem_board_id BIGINT NULL;
    
    PRINT 'Added stg_monday_subitem_board_id column to STG_MON_CustMasterSchedule_Subitems';
END
ELSE
BEGIN
    PRINT 'stg_monday_subitem_board_id column already exists in STG_MON_CustMasterSchedule_Subitems';
END

-- Add index for board ID lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_STG_MON_CustMasterSchedule_Subitems_board_id')
BEGIN
    CREATE INDEX IX_STG_MON_CustMasterSchedule_Subitems_board_id 
    ON STG_MON_CustMasterSchedule_Subitems (stg_monday_subitem_board_id);
    
    PRINT 'Created index on stg_monday_subitem_board_id';
END

PRINT 'Monday.com subitem board ID migration completed successfully';
