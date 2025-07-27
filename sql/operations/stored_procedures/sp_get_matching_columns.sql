CREATE OR ALTER PROCEDURE sp_get_matching_columns
    @table1 NVARCHAR(128),
    @table2 NVARCHAR(128)
AS
BEGIN
    SET NOCOUNT ON;

    -- Get columns for both tables with ordinal position, excluding uniqueidentifier columns
    WITH t1_cols AS (
        SELECT 
            COLUMN_NAME, 
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = @table1
          AND DATA_TYPE <> 'uniqueidentifier'
    ),
    t2_cols AS (
        SELECT 
            COLUMN_NAME, 
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = @table2
          AND DATA_TYPE <> 'uniqueidentifier'
    )
    SELECT 
        t1.COLUMN_NAME,
        t1.ORDINAL_POSITION AS Table1_Ordinal,
        t2.ORDINAL_POSITION AS Table2_Ordinal
    FROM t1_cols t1
    INNER JOIN t2_cols t2
        ON t1.COLUMN_NAME = t2.COLUMN_NAME
    ORDER BY t1.ORDINAL_POSITION ASC;
    END

EXEC sp_get_matching_columns 'swp_ORDER_LIST_SYNC', 'FACT_ORDER_LIST';