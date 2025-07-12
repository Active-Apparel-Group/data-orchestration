"""
Generate Complete ORDER_LIST Hybrid Transformation
Purpose: Auto-generate all 406 columns and 45 table unions for hybrid transformation
Author: Data Engineering Team
Date: July 8, 2025
"""
import sys
from pathlib import Path

def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

def get_order_list_schema():
    """Get complete ORDER_LIST schema with data types"""
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'ORDER_LIST'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'data_type': row[1],
                'max_length': row[2],
                'precision': row[3],
                'scale': row[4],
                'nullable': row[5] == 'YES'
            })
        return columns

def get_raw_tables():
    """Get all raw tables from extract layer"""
    with db.get_connection('orders') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME LIKE 'x%_ORDER_LIST_RAW'
            ORDER BY TABLE_NAME
        """)
        return [row[0] for row in cursor.fetchall()]

def generate_column_transformation(column):
    """Generate SQL transformation for a specific column based on data type"""
    col_name = column['name']
    data_type = column['data_type'].lower()
    
    if data_type in ['varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext']:
        # String columns
        return f"NULLIF(TRIM([{col_name}]), '') AS [{col_name}]"
    
    elif data_type in ['int', 'bigint', 'smallint', 'tinyint']:
        # Integer columns
        return f"""CASE 
                WHEN ISNUMERIC([{col_name}]) = 1 
                AND TRY_CAST([{col_name}] AS INT) BETWEEN -2147483648 AND 2147483647
                THEN TRY_CAST([{col_name}] AS INT)
                ELSE NULL
            END AS [{col_name}]"""
    
    elif data_type in ['date', 'datetime', 'datetime2', 'smalldatetime']:
        # Date columns
        return f"""COALESCE(
                TRY_CONVERT(DATE, [{col_name}], 101),  -- MM/DD/YYYY
                TRY_CONVERT(DATE, [{col_name}], 103),  -- DD/MM/YYYY
                TRY_CONVERT(DATE, [{col_name}], 120)   -- YYYY-MM-DD
            ) AS [{col_name}]"""
    
    elif data_type in ['decimal', 'numeric', 'float', 'real', 'money', 'smallmoney']:
        # Decimal/numeric columns
        precision = column.get('precision', 18)
        scale = column.get('scale', 4)
        return f"""CASE 
                WHEN TRY_CAST([{col_name}] AS DECIMAL({precision},{scale})) IS NOT NULL
                AND ABS(TRY_CAST([{col_name}] AS DECIMAL({precision},{scale}))) < 1e15
                THEN TRY_CAST([{col_name}] AS DECIMAL({precision},{scale}))
                ELSE NULL
            END AS [{col_name}]"""
    
    else:
        # Default - treat as string
        return f"NULLIF(TRIM([{col_name}]), '') AS [{col_name}]"

def generate_error_tracking(columns):
    """Generate error tracking for conversion failures"""
    error_cases = []
    
    for column in columns:
        col_name = column['name']
        data_type = column['data_type'].lower()
        
        if data_type in ['int', 'bigint', 'smallint', 'tinyint']:
            error_cases.append(f"""CASE WHEN [{col_name}] IS NOT NULL AND TRY_CAST([{col_name}] AS INT) IS NULL 
                     THEN '{col_name}:' + CAST([{col_name}] AS NVARCHAR(50)) END""")
        
        elif data_type in ['date', 'datetime', 'datetime2', 'smalldatetime']:
            error_cases.append(f"""CASE WHEN [{col_name}] IS NOT NULL 
                     AND COALESCE(TRY_CONVERT(DATE, [{col_name}], 101), TRY_CONVERT(DATE, [{col_name}], 103), TRY_CONVERT(DATE, [{col_name}], 120)) IS NULL 
                     THEN '{col_name}:' + CAST([{col_name}] AS NVARCHAR(50)) END""")
        
        elif data_type in ['decimal', 'numeric', 'float', 'real', 'money', 'smallmoney']:
            precision = column.get('precision', 18)
            scale = column.get('scale', 4)
            error_cases.append(f"""CASE WHEN [{col_name}] IS NOT NULL 
                     AND TRY_CAST([{col_name}] AS DECIMAL({precision},{scale})) IS NULL
                     THEN '{col_name}:' + CAST([{col_name}] AS NVARCHAR(50)) END""")
    
    return "CONCAT_WS('|',\\n                " + ",\\n                ".join(error_cases) + "\\n            ) AS _conversion_errors"

def generate_table_union(raw_tables):
    """Generate UNION ALL for all raw tables"""
    unions = []
    for table in raw_tables:
        unions.append(f"SELECT * FROM dbo.{table} WHERE [AAG ORDER NUMBER] IS NOT NULL")
    
    return "\\n            UNION ALL\\n            ".join(unions)

def generate_complete_hybrid_procedure():
    """Generate the complete hybrid transformation procedure"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("Generating complete hybrid transformation procedure...")
    
    # Get schema and tables
    columns = get_order_list_schema()
    raw_tables = get_raw_tables()
    
    logger.info(f"Found {len(columns)} columns in ORDER_LIST schema")
    logger.info(f"Found {len(raw_tables)} raw tables from extract layer")
    
    # Generate transformations
    column_transformations = []
    column_names_insert = []
    column_names_select = []
    
    for column in columns:
        col_name = column['name']
        if col_name not in ['_SOURCE_FILE', '_EXTRACTED_AT', '_SHEET_NAME']:  # Skip metadata columns
            column_transformations.append(generate_column_transformation(column))
            column_names_insert.append(f"[{col_name}]")
            column_names_select.append(f"[{col_name}]")
    
    # Generate components
    transformations_sql = ",\\n            ".join(column_transformations)
    error_tracking_sql = generate_error_tracking(columns)
    table_union_sql = generate_table_union(raw_tables)
    column_insert_sql = ",\\n        ".join(column_names_insert)
    column_select_sql = ",\\n        ".join(column_names_select)
    
    # Write complete procedure
    procedure_sql = f"""-- order_list_transform_complete.sql
-- PURPOSE: Complete auto-generated hybrid transformation for ORDER_LIST
-- GENERATED: {len(columns)} columns, {len(raw_tables)} tables
-- DATE: July 8, 2025

CREATE OR ALTER PROCEDURE dbo.sp_Transform_OrderList_Customer_Hybrid_Complete
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Create error tracking table if it doesn't exist
    IF OBJECT_ID('dbo.ORDER_LIST_TRANSFORM_ERRORS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ORDER_LIST_TRANSFORM_ERRORS (
            source_table NVARCHAR(128),
            error_data NVARCHAR(MAX),
            conversion_errors NVARCHAR(MAX),
            error_date DATETIME2 DEFAULT GETDATE()
        );
    END
    
    -- 1. Create temp table with same schema as ORDER_LIST (HYBRID APPROACH)
    SELECT * INTO #ORDER_LIST_TRANSFORM 
    FROM dbo.ORDER_LIST WHERE 1=0;
    
    -- 2. Single-pass transformation with error tracking (ALL {len(columns)} COLUMNS)
    WITH TransformedData AS (
        SELECT 
            {transformations_sql},
            
            -- Track conversion errors for all columns
            {error_tracking_sql}
            
        FROM (
            -- Union all {len(raw_tables)} raw tables
            {table_union_sql}
        ) raw
    )
    
    -- 3. Insert successful transformations into temp table
    INSERT INTO #ORDER_LIST_TRANSFORM (
        {column_insert_sql}
    )
    SELECT 
        {column_select_sql}
    FROM TransformedData
    WHERE _conversion_errors = '' OR _conversion_errors IS NULL;
    
    -- 4. Log problematic records
    INSERT INTO dbo.ORDER_LIST_TRANSFORM_ERRORS (source_table, error_data, conversion_errors)
    SELECT 
        'MULTIPLE_RAW_TABLES',
        LEFT(CAST([AAG ORDER NUMBER] AS NVARCHAR(MAX)), 100),
        _conversion_errors
    FROM TransformedData
    WHERE _conversion_errors != '' AND _conversion_errors IS NOT NULL;
    
    -- 5. Calculate and validate success rate
    DECLARE @TotalRows INT, @SuccessRows INT, @SuccessRate DECIMAL(5,2);
    
    SELECT @TotalRows = COUNT(*) FROM TransformedData;
    SELECT @SuccessRows = COUNT(*) FROM #ORDER_LIST_TRANSFORM;
    SET @SuccessRate = CASE WHEN @TotalRows > 0 THEN 100.0 * @SuccessRows / @TotalRows ELSE 100.0 END;
    
    -- 6. Atomic swap if threshold met (HYBRID APPROACH CORE)
    IF @SuccessRate >= 95.0
    BEGIN
        BEGIN TRANSACTION AtomicSwap;
        
        BEGIN TRY
            -- Backup current ORDER_LIST and perform atomic swap
            IF OBJECT_ID('dbo.ORDER_LIST_OLD', 'U') IS NOT NULL
                DROP TABLE dbo.ORDER_LIST_OLD;
                
            EXEC sp_rename 'dbo.ORDER_LIST', 'ORDER_LIST_OLD';
            
            -- Create new ORDER_LIST from temp table
            SELECT * INTO dbo.ORDER_LIST_NEW FROM #ORDER_LIST_TRANSFORM;
            EXEC sp_rename 'dbo.ORDER_LIST_NEW', 'ORDER_LIST';
            
            COMMIT TRANSACTION AtomicSwap;
            
            -- Return success results
            SELECT 
                @TotalRows AS total_rows_processed,
                @SuccessRows AS successful_rows,
                @SuccessRate AS success_rate_percent,
                'PASSED' AS validation_status,
                'ATOMIC_SWAP_COMPLETED' AS operation_status;
                
        END TRY
        BEGIN CATCH
            ROLLBACK TRANSACTION AtomicSwap;
            
            DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
            
            -- Return failure with error details
            SELECT 
                @TotalRows AS total_rows_processed,
                @SuccessRows AS successful_rows,
                @SuccessRate AS success_rate_percent,
                'FAILED' AS validation_status,
                'ATOMIC_SWAP_FAILED: ' + @ErrorMessage AS operation_status;
                
            RAISERROR('Atomic swap failed: %s', 16, 1, @ErrorMessage);
        END CATCH
    END
    ELSE
    BEGIN
        -- Return failure - success rate too low
        SELECT 
            @TotalRows AS total_rows_processed,
            @SuccessRows AS successful_rows,
            @SuccessRate AS success_rate_percent,
            'FAILED' AS validation_status,
            'SUCCESS_RATE_TOO_LOW' AS operation_status;
            
        RAISERROR('Transform success rate %.2f%% below 95%% threshold', 16, 1, @SuccessRate);
    END
END
GO
"""
    
    # Write to file
    output_file = repo_root / "sql" / "transformations" / "order_list_transform_complete.sql"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(procedure_sql)
    
    logger.info(f"Generated complete hybrid procedure: {output_file}")
    logger.info(f"✅ {len(columns)} columns with type-specific transformations")
    logger.info(f"✅ {len(raw_tables)} raw tables in UNION ALL")
    logger.info(f"✅ Complete error tracking for all conversions")
    logger.info(f"✅ Atomic swap with rollback capabilities")
    
    return str(output_file)

def main():
    """Generate the complete hybrid transformation procedure"""
    print("🚀 GENERATING COMPLETE ORDER_LIST HYBRID TRANSFORMATION")
    print("=" * 60)
    
    try:
        output_file = generate_complete_hybrid_procedure()
        print(f"\\n✅ SUCCESS: Generated complete hybrid procedure")
        print(f"📁 File: {output_file}")
        print(f"\\n🎯 Next Steps:")
        print(f"1. Review the generated SQL procedure")
        print(f"2. Deploy to database for testing")
        print(f"3. Update Python orchestrator to call hybrid procedure")
        print(f"4. Validate against Python results")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
