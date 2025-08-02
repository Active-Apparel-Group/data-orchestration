/*=============================================================
  Helper: drop & rebuild commonly-used row-store indexes
  • Edit the @IndexColumns list only ➜ names & SQL are derived
==============================================================*/
CREATE OR ALTER PROCEDURE dbo.usp_OrderList_BuildIndexes
    @SyncTable   sysname,
    @IndexJson   nvarchar(max) = NULL  -- optional: pass JSON array; otherwise use default list
AS
BEGIN
    SET NOCOUNT ON;

    /*----------------------------------------------------------
      1️⃣  Define the column sets
          – Either use the supplied JSON array OR a hard-coded list
          – Each list item is a comma-separated column string, e.g.
              "[AAG ORDER NUMBER]"   (single)
              "[AAG ORDER NUMBER],[PO NUMBER]"  (composite)
    ----------------------------------------------------------*/
    DECLARE @IndexColumns TABLE (col_list nvarchar(4000));

    IF @IndexJson IS NOT NULL
    BEGIN
        /* Expecting JSON like
            [
              "[AAG ORDER NUMBER]",
              "[PO NUMBER]",
              "[AAG ORDER NUMBER],[PO NUMBER]"
            ]
        */
        INSERT @IndexColumns (col_list)
        SELECT value
        FROM   OPENJSON(@IndexJson);
    END
    ELSE
    BEGIN
        /* ===== Default list – edit freely ===== */
        INSERT @IndexColumns (col_list) VALUES
            (N'[AAG ORDER NUMBER]'),
            (N'[PO NUMBER]'),
            (N'[CUSTOMER NAME]'),
            (N'[SOURCE_CUSTOMER_NAME]'),
            (N'[CUSTOMER STYLE]'),
            (N'[AAG SEASON]'),
            (N'[ORDER TYPE]'),
            (N'[CUSTOMER SEASON]'),
            (N'[AAG ORDER NUMBER],[PO NUMBER]');   -- composite
    END

    /*----------------------------------------------------------
      2️⃣  Generate DROP and CREATE statements dynamically
          – Sanitise column strings to make legal index names
    ----------------------------------------------------------*/
    DECLARE
        @sqlDrop   nvarchar(max) = N'',
        @sqlCreate nvarchar(max) = N'',
        @safeTable nvarchar(128) = QUOTENAME(@SyncTable);

    SELECT
        @sqlDrop   = @sqlDrop + '
        IF EXISTS (SELECT 1 FROM sys.indexes
                   WHERE name = ''' + ix_name + '''
                     AND object_id = OBJECT_ID(''' + @safeTable + ''')) 
            DROP INDEX [' + ix_name + '] ON ' + @safeTable + ';',

        @sqlCreate = @sqlCreate + '
        CREATE INDEX ' + ix_name + ' ON ' + @safeTable + ' (' + col_list + ');'
    FROM (
        SELECT
              col_list,
              'IDX_' + @SyncTable + '_' +
              REPLACE(
                  REPLACE(
                     REPLACE(
                       REPLACE(REPLACE(col_list,'[',''),']','')
                     ,' ','_')
                  ,'/', '_')
              ,',','_')       AS ix_name
        FROM @IndexColumns
    ) q;

    /*----------------------------------------------------------
      3️⃣  Execute
    ----------------------------------------------------------*/
    EXEC (@sqlDrop);
    EXEC (@sqlCreate);
END;
GO