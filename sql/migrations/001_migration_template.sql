-- Migration: 001_initial_schema_example
-- Database: ORDERS
-- Description: Example migration script template
-- Author: [Your Name]
-- Date: YYYY-MM-DD
-- JIRA/Issue: [Ticket Number]
-- =============================================================================
-- MIGRATION: Forward Script
-- =============================================================================
BEGIN TRANSACTION;

-- Add your DDL changes here
-- Examples:
-- 1. Create new table
/*
CREATE TABLE [dbo].[new_table] (
[id] INT IDENTITY(1,1) PRIMARY KEY,
[name] NVARCHAR(255) NOT NULL,
[created_date] DATETIME2 DEFAULT GETDATE()
);
 */
-- 2. Add new column
/*
ALTER TABLE [dbo].[existing_table] 
ADD [new_column] NVARCHAR(100) NULL;
 */
-- 3. Create index
/*
CREATE INDEX [IX_table_column] 
ON [dbo].[table_name] ([column_name]);
 */
-- 4. Add constraint
/*
ALTER TABLE [dbo].[table_name]
ADD CONSTRAINT [CK_table_constraint] 
CHECK ([column_name] IN ('value1', 'value2'));
 */
-- Verify migration
SELECT
    'Migration 001 completed successfully' AS Status;

COMMIT TRANSACTION;

-- =============================================================================
-- ROLLBACK: Reverse Script (if needed)
-- =============================================================================
/*
BEGIN TRANSACTION;

-- Reverse the changes in opposite order
-- Example rollback:

-- DROP CONSTRAINT [CK_table_constraint];
-- DROP INDEX [IX_table_column] ON [dbo].[table_name];
-- ALTER TABLE [dbo].[existing_table] DROP COLUMN [new_column];
-- DROP TABLE [dbo].[new_table];

SELECT 'Migration 001 rolled back successfully' AS Status;

COMMIT TRANSACTION;
 */
-- =============================================================================
-- NOTES
-- =============================================================================
/*
1. Always test in development environment first
2. Take backup before running in production
3. Verify data integrity after migration
4. Update documentation and DDL files after successful migration
5. Notify team of schema changes
 */