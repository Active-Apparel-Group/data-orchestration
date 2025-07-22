-- Table: dbo.FM_fabric_supplier_moq
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FM_fabric_supplier_moq] (
    [F_SUPPLIER_MOQ_ID] BIGINT NULL,
    [SUPPLIER] NVARCHAR(255) NULL,
    [MOQ_CATEGORY] NVARCHAR(255) NULL,
    [UNIT] NVARCHAR(255) NULL,
    [MOQ_PRICE] NVARCHAR(255) NULL,
    [REMARK] NVARCHAR(255) NULL,
    [CREATOR] NVARCHAR(255) NULL,
    [CREATE_TIME] DATETIME2 NULL,
    [UPDATOR] NVARCHAR(255) NULL,
    [UPDATE_TIME] DATETIME2 NULL,
    [MOQ_CATEGORY_LABEL] NVARCHAR(255) NULL
);
