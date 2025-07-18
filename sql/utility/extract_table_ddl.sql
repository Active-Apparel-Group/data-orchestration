-- Quick DDL extraction queries for Azure SQL
-- Run these directly in SSMS, Azure Data Studio, or sqlcmd

-- 1. Get all table names in database
SELECT 
    TABLE_SCHEMA,
    TABLE_NAME,
    TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME;

-- 2. Get detailed column information for a specific table
-- Replace 'YourTableName' with actual table name
DECLARE @TableName NVARCHAR(128) = 'YourTableName'
DECLARE @SchemaName NVARCHAR(128) = 'dbo'

SELECT 
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.NUMERIC_PRECISION,
    c.NUMERIC_SCALE,
    c.IS_NULLABLE,
    c.COLUMN_DEFAULT,
    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END AS IS_PRIMARY_KEY
FROM INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN (
    SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
    INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
        ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
        AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
    AND c.TABLE_NAME = pk.TABLE_NAME 
    AND c.COLUMN_NAME = pk.COLUMN_NAME
WHERE c.TABLE_SCHEMA = @SchemaName AND c.TABLE_NAME = @TableName
ORDER BY c.ORDINAL_POSITION;

-- 3. Get indexes for a table
SELECT 
    i.name AS index_name,
    i.is_unique,
    i.type_desc,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
INNER JOIN sys.tables t ON i.object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = @SchemaName 
AND t.name = @TableName
AND i.is_primary_key = 0  -- Exclude primary key
AND i.type > 0  -- Exclude heaps
GROUP BY i.name, i.is_unique, i.type_desc
ORDER BY i.name;

-- 4. Get foreign key constraints
SELECT 
    fk.name AS foreign_key_name,
    SCHEMA_NAME(tp.schema_id) AS parent_schema,
    tp.name AS parent_table,
    cp.name AS parent_column,
    SCHEMA_NAME(tr.schema_id) AS referenced_schema,
    tr.name AS referenced_table,
    cr.name AS referenced_column
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
WHERE SCHEMA_NAME(tp.schema_id) = @SchemaName AND tp.name = @TableName
ORDER BY fk.name, fkc.constraint_column_id;

-- 5. Generate CREATE TABLE statement for any table
-- This creates a more complete DDL script
DECLARE @SQL NVARCHAR(MAX) = ''

SELECT @SQL = @SQL + 
    'CREATE TABLE [' + @SchemaName + '].[' + @TableName + '] (' + CHAR(13) +
    STUFF((
        SELECT CHAR(13) + '    ,' + 
               '[' + COLUMN_NAME + '] ' + 
               DATA_TYPE + 
               CASE 
                   WHEN DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar') 
                   THEN CASE WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN '(MAX)' 
                             ELSE '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + ')' END
                   WHEN DATA_TYPE IN ('decimal', 'numeric') 
                   THEN '(' + CAST(NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(NUMERIC_SCALE AS VARCHAR) + ')'
                   ELSE ''
               END +
               CASE WHEN IS_NULLABLE = 'NO' THEN ' NOT NULL' ELSE ' NULL' END +
               CASE WHEN COLUMN_DEFAULT IS NOT NULL THEN ' DEFAULT ' + COLUMN_DEFAULT ELSE '' END
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = @SchemaName AND TABLE_NAME = @TableName
        ORDER BY ORDINAL_POSITION
        FOR XML PATH(''), TYPE
    ).value('.', 'NVARCHAR(MAX)'), 1, 6, '    ') +
    CHAR(13) + ');'

PRINT @SQL
