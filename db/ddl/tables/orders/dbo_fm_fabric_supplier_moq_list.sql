-- Table: dbo.FM_fabric_supplier_moq_list
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[FM_fabric_supplier_moq_list] (
    [F_SUPPLIER_MOQ_LIST_ID] BIGINT NULL,
    [F_SUPPLIER_MOQ_ID] DECIMAL(18,4) NULL,
    [MOQ_TYPE] NVARCHAR(255) NULL,
    [MOQ_PRICE] DECIMAL(18,4) NULL,
    [REMARK] NVARCHAR(255) NULL,
    [CREATOR] NVARCHAR(255) NULL,
    [CREATE_TIME] DATETIME2 NULL,
    [UPDATOR] NVARCHAR(255) NULL,
    [UPDATE_TIME] DATETIME2 NULL
);
