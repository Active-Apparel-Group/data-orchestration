-- =====================================================================================
-- SNAPSHOT_ARCHIVE - Parquet Archive Storage in Kestra PostgreSQL
-- =====================================================================================
-- Purpose: Long-term archive storage for ORDERS_UNIFIED snapshots
-- Database: kestra (PostgreSQL)
-- Architecture: Stores compressed Parquet files as BYTEA with metadata
-- =====================================================================================

-- Archive table for long-term storage (PostgreSQL)
CREATE TABLE IF NOT EXISTS snapshot_archive (
    -- Primary key
    archive_id BIGSERIAL PRIMARY KEY,
    
    -- Snapshot metadata
    snapshot_date TIMESTAMP NOT NULL,
    customer_filter VARCHAR(255) NOT NULL DEFAULT 'ALL',
    batch_id UUID,
    records_count INTEGER,
    
    -- Source system reference
    source_database VARCHAR(100) NOT NULL DEFAULT 'ORDERS',
    source_table VARCHAR(255) NOT NULL DEFAULT 'ORDERS_UNIFIED',
    
    -- Parquet storage
    parquet_data BYTEA NOT NULL,  -- Compressed Parquet file
    parquet_size BIGINT,          -- Size in bytes
    compression_ratio DECIMAL(5,2), -- Compression efficiency
    
    -- File metadata
    original_columns INTEGER,     -- Number of columns in source
    schema_hash VARCHAR(64),      -- Schema fingerprint for validation
    file_checksum VARCHAR(64),    -- MD5 checksum of Parquet data
    
    -- Archive metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'data-orchestration',
    retention_until DATE,         -- Automatic cleanup date
    tags JSONB,                   -- Flexible metadata tags
    
    -- Performance indexes
    CONSTRAINT uk_snapshot_archive_unique UNIQUE (snapshot_date, customer_filter, source_table)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_snapshot_archive_date 
    ON snapshot_archive (snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_snapshot_archive_customer 
    ON snapshot_archive (customer_filter, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_snapshot_archive_batch 
    ON snapshot_archive (batch_id) WHERE batch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_snapshot_archive_retention 
    ON snapshot_archive (retention_until) WHERE retention_until IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_snapshot_archive_tags 
    ON snapshot_archive USING GIN (tags) WHERE tags IS NOT NULL;

-- Table documentation
COMMENT ON TABLE snapshot_archive IS 'Long-term archive storage for ORDERS_UNIFIED snapshots in compressed Parquet format';
COMMENT ON COLUMN snapshot_archive.parquet_data IS 'Compressed Parquet file containing full snapshot data';
COMMENT ON COLUMN snapshot_archive.schema_hash IS 'SHA-256 hash of column names and types for schema validation';
COMMENT ON COLUMN snapshot_archive.compression_ratio IS 'Compression ratio (compressed_size / original_size)';
COMMENT ON COLUMN snapshot_archive.tags IS 'Flexible JSON metadata for custom tagging and categorization';

-- =====================================================================================
-- ARCHIVE MANAGEMENT FUNCTIONS
-- =====================================================================================

-- Function to get archive statistics
CREATE OR REPLACE FUNCTION get_archive_statistics(
    p_customer_filter VARCHAR(255) DEFAULT NULL,
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    customer_filter VARCHAR(255),
    snapshot_count BIGINT,
    total_size_mb NUMERIC,
    avg_compression_ratio NUMERIC,
    oldest_snapshot TIMESTAMP,
    newest_snapshot TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa.customer_filter,
        COUNT(*) as snapshot_count,
        ROUND(SUM(sa.parquet_size)::NUMERIC / 1024 / 1024, 2) as total_size_mb,
        ROUND(AVG(sa.compression_ratio), 2) as avg_compression_ratio,
        MIN(sa.snapshot_date) as oldest_snapshot,
        MAX(sa.snapshot_date) as newest_snapshot
    FROM snapshot_archive sa
    WHERE (p_customer_filter IS NULL OR sa.customer_filter = p_customer_filter)
      AND sa.snapshot_date >= CURRENT_TIMESTAMP - INTERVAL '%d days' % p_days_back
    GROUP BY sa.customer_filter
    ORDER BY sa.customer_filter;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old archives
CREATE OR REPLACE FUNCTION cleanup_old_archives(
    p_keep_days INTEGER DEFAULT 90,
    p_dry_run BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    action VARCHAR(10),
    archive_id BIGINT,
    snapshot_date TIMESTAMP,
    customer_filter VARCHAR(255),
    size_mb NUMERIC
) AS $$
DECLARE
    cleanup_date TIMESTAMP;
    deleted_count INTEGER := 0;
BEGIN
    cleanup_date := CURRENT_TIMESTAMP - INTERVAL '%d days' % p_keep_days;
    
    IF p_dry_run THEN
        -- Return what would be deleted
        RETURN QUERY
        SELECT 
            'DELETE'::VARCHAR(10) as action,
            sa.archive_id,
            sa.snapshot_date,
            sa.customer_filter,
            ROUND(sa.parquet_size::NUMERIC / 1024 / 1024, 2) as size_mb
        FROM snapshot_archive sa
        WHERE sa.snapshot_date < cleanup_date
           OR (sa.retention_until IS NOT NULL AND sa.retention_until < CURRENT_DATE)
        ORDER BY sa.snapshot_date;
    ELSE
        -- Actually delete old records
        WITH deleted AS (
            DELETE FROM snapshot_archive 
            WHERE snapshot_date < cleanup_date
               OR (retention_until IS NOT NULL AND retention_until < CURRENT_DATE)
            RETURNING archive_id, snapshot_date, customer_filter, parquet_size
        )
        SELECT 
            'DELETED'::VARCHAR(10) as action,
            d.archive_id,
            d.snapshot_date,
            d.customer_filter,
            ROUND(d.parquet_size::NUMERIC / 1024 / 1024, 2) as size_mb
        FROM deleted d
        ORDER BY d.snapshot_date;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to validate archive integrity
CREATE OR REPLACE FUNCTION validate_archive_integrity(
    p_archive_id BIGINT DEFAULT NULL
)
RETURNS TABLE (
    archive_id BIGINT,
    is_valid BOOLEAN,
    validation_error TEXT,
    file_size_mb NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa.archive_id,
        CASE 
            WHEN sa.parquet_data IS NOT NULL AND LENGTH(sa.parquet_data) > 0 THEN TRUE
            ELSE FALSE
        END as is_valid,
        CASE 
            WHEN sa.parquet_data IS NULL THEN 'Parquet data is NULL'
            WHEN LENGTH(sa.parquet_data) = 0 THEN 'Parquet data is empty'
            WHEN sa.parquet_size != LENGTH(sa.parquet_data) THEN 'Size mismatch'
            ELSE NULL
        END as validation_error,
        ROUND(LENGTH(sa.parquet_data)::NUMERIC / 1024 / 1024, 2) as file_size_mb
    FROM snapshot_archive sa
    WHERE (p_archive_id IS NULL OR sa.archive_id = p_archive_id)
    ORDER BY sa.archive_id;
END;
$$ LANGUAGE plpgsql;
