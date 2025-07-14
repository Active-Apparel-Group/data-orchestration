-- Table: dbo.swp_mes_target_table
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[swp_mes_target_table] (
    [MO Number] NVARCHAR(MAX) NULL,
    [style_no] NVARCHAR(MAX) NULL,
    [closed_time_t] NVARCHAR(MAX) NULL,
    [state] NVARCHAR(MAX) NULL,
    [order_number] NVARCHAR(MAX) NULL,
    [prep_number] NVARCHAR(MAX) NULL,
    [cut_number] NVARCHAR(MAX) NULL,
    [sew_number] NVARCHAR(MAX) NULL,
    [finish_number] NVARCHAR(MAX) NULL,
    [sample_number] NVARCHAR(MAX) NULL,
    [defect_number] NVARCHAR(MAX) NULL,
    [remain_number] NVARCHAR(MAX) NULL,
    [cut_fdate] NVARCHAR(MAX) NULL,
    [sew_fdate] NVARCHAR(MAX) NULL,
    [finish_fdate] NVARCHAR(MAX) NULL,
    [customer_name] NVARCHAR(MAX) NULL,
    [customer_no] NVARCHAR(MAX) NULL,
    [Package_scan] NVARCHAR(MAX) NULL,
    [Bucket_Scan] NVARCHAR(MAX) NULL,
    [PNP_Receive] NVARCHAR(MAX) NULL,
    [big_ironing] NVARCHAR(MAX) NULL,
    [WIP_Cut] NVARCHAR(MAX) NULL,
    [WIP_Sew] NVARCHAR(MAX) NULL,
    [WIP_Fin] NVARCHAR(MAX) NULL,
    [FG_Qty] NVARCHAR(MAX) NULL
);
