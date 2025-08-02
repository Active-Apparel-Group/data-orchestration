/*=============================================================
  dbo.usp_ORDER_LIST_PostStage_Clean   (quote-safe version)
=============================================================*/
CREATE OR ALTER PROCEDURE dbo.usp_ORDER_LIST_PostStage_Clean
    @SourceTable sysname = N'ORDER_LIST',
    @SyncTable   sysname = N'swp_ORDER_LIST_SYNC',
    @BoardID     sysname = N'9609317401'
AS
BEGIN
    SET NOCOUNT, XACT_ABORT ON;

    /* fully-quoted object names ----------------------------------*/
    DECLARE
        @src nvarchar(260) = QUOTENAME(
                               ISNULL(PARSENAME(@SourceTable,2),'dbo'))
                           + '.' +
                           QUOTENAME(PARSENAME(@SourceTable,1)),
        @tgt nvarchar(260) = QUOTENAME(
                               ISNULL(PARSENAME(@SyncTable,2),'dbo'))
                           + '.' +
                           QUOTENAME(PARSENAME(@SyncTable,1)),
        @board nvarchar(260)    = QUOTENAME(@BoardID, '''') ;

    BEGIN TRY
        BEGIN TRAN;

        /* 0️⃣  Re-hydrate ---------------------------------------
        Add Print before each EXEC statement */
        PRINT 'Re-hydrating ' + @tgt + ' from ' + @src + ';';
        
        EXEC (N'IF OBJECT_ID(''' + @tgt + ''',''U'') IS NOT NULL
              DROP TABLE ' + @tgt + ';
              SELECT * INTO ' + @tgt + ' FROM ' + @src + ';');
        



        /* 1️⃣  Delete totally blank rows ------------------------*/
        PRINT 'Deleting rows with all key fields blank from ' + @tgt + ';';

        EXEC (N'DELETE FROM ' + @tgt + '
              WHERE COALESCE([PLANNED DELIVERY METHOD],'''') = ''''
                AND COALESCE([CUSTOMER STYLE],'''')          = ''''
                AND COALESCE([PO NUMBER],'''')               = ''''
                AND COALESCE([CUSTOMER ALT PO],'''')         = ''''
                AND COALESCE([AAG SEASON],'''')              = ''''
                AND COALESCE([CUSTOMER SEASON],'''')         = ''''
                AND COALESCE([CUSTOMER COLOUR DESCRIPTION],'''') = ''''
                AND COALESCE([TOTAL QTY],0) = 0;');

        /* 2️⃣  Fill-down customer name -------------------------*/
        PRINT 'Filling down customer names in ' + @tgt + ';';

        EXEC (N'UPDATE tgt
                 SET [CUSTOMER NAME] = src.fill_name
               FROM ' + @tgt + ' AS tgt
               JOIN v_order_list_customer_name_fill AS src
                 ON src.[_SOURCE_TABLE] = tgt.[_SOURCE_TABLE]
              WHERE tgt.[CUSTOMER NAME] IS NULL
                 OR LTRIM(RTRIM(tgt.[CUSTOMER NAME])) = '''';');

        /* 3️⃣  Source->canonical & mapping ---------------------*/
        PRINT 'Updating canonical customer names in ' + @tgt + ';';

        EXEC (N'UPDATE ' + @tgt + '
                 SET [SOURCE_CUSTOMER_NAME] = [CUSTOMER NAME];');

        EXEC (N'UPDATE tgt
                 SET [CUSTOMER NAME] = map.[canonical]
               FROM ' + @tgt + ' AS tgt
               JOIN canonical_customer_map AS map
                 ON map.[name] = tgt.[SOURCE_CUSTOMER_NAME]
              WHERE tgt.[CUSTOMER NAME] <> map.[canonical];');

        /* 4️⃣  Business rules (group, order-type) --------------*/
        PRINT 'Updating group_name in ' + @tgt + ';';

        EXEC (N'UPDATE ' + @tgt + '
                 SET group_name = CASE
                       WHEN [CUSTOMER SEASON] IS NOT NULL
                             THEN CONCAT([CUSTOMER NAME],'' '',[CUSTOMER SEASON])
                       WHEN [AAG SEASON] IS NOT NULL
                             THEN CONCAT([CUSTOMER NAME],'' '',[AAG SEASON])
                       ELSE ''check'' END
               WHERE group_name IS NULL OR group_name = '''';');

        /* Need to filter this update statement with @Board_id variable */
        PRINT 'Updating group_id in ' + @tgt + ' for board ' + @board + ';';

        EXEC (N'UPDATE s
                 SET group_id = g.group_id
               FROM ' + @tgt + ' AS s
               JOIN MON_Boards_Groups AS g
                 ON s.group_name = g.group_name
              WHERE g.board_id = ' + @board + ';');

        /* Create item_name for Monday.com Board */
        PRINT 'Updating item_name in ' + @tgt + ';';

        EXEC (N'UPDATE ' + @tgt + '
                 SET item_name = 
                    CONCAT(
                        COALESCE([ALIAS/RELATED ITEM], [CUSTOMER STYLE]),'' '',
                        COALESCE([CUSTOMER''S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS], [CUSTOMER COLOUR DESCRIPTION]),'' '',
                        [AAG ORDER NUMBER],'' '',
                        COALESCE([PO NUMBER], [CUSTOMER ALT PO]))
               WHERE item_name IS NULL OR item_name = '''';');

         /* Update Order Type */
        PRINT 'Updating order type in ' + @tgt + ';';
        EXEC (N'UPDATE ' + @tgt + '
                 SET [ORDER TYPE] = ''RECEIVED''
               WHERE [ORDER TYPE] = ''ACTIVE'';');

         /* Update Order Type */
        PRINT 'Updating order type in ' + @tgt + ';';
        EXEC (N'UPDATE ' + @tgt + '
                 SET [ORDER TYPE] = ''CANCELLED''
               WHERE [ORDER TYPE] = ''Cancelled'';');
      

        /* 6️⃣  Indexes -----------------------------------------*/
        EXEC dbo.usp_OrderList_BuildIndexes @SyncTable = @SyncTable;

        COMMIT TRAN;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        DECLARE @msg nvarchar(max) = CONCAT(
               ERROR_MESSAGE(),
               N' (error ', ERROR_NUMBER(),
               N' at line ', ERROR_LINE(), N')');
        RAISERROR(N'usp_ORDER_LIST_PostStage_Clean failed: %s',16,1,@msg);
    END CATCH;
END
GO


