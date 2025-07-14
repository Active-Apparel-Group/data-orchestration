SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[STG_MON_CustMasterSchedule_Subitems](
	[stg_id] [bigint] IDENTITY(1,1) NOT NULL,
	[stg_batch_id] [nvarchar](50) NOT NULL,
	[stg_parent_stg_id] [bigint] NULL,
	[stg_status] [nvarchar](20) NOT NULL,
	[stg_created_date] [datetime2](7) NOT NULL,
	[stg_processed_date] [datetime2](7) NULL,
	[stg_monday_subitem_id] [bigint] NULL,
	[stg_monday_parent_item_id] [bigint] NULL,
	[stg_error_message] [nvarchar](max) NULL,
	[stg_retry_count] [int] NOT NULL,
	[stg_api_payload] [nvarchar](max) NULL,
	[AAG_ORDER_NUMBER] [nvarchar](50) NULL,
	[STYLE] [nvarchar](100) NULL,
	[COLOR] [nvarchar](100) NULL,
	[PO_NUMBER] [nvarchar](50) NULL,
	[CUSTOMER_ALT_PO] [nvarchar](50) NULL,
	[CUSTOMER] [nvarchar](100) NULL,
	[Size] [nvarchar](10) NOT NULL,
	[ORDER_QTY] [decimal](18, 2) NOT NULL,
	[UNIT_OF_MEASURE] [nvarchar](20) NULL,
	[parent_source_uuid] [uniqueidentifier] NULL,
	[stg_size_label] [nvarchar](100) NULL,
	[stg_monday_subitem_board_id] [bigint] NULL,
	[Order Qty] [nvarchar](max) NULL,
	[Shipped Qty] [nvarchar](max) NULL,
	[Packed Qty] [nvarchar](max) NULL,
	[Cut Qty] [nvarchar](max) NULL,
	[Sew Qty] [nvarchar](max) NULL,
	[Finishing Qty] [nvarchar](max) NULL,
	[Received not Shipped Qty] [nvarchar](max) NULL,
	[ORDER LINE STATUS] [nvarchar](200) NULL,
	[Item ID] [nvarchar](200) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
