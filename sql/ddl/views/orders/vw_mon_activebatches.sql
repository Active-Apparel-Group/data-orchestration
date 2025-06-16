-- View: dbo.VW_MON_ActiveBatches
-- Database: ORDERS
-- Purpose: Monitoring view for active and recent Monday.com batch processing
-- Dependencies: MON_BatchProcessing table

CREATE VIEW [dbo].[VW_MON_ActiveBatches] AS
SELECT 
    [batch_id],
    [customer_name],
    [batch_type],
    [status],
    [start_time],
    [duration_seconds],
    [total_records],
    [successful_records],
    [failed_records],
    CASE 
        WHEN [total_records] > 0 
        THEN CAST([successful_records] AS FLOAT) / [total_records] * 100
        ELSE 0 
    END AS success_percentage,
    [error_summary]
FROM [dbo].[MON_BatchProcessing]
WHERE [status] NOT IN ('COMPLETED', 'FAILED')
   OR [start_time] >= DATEADD(HOUR, -24, GETDATE()); -- Show recent completed batches too
