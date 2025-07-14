-- =====================================================================================
-- ORDERS_UNIFIED_SNAPSHOT - Hybrid Snapshot Storage
-- =====================================================================================
-- Purpose: Fast change detection for Orders Unified Delta Sync V3
-- Database: ORDERS (SQL Server)
-- Architecture: Hybrid approach - SQL Server table + Kestra PostgreSQL archive
-- =====================================================================================

-- Primary snapshot table for fast queries (SQL Server)
CREATE TABLE [dbo].[ORDERS_UNIFIED_SNAPSHOT] (
    -- Unique identifier for each record
    [record_uuid] UNIQUEIDENTIFIER NOT NULL,
    
    -- Row hash for change detection (SHA-256)
    [row_hash] NVARCHAR(64) NOT NULL,
    
    -- Business key fields for joins
    [AAG ORDER NUMBER] NVARCHAR(255) NOT NULL,
    [CUSTOMER NAME] NVARCHAR(255) NULL,
    [CUSTOMER STYLE] NVARCHAR(255) NULL,
    [CUSTOMER COLOUR DESCRIPTION] NVARCHAR(255) NULL,
    [PO NUMBER] NVARCHAR(255) NULL,
    [CUSTOMER ALT PO] NVARCHAR(255) NULL,
    [ACTIVE] NVARCHAR(10) NULL,
    
    -- Snapshot metadata
    [snapshot_date] DATETIME2 NOT NULL DEFAULT GETDATE(),
    [customer_filter] NVARCHAR(255) NOT NULL DEFAULT 'ALL',
    [batch_id] UNIQUEIDENTIFIER NULL,
    [records_count] INT NULL,
    
    -- Archive reference
    [parquet_archive_id] BIGINT NULL,  -- FK to Kestra PostgreSQL archive
      -- Primary key constraint
    CONSTRAINT PK_ORDERS_UNIFIED_SNAPSHOT PRIMARY KEY CLUSTERED ([record_uuid])
);

-- Table-level documentation
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Hybrid snapshot storage for ORDERS_UNIFIED change detection. Primary storage in SQL Server for fast queries, with Parquet archive in Kestra PostgreSQL.',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ORDERS_UNIFIED_SNAPSHOT';

-- Column documentation
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for each snapshot record', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDERS_UNIFIED_SNAPSHOT', @level2type = N'COLUMN', @level2name = N'record_uuid';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'SHA-256 hash of concatenated key fields for change detection', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDERS_UNIFIED_SNAPSHOT', @level2type = N'COLUMN', @level2name = N'row_hash';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Customer filter used when creating snapshot (ALL for full dataset)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDERS_UNIFIED_SNAPSHOT', @level2type = N'COLUMN', @level2name = N'customer_filter';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Foreign key reference to Parquet archive in Kestra PostgreSQL', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDERS_UNIFIED_SNAPSHOT', @level2type = N'COLUMN', @level2name = N'parquet_archive_id';

-- Create performance indexes
CREATE NONCLUSTERED INDEX IX_SNAPSHOT_HASH_LOOKUP 
ON [dbo].[ORDERS_UNIFIED_SNAPSHOT] ([row_hash]) 
INCLUDE ([AAG ORDER NUMBER]);

CREATE NONCLUSTERED INDEX IX_SNAPSHOT_CUSTOMER_DATE 
ON [dbo].[ORDERS_UNIFIED_SNAPSHOT] ([customer_filter], [snapshot_date]);

CREATE NONCLUSTERED INDEX IX_SNAPSHOT_AAG_ORDER 
ON [dbo].[ORDERS_UNIFIED_SNAPSHOT] ([AAG ORDER NUMBER]) 
INCLUDE ([row_hash]);

-- =====================================================================================
-- MAINTENANCE PROCEDURES
-- =====================================================================================
GO

-- Cleanup old snapshots (keep only current + 1 previous per customer)
CREATE OR ALTER PROCEDURE [dbo].[sp_cleanup_snapshot_history]
    @customer_filter NVARCHAR(255) = NULL,
    @keep_count INT = 2  -- Keep current + 1 previous
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @deleted_count INT = 0;
    
    -- Delete old snapshots, keeping only the most recent N per customer
    WITH RankedSnapshots AS (
        SELECT 
            record_uuid,
            ROW_NUMBER() OVER (
                PARTITION BY customer_filter 
                ORDER BY snapshot_date DESC
            ) as snapshot_rank
        FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]
        WHERE (@customer_filter IS NULL OR customer_filter = @customer_filter)
    )
    DELETE FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]
    WHERE record_uuid IN (
        SELECT record_uuid 
        FROM RankedSnapshots 
        WHERE snapshot_rank > @keep_count
    );
    
    SET @deleted_count = @@ROWCOUNT;
      PRINT CONCAT('Cleaned up ', @deleted_count, ' old snapshot records');
END;
GO

-- Get snapshot statistics
CREATE OR ALTER PROCEDURE [dbo].[sp_snapshot_statistics]
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        customer_filter,
        COUNT(*) as snapshot_count,
        MIN(snapshot_date) as oldest_snapshot,
        MAX(snapshot_date) as newest_snapshot,
        COUNT(DISTINCT batch_id) as unique_batches,
        SUM(records_count) as total_records
    FROM [dbo].[ORDERS_UNIFIED_SNAPSHOT]
    GROUP BY customer_filter
    ORDER BY customer_filter;
END;
