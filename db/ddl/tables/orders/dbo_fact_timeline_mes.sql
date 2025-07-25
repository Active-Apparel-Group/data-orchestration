-- Table: dbo.FACT_timeline_MES
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FACT_timeline_MES] (
    [StyleColorPOID] INT NULL,
    [master_id] BIGINT NULL,
    [customer_no] NVARCHAR(MAX) NULL,
    [style_no] NVARCHAR(100) NULL,
    [color_name] NVARCHAR(MAX) NULL,
    [item_no] NVARCHAR(100) NULL,
    [Season] NVARCHAR(MAX) NULL,
    [Drop] NVARCHAR(100) NULL,
    [AAG Season] NVARCHAR(100) NULL,
    [PO] NVARCHAR(100) NULL,
    [Color] NVARCHAR(100) NULL,
    [customer_name] NVARCHAR(100) NULL,
    [order_no] NVARCHAR(MAX) NULL,
    [factory_name] NVARCHAR(MAX) NULL,
    [group_name] NVARCHAR(MAX) NULL,
    [state] NVARCHAR(MAX) NULL,
    [dept_id] NVARCHAR(MAX) NULL,
    [closed_time] NVARCHAR(MAX) NULL,
    [closed_time_t] NVARCHAR(MAX) NULL,
    [dept_name] NVARCHAR(MAX) NULL,
    [order_number] INT NULL,
    [prep_number] INT NULL,
    [cut_number] INT NULL,
    [sew_number] INT NULL,
    [finish_number] INT NULL,
    [sample_number] INT NULL,
    [defect_number] INT NULL,
    [remain_number] INT NULL,
    [pre_cut] DECIMAL(38,6) NULL,
    [act_cut] DECIMAL(38,6) NULL,
    [return_cut] DECIMAL(38,6) NULL,
    [month_m] INT NULL,
    [week_w] INT NULL,
    [cut_fdate] NVARCHAR(MAX) NULL,
    [sew_fdate] NVARCHAR(MAX) NULL,
    [finish_fdate] NVARCHAR(MAX) NULL,
    [finish_order_rate] FLOAT NULL,
    [finish_cut_rate] FLOAT NULL,
    [wh01] INT NULL,
    [wh02] INT NULL,
    [wh03] INT NULL,
    [wh05] INT NULL,
    [wh07A] INT NULL,
    [wh07B] INT NULL,
    [wh07C] INT NULL,
    [wh07H] INT NULL,
    [wh09A] INT NULL,
    [wh09B] INT NULL,
    [wh09C] INT NULL,
    [wh09H] INT NULL,
    [create_time] DATE NULL,
    [create_time_order] DATE NULL,
    [cut_sdate] NVARCHAR(MAX) NULL,
    [sew_sdate] NVARCHAR(MAX) NULL,
    [finish_sdate] NVARCHAR(MAX) NULL,
    [no_in] INT NULL,
    [style_sort] NVARCHAR(MAX) NULL,
    [Cutting WIP] INT NULL,
    [Sewing WIP] INT NULL,
    [Finishing WIP] INT NULL,
    [work people] INT NULL,
    [Attend Hrs] FLOAT NULL,
    [GSD Hrs prod] FLOAT NULL,
    [eff] DECIMAL(38,6) NULL,
    [work people2] INT NULL,
    [Attend Hrs2] FLOAT NULL,
    [GSD Hrs prod2] FLOAT NULL,
    [eff2] DECIMAL(38,6) NULL,
    [work people3] INT NULL,
    [Attend Hrs3] FLOAT NULL,
    [GSD Hrs prod3] FLOAT NULL,
    [eff3] DECIMAL(38,6) NULL,
    [dress name] NVARCHAR(MAX) NULL,
    [Production type] NVARCHAR(MAX) NULL,
    [Package scan] INT NULL,
    [Bucket Scan] INT NULL,
    [PNP Receive] INT NULL,
    [big_ironing] INT NULL,
    [process_state] INT NULL,
    [abnormal_number] INT NULL,
    [description] NVARCHAR(MAX) NULL,
    [opinion] NVARCHAR(MAX) NULL,
    [applicat_by] NVARCHAR(MAX) NULL,
    [verity_by] NVARCHAR(MAX) NULL,
    [verity_time] DATETIME2 NULL
);
