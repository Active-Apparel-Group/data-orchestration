-- Migration 009: ORDER_LIST API Logging Archival Table
-- Purpose: Create dedicated table for preserving API interaction history from hourly pipeline runs
-- Author: Generated for TASK022 - API Logging Archival System
-- Date: 2025-07-30

USE [ORDERS];  -- Main database
GO

-- =====================================================================================
-- CREATE ORDER_LIST_API_LOG TABLE
-- =====================================================================================
-- Purpose: Store API logging data extracted from main tables after each pipeline run
-- Scope: Preserve API interaction history for troubleshooting and audit trail
-- Strategy: Lightweight table with essential fields for efficient archival and retrieval

CREATE TABLE dbo.ORDER_LIST_API_LOG (
    -- Primary Key and Identification
    [id] BIGINT IDENTITY(1,1) NOT NULL,
    [record_uuid] UNIQUEIDENTIFIER NOT NULL,
    [source] NVARCHAR(20) NOT NULL,  -- 'HEADER' or 'LINE' to distinguish data source
    
    -- Sync State Tracking
    [sync_state] NVARCHAR(20) NULL,
    [sync_completed_at] DATETIME2 NULL,
    
    -- API Logging Data (from main tables)
    [api_request_payload] NVARCHAR(MAX) NULL,
    [api_response_payload] NVARCHAR(MAX) NULL,
    [api_request_timestamp] DATETIME2 NULL,
    [api_response_timestamp] DATETIME2 NULL,
    [api_operation_type] NVARCHAR(50) NULL,
    [api_status] NVARCHAR(20) NULL,
    
    -- Archival Metadata
    [archived_at] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [pipeline_run_id] NVARCHAR(50) NULL,  -- For identifying specific pipeline runs
    
    -- Constraints
    CONSTRAINT PK_ORDER_LIST_API_LOG PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT CK_ORDER_LIST_API_LOG_SOURCE CHECK ([source] IN ('HEADER', 'LINE'))
);

-- =====================================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- =====================================================================================

-- Index for record_uuid lookups (primary access pattern)
CREATE INDEX IX_ORDER_LIST_API_LOG_RECORD_UUID 
ON dbo.ORDER_LIST_API_LOG ([record_uuid]);

-- Index for date-based queries and cleanup operations
CREATE INDEX IX_ORDER_LIST_API_LOG_ARCHIVED_AT 
ON dbo.ORDER_LIST_API_LOG ([archived_at]);

-- Index for filtering by source type
CREATE INDEX IX_ORDER_LIST_API_LOG_SOURCE 
ON dbo.ORDER_LIST_API_LOG ([source]);

-- Composite index for pipeline run analysis
CREATE INDEX IX_ORDER_LIST_API_LOG_PIPELINE_RUN 
ON dbo.ORDER_LIST_API_LOG ([pipeline_run_id], [archived_at]);

-- Index for API status analysis
CREATE INDEX IX_ORDER_LIST_API_LOG_API_STATUS 
ON dbo.ORDER_LIST_API_LOG ([api_status], [api_operation_type]);

-- =====================================================================================
-- ADD DESCRIPTION AND METADATA
-- =====================================================================================

-- Add table description
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'API Logging Archival Table - Preserves Monday.com API interaction history from hourly pipeline runs for troubleshooting and audit trails',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG';

-- Add column descriptions
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Primary key for archival record', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'UUID linking to original record in FACT_ORDER_LIST or ORDER_LIST_LINES', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'record_uuid';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Source of API logging data: HEADER (from FACT_ORDER_LIST) or LINE (from ORDER_LIST_LINES)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'source';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Sync state at time of archival (PENDING, COMPLETED, ERROR, etc.)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'sync_state';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when sync was completed for this record', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'sync_completed_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'JSON payload sent to Monday.com API', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'api_request_payload';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'JSON response received from Monday.com API', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'api_response_payload';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when API request was sent', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'api_request_timestamp';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when API response was received', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'api_response_timestamp';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Type of Monday.com API operation (create_item, create_subitem, update_item, etc.)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'api_operation_type';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'API operation status (SUCCESS, ERROR, TIMEOUT, etc.)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'api_status';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Timestamp when this record was archived from main tables', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'archived_at';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Identifier for specific pipeline run (for grouping related API operations)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'ORDER_LIST_API_LOG', @level2type = N'COLUMN', @level2name = N'pipeline_run_id';

PRINT 'ORDER_LIST_API_LOG table created successfully with indexes and metadata.';

-- =====================================================================================
-- VALIDATION QUERIES
-- =====================================================================================

-- Verify table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ORDER_LIST_API_LOG'
ORDER BY ORDINAL_POSITION;

-- Verify indexes
SELECT 
    i.name AS index_name,
    i.type_desc AS index_type,
    STRING_AGG(c.name, ', ') AS columns
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.ORDER_LIST_API_LOG')
GROUP BY i.name, i.type_desc
ORDER BY i.name;

PRINT 'Table validation completed.';
