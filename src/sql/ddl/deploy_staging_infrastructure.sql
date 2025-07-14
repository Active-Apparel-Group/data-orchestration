-- Deployment Script: Monday.com Staging Infrastructure
-- Purpose: Create all staging, error, and tracking tables for Monday.com integration
-- Run Order: Execute statements in order shown below
-- Database: ORDERS

-- ====================================================
-- Phase 1: Create Staging Tables
-- ====================================================

-- 1.1 Main staging table for orders
PRINT 'Creating STG_MON_CustMasterSchedule...'
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[STG_MON_CustMasterSchedule]') AND type in (N'U'))
BEGIN
    EXEC('CREATE TABLE [dbo].[STG_MON_CustMasterSchedule] ([temp_col] INT)') -- Temporary table
END
GO

-- Drop and recreate to ensure latest schema
DROP TABLE IF EXISTS [dbo].[STG_MON_CustMasterSchedule_Subitems]; -- Drop child first due to FK
DROP TABLE IF EXISTS [dbo].[STG_MON_CustMasterSchedule];

EXEC sp_executesql N'$(staging_table_sql)'; -- Will be replaced with actual table creation

PRINT 'STG_MON_CustMasterSchedule created successfully.'
GO

-- 1.2 Subitems staging table
PRINT 'Creating STG_MON_CustMasterSchedule_Subitems...'
GO

EXEC sp_executesql N'$(staging_subitems_table_sql)'; -- Will be replaced with actual table creation

PRINT 'STG_MON_CustMasterSchedule_Subitems created successfully.'
GO

-- ====================================================
-- Phase 2: Create Error Tables
-- ====================================================

-- 2.1 Main error table
PRINT 'Creating ERR_MON_CustMasterSchedule...'
GO

DROP TABLE IF EXISTS [dbo].[ERR_MON_CustMasterSchedule];

EXEC sp_executesql N'$(error_table_sql)'; -- Will be replaced with actual table creation

PRINT 'ERR_MON_CustMasterSchedule created successfully.'
GO

-- 2.2 Subitems error table
PRINT 'Creating ERR_MON_CustMasterSchedule_Subitems...'
GO

DROP TABLE IF EXISTS [dbo].[ERR_MON_CustMasterSchedule_Subitems];

EXEC sp_executesql N'$(error_subitems_table_sql)'; -- Will be replaced with actual table creation

PRINT 'ERR_MON_CustMasterSchedule_Subitems created successfully.'
GO

-- ====================================================
-- Phase 3: Create Tracking Tables
-- ====================================================

-- 3.1 Batch processing tracking table
PRINT 'Creating MON_BatchProcessing...'
GO

DROP TABLE IF EXISTS [dbo].[MON_BatchProcessing];

EXEC sp_executesql N'$(batch_tracking_table_sql)'; -- Will be replaced with actual table creation

PRINT 'MON_BatchProcessing created successfully.'
GO

-- ====================================================
-- Phase 4: Create Views
-- ====================================================

-- 4.1 Active batches monitoring view
PRINT 'Creating VW_MON_ActiveBatches...'
GO

DROP VIEW IF EXISTS [dbo].[VW_MON_ActiveBatches];

EXEC sp_executesql N'$(active_batches_view_sql)'; -- Will be replaced with actual view creation

PRINT 'VW_MON_ActiveBatches created successfully.'
GO

-- ====================================================
-- Phase 5: Create Utility Stored Procedures
-- ====================================================

-- 5.1 Cleanup procedure for completed batches
PRINT 'Creating utility stored procedures...'
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_MON_CleanupCompletedBatches]
    @DaysToKeep INT = 7
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @CutoffDate DATETIME2 = DATEADD(DAY, -@DaysToKeep, GETDATE());
    DECLARE @DeletedBatches INT = 0;
    DECLARE @DeletedStaging INT = 0;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Delete old completed staging records
        DELETE FROM [dbo].[STG_MON_CustMasterSchedule_Subitems]
        WHERE [stg_status] = 'PROMOTED' 
          AND [stg_processed_date] < @CutoffDate;
        
        SET @DeletedStaging = @@ROWCOUNT;
        
        DELETE FROM [dbo].[STG_MON_CustMasterSchedule]
        WHERE [stg_status] = 'PROMOTED' 
          AND [stg_processed_date] < @CutoffDate;
        
        SET @DeletedStaging = @DeletedStaging + @@ROWCOUNT;
        
        -- Delete old completed batch records
        DELETE FROM [dbo].[MON_BatchProcessing]
        WHERE [status] IN ('COMPLETED', 'FAILED')
          AND [end_time] < @CutoffDate;
        
        SET @DeletedBatches = @@ROWCOUNT;
        
        COMMIT TRANSACTION;
        
        PRINT CONCAT('Cleanup completed. Deleted ', @DeletedBatches, ' batch records and ', @DeletedStaging, ' staging records.');
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END
GO

-- 5.2 Batch status summary procedure
CREATE OR ALTER PROCEDURE [dbo].[sp_MON_GetBatchSummary]
    @CustomerName NVARCHAR(100) = NULL,
    @DaysBack INT = 7
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartDate DATETIME2 = DATEADD(DAY, -@DaysBack, GETDATE());
    
    SELECT 
        [customer_name],
        [batch_type],
        COUNT(*) as total_batches,
        SUM(CASE WHEN [status] = 'COMPLETED' THEN 1 ELSE 0 END) as completed_batches,
        SUM(CASE WHEN [status] = 'FAILED' THEN 1 ELSE 0 END) as failed_batches,
        SUM(CASE WHEN [status] NOT IN ('COMPLETED', 'FAILED') THEN 1 ELSE 0 END) as active_batches,
        SUM([total_records]) as total_records_processed,
        SUM([successful_records]) as total_successful_records,
        SUM([failed_records]) as total_failed_records,
        AVG([duration_seconds]) as avg_duration_seconds
    FROM [dbo].[MON_BatchProcessing]
    WHERE [start_time] >= @StartDate
      AND (@CustomerName IS NULL OR [customer_name] = @CustomerName)
    GROUP BY [customer_name], [batch_type]
    ORDER BY [customer_name], [batch_type];
END
GO

PRINT 'All database objects created successfully!'
PRINT 'Phase 1 (Database Schema Setup) - COMPLETED ✓'
GO

-- ====================================================
-- Verification Queries
-- ====================================================
PRINT 'Running verification queries...'
GO

-- Check that all tables were created
SELECT 
    'STG_MON_CustMasterSchedule' as table_name,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule'

UNION ALL

SELECT 
    'STG_MON_CustMasterSchedule_Subitems' as table_name,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'STG_MON_CustMasterSchedule_Subitems'

UNION ALL

SELECT 
    'ERR_MON_CustMasterSchedule' as table_name,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ERR_MON_CustMasterSchedule'

UNION ALL

SELECT 
    'ERR_MON_CustMasterSchedule_Subitems' as table_name,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ERR_MON_CustMasterSchedule_Subitems'

UNION ALL

SELECT 
    'MON_BatchProcessing' as table_name,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'MON_BatchProcessing';

-- Check indexes
SELECT 
    OBJECT_NAME(i.object_id) as table_name,
    i.name as index_name,
    i.type_desc
FROM sys.indexes i
WHERE OBJECT_NAME(i.object_id) LIKE '%STG_MON%' 
   OR OBJECT_NAME(i.object_id) LIKE '%ERR_MON%'
   OR OBJECT_NAME(i.object_id) LIKE '%MON_BatchProcessing%'
ORDER BY table_name, index_name;

PRINT 'Database schema verification completed!'
GO
