# Azure SQL DDL Extraction using sqlcmd
# This script connects to Azure SQL and extracts table DDL

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerName,
    
    [Parameter(Mandatory=$true)]
    [string]$DatabaseName,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [string]$TableName = "",
    [string]$SchemaName = "dbo",
    [string]$OutputDir = ".\ddl_output"
)

Write-Host "🔧 Azure SQL DDL Extraction Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Create output directory
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "📁 Created output directory: $OutputDir" -ForegroundColor Green
}

# Build connection string for sqlcmd
$ConnectionParams = @(
    "-S", $ServerName
    "-d", $DatabaseName
    "-U", $Username
    "-P", $Password
    "-N"  # Encrypt connection
    "-l", "30"  # Login timeout
)

# Function to execute SQL and save results
function Invoke-SqlQuery {
    param(
        [string]$Query,
        [string]$OutputFile
    )
    
    try {
        $TempFile = [System.IO.Path]::GetTempFileName()
        $Query | Out-File -FilePath $TempFile -Encoding UTF8
        
        $Result = & sqlcmd @ConnectionParams -i $TempFile -o $OutputFile -W -s "|" -h -1
        
        Remove-Item $TempFile -Force
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Query executed successfully: $OutputFile" -ForegroundColor Green
        } else {
            Write-Host "❌ Query failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Error executing query: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 1. Get list of tables
$TablesQuery = @"
SELECT 
    TABLE_SCHEMA + '.' + TABLE_NAME AS FullTableName,
    TABLE_SCHEMA,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
$(if ($TableName) { "AND TABLE_NAME = '$TableName'" })
$(if ($SchemaName -ne "dbo") { "AND TABLE_SCHEMA = '$SchemaName'" })
ORDER BY TABLE_SCHEMA, TABLE_NAME;
"@

Write-Host "📋 Getting table list..." -ForegroundColor Yellow
Invoke-SqlQuery -Query $TablesQuery -OutputFile "$OutputDir\table_list.txt"

# 2. For each table, generate DDL
$TableListFile = "$OutputDir\table_list.txt"
if (Test-Path $TableListFile) {
    $Tables = Get-Content $TableListFile | Where-Object { $_ -and $_ -notmatch "^-+$" -and $_ -notmatch "FullTableName" }
    
    foreach ($TableLine in $Tables) {
        if ($TableLine.Trim()) {
            $Parts = $TableLine.Split('|')
            if ($Parts.Count -ge 3) {
                $FullName = $Parts[0].Trim()
                $Schema = $Parts[1].Trim()
                $Table = $Parts[2].Trim()
                
                Write-Host "🔄 Processing table: $FullName" -ForegroundColor Yellow
                
                # Generate CREATE TABLE statement
                $DDLQuery = @"
DECLARE @TableName NVARCHAR(128) = '$Table'
DECLARE @SchemaName NVARCHAR(128) = '$Schema'
DECLARE @SQL NVARCHAR(MAX) = ''

-- Build CREATE TABLE statement
SELECT @SQL = 'CREATE TABLE [' + @SchemaName + '].[' + @TableName + '] (' + CHAR(13) +
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

-- Get Primary Key
PRINT ''
PRINT '-- Primary Key'
SELECT 'ALTER TABLE [' + @SchemaName + '].[' + @TableName + '] ADD CONSTRAINT [' + tc.CONSTRAINT_NAME + '] PRIMARY KEY (' +
       STRING_AGG('[' + kcu.COLUMN_NAME + ']', ', ') + ');'
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE tc.TABLE_SCHEMA = @SchemaName AND tc.TABLE_NAME = @TableName AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
GROUP BY tc.CONSTRAINT_NAME

-- Get Indexes
PRINT ''
PRINT '-- Indexes'
SELECT 'CREATE ' + 
       CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
       'INDEX [' + i.name + '] ON [' + @SchemaName + '].[' + @TableName + '] (' +
       STRING_AGG('[' + c.name + ']', ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) + ');'
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
INNER JOIN sys.tables t ON i.object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = @SchemaName AND t.name = @TableName
AND i.is_primary_key = 0 AND i.type > 0
GROUP BY i.name, i.is_unique
ORDER BY i.name
"@
                
                $OutputFile = "$OutputDir\$($FullName.Replace('.', '_'))_ddl.sql"
                Invoke-SqlQuery -Query $DDLQuery -OutputFile $OutputFile
            }
        }
    }
}

Write-Host ""
Write-Host "🎉 DDL extraction complete!" -ForegroundColor Green
Write-Host "📁 Files saved to: $OutputDir" -ForegroundColor Cyan

# Example usage comment
Write-Host ""
Write-Host "Example usage:" -ForegroundColor Yellow
Write-Host ".\extract_ddl.ps1 -ServerName 'your-server.database.windows.net' -DatabaseName 'YourDB' -Username 'admin' -Password 'YourPassword'" -ForegroundColor Gray
