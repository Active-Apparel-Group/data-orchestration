-- Table: dbo.MES_operational_performance
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[MES_operational_performance] (
    [MO Number] NVARCHAR(255) NULL,
    [style_no] NVARCHAR(255) NULL,
    [closed_time_t] NVARCHAR(255) NULL,
    [state] NVARCHAR(255) NULL,
    [order_number] BIGINT NULL,
    [prep_number] DECIMAL(18,4) NULL,
    [cut_number] BIGINT NULL,
    [sew_number] BIGINT NULL,
    [finish_number] BIGINT NULL,
    [sample_number] BIGINT NULL,
    [defect_number] BIGINT NULL,
    [remain_number] BIGINT NULL,
    [cut_fdate] NVARCHAR(255) NULL,
    [sew_fdate] NVARCHAR(255) NULL,
    [finish_fdate] NVARCHAR(255) NULL,
    [customer_name] NVARCHAR(255) NULL,
    [customer_no] NVARCHAR(255) NULL,
    [Package_scan] DECIMAL(18,4) NULL,
    [Bucket_Scan] DECIMAL(18,4) NULL,
    [PNP_Receive] DECIMAL(18,4) NULL,
    [big_ironing] DECIMAL(18,4) NULL,
    [WIP_Cut] BIGINT NULL,
    [WIP_Sew] BIGINT NULL,
    [WIP_Fin] DECIMAL(18,4) NULL,
    [FG_Qty] DECIMAL(18,4) NULL
);
