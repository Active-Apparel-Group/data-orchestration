-- Enhanced API Logging Table - Essential Metrics Only
-- Replaces heavy payload logging with actionable insights

-- Drop existing table if it exists
IF OBJECT_ID('ORDER_LIST_API_LOG_ENHANCED', 'U') IS NOT NULL
    DROP TABLE ORDER_LIST_API_LOG_ENHANCED;

-- Create enhanced API logging table
CREATE TABLE ORDER_LIST_API_LOG_ENHANCED (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    record_uuid VARCHAR(50) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    aag_order_number VARCHAR(50) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_category VARCHAR(50) NULL,
    error_summary VARCHAR(500) NULL,
    retry_count INT DEFAULT 0,
    processing_time_ms INT NULL,
    logged_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    -- Indexes for performance
    INDEX IX_APILogEnhanced_Customer (customer_name, logged_at),
    INDEX IX_APILogEnhanced_Status (status, logged_at),
    INDEX IX_APILogEnhanced_RecordUUID (record_uuid),
    INDEX IX_APILogEnhanced_ErrorCategory (error_category, logged_at)
);

-- Add constraints
ALTER TABLE ORDER_LIST_API_LOG_ENHANCED 
ADD CONSTRAINT CHK_APILogEnhanced_Status 
CHECK (status IN ('SUCCESS', 'ERROR', 'PENDING', 'RETRY'));

ALTER TABLE ORDER_LIST_API_LOG_ENHANCED 
ADD CONSTRAINT CHK_APILogEnhanced_RetryCount 
CHECK (retry_count >= 0 AND retry_count <= 10);

-- Sample data for testing
INSERT INTO ORDER_LIST_API_LOG_ENHANCED (
    record_uuid, customer_name, aag_order_number, operation_type, 
    status, error_category, error_summary, retry_count, processing_time_ms
) VALUES 
('test-001', 'GREYSON', 'PO4755-001', 'async_batch_create_items', 'SUCCESS', NULL, NULL, 0, 1250),
('test-002', 'GREYSON', 'PO4755-002', 'async_batch_create_items', 'ERROR', 'DROPDOWN_VALUE_MISSING', 'Dropdown value not found - needs creation', 1, 2100),
('test-003', 'JOHNNIE O', 'JO2024-001', 'async_batch_create_items', 'SUCCESS', NULL, NULL, 0, 950);

-- Verify table creation
SELECT 
    'Enhanced API Log Table Created' as result,
    COUNT(*) as sample_records
FROM ORDER_LIST_API_LOG_ENHANCED;

-- Show sample records
SELECT TOP 5 * FROM ORDER_LIST_API_LOG_ENHANCED ORDER BY logged_at DESC;

PRINT 'Enhanced API logging table created successfully! 🎯';
