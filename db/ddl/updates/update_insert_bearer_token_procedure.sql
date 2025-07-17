-- Updated stored procedure for log.InsertBearerToken with token_type support
-- This replaces the existing procedure to support multiple token types

-- Drop existing procedure if it exists
IF EXISTS (SELECT 1 FROM sys.procedures WHERE name = 'InsertBearerToken' AND schema_id = SCHEMA_ID('log'))
BEGIN
    DROP PROCEDURE [log].[InsertBearerToken]
    PRINT 'Dropped existing log.InsertBearerToken procedure'
END
GO

-- Create updated stored procedure
CREATE PROCEDURE [log].[InsertBearerToken]
    @bearerToken NVARCHAR(1300),
    @expires_in INT,
    @token_type NVARCHAR(50) = 'power_automate'  -- Default to existing behavior
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @expiresOn DATETIME2(7)
    
    -- Calculate expiration time from current time + expires_in seconds
    SET @expiresOn = DATEADD(SECOND, @expires_in, GETDATE())
    
    -- Insert the token
    INSERT INTO [log].[BearerTokens] (
        [bearerToken],
        [dateRetrieved], 
        [expiresOn],
        [token_type]
    ) VALUES (
        @bearerToken,
        GETDATE(),
        @expiresOn,
        @token_type
    )
    
    -- Return success info
    SELECT 
        @@ROWCOUNT as rows_inserted,
        @expiresOn as expires_on,
        @token_type as token_type
END
GO

PRINT 'Created updated log.InsertBearerToken procedure with token_type support'
GO
