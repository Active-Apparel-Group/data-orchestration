-- Add token_type column to log.BearerTokens table
-- This allows us to distinguish between Power BI, Power Automate, and other Azure service tokens

-- Check if column already exists
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'log' 
    AND TABLE_NAME = 'BearerTokens' 
    AND COLUMN_NAME = 'token_type'
)
BEGIN
    ALTER TABLE [log].[BearerTokens] 
    ADD [token_type] [nvarchar](50) NOT NULL DEFAULT 'power_automate'
    
    PRINT 'Added token_type column to log.BearerTokens'
END
ELSE
BEGIN
    PRINT 'token_type column already exists in log.BearerTokens'
END
GO

-- Update existing records to have proper token_type
UPDATE [log].[BearerTokens] 
SET [token_type] = 'power_automate' 
WHERE [token_type] = 'power_automate'  -- This is just to trigger the default
GO

PRINT 'log.BearerTokens table updated with token_type column'
GO
