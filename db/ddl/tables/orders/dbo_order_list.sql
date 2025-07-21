-- COMPLETE ORDER_LIST SCHEMA
-- Generated from analysis of 45 customer ORDER_LIST tables
-- Includes all three groups with optimized ordering

CREATE TABLE [dbo].[ORDER_LIST] (
    -- Auto-increment primary key
    -- [ID] INT IDENTITY(1,1) PRIMARY KEY,
    -- add uuid instead
    [record_uuid] UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,

    -- GROUP 1: ORDER DETAILS
    [AAG ORDER NUMBER] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [CUSTOMER NAME] NVARCHAR(100) NULL,  -- Coverage: 100.0% (CANONICAL CUSTOMER NAME)
    [SOURCE_CUSTOMER_NAME] NVARCHAR(100) NULL,  -- Original customer name from source files
    [ORDER DATE PO RECEIVED] DATETIME2 NULL,   -- Coverage: 100.0%
    [PO NUMBER] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER ALT PO] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [AAG SEASON] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER SEASON] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [DROP] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [MONTH] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [RANGE / COLLECTION] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CATEGORY] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [PATTERN ID] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [PLANNER] NVARCHAR(500) NULL,  -- Coverage: 100.0%
    [MAKE OR BUY] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [ORIGINAL ALIAS/RELATED ITEM] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [PRICING ALIAS/RELATED ITEM] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [ALIAS/RELATED ITEM] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER STYLE] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [STYLE DESCRIPTION] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [CUSTOMER'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER COLOUR DESCRIPTION] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [INFOR WAREHOUSE CODE] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [BULK AGREEMENT NUMBER] NVARCHAR(255) NULL,  -- Coverage: 64.4%
    [INFOR FACILITY CODE] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [INFOR BUSINESS UNIT AREA] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [BULK AGREEMENT DESCRIPTION] NVARCHAR(255) NULL,  -- Coverage: 64.4%
    [CO NUMBER - INITIAL DISTRO] NVARCHAR(255) NULL,  -- Coverage: 46.7%
    [INFOR CUSTOMER CODE] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [CO NUMBER - ALLOCATION DISTRO] NVARCHAR(255) NULL,  -- Coverage: 46.7%
    [CO NUMBER (INITIAL DISTRO)] NVARCHAR(255) NULL,  -- Coverage: 26.7%
    [CO NUMBER (ALLOCATION DISTRO)] NVARCHAR(255) NULL,  -- Coverage: 26.7%
    [INFOR ORDER TYPE] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [INFOR SEASON CODE] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [ITEM TYPE CODE] NVARCHAR(255) NULL,  -- Coverage: 60.0%
    [PRODUCT GROUP CODE] NVARCHAR(255) NULL,  -- Coverage: 60.0%
    [ITEM GROUP CODE] NVARCHAR(255) NULL,  -- Coverage: 60.0%
    [PLANNER2] NVARCHAR(255) NULL,  -- Coverage: 22.2%
    [GENDER GROUP CODE] NVARCHAR(255) NULL,  -- Coverage: 60.0%
    [FABRIC TYPE CODE] NVARCHAR(255) NULL,  -- Coverage: 60.0%
    [INFOR MAKE/BUY CODE] NVARCHAR(255) NULL,  -- Coverage: 24.4%
    [INFOR ITEM TYPE CODE] NVARCHAR(255) NULL,  -- Coverage: 24.4%
    [INFOR PRODUCT GROUP CODE] NVARCHAR(255) NULL,  -- Coverage: 24.4%
    [INFOR ITEM GROUP CODE] NVARCHAR(255) NULL,  -- Coverage: 24.4%
    [INFOR GENDER GROUP CODE] NVARCHAR(255) NULL,  -- Coverage: 24.4%
    [INFOR FABRIC TYPE CODE] NVARCHAR(255) NULL,  -- Coverage: 24.4%
    [LONGSON ALIAS] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [INFOR COLOUR CODE] NVARCHAR(255) NULL,  -- Coverage: 28.9%
    [FACILITY CODE] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [CUSTOMER CODE] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [Column2] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [Column1] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [AAG SEASON CODE] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [MAKE OR BUY FLAG] NVARCHAR(100) NULL,  -- Coverage: 4.4%
    [MAKE/BUY CODE] NVARCHAR(100) NULL,  -- Coverage: 6.7%
    [UNIT OF MEASURE] NVARCHAR(100) NULL,  -- Coverage: 100.0%

    -- GROUP 2: GARMENT SIZES (All INT for quantity calculations)
    -- Baby Sizes
    [2T] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3T] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [4T] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [5T] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [6T] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    -- Numeric Child
    [0] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [0-3M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [1] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [2] INT NULL,  -- Coverage: 8.9%, CONVERTED from nvarchar
    [2/3] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3/6 MTHS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3-6M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3-4 years] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3-4] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [4] INT NULL,  -- Coverage: 17.8%, CONVERTED from nvarchar
    [4/5] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [04/XXS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [5] INT NULL,  -- Coverage: 8.9%, CONVERTED from nvarchar
    [5-6 years] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [5-6] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [6] INT NULL,  -- Coverage: 20.0%, CONVERTED from nvarchar
    [6-12M] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [6/7] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [6/12 MTHS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [6-9M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [6-10] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [S(6-8)] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [7] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    [7-8 years] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [7-8] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [8] INT NULL,  -- Coverage: 22.2%, CONVERTED from nvarchar
    [08/S] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [8/9] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [M(8-10)] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [9] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [9-12M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [9-10 years] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [9-10] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [10] INT NULL,  -- Coverage: 22.2%, CONVERTED from nvarchar
    [10/M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [10/11] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [10-12] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [M(10-12)] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [L(10-12)] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [11-12 years] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [11-14] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [12] INT NULL,  -- Coverage: 22.2%, CONVERTED from nvarchar
    [12/18 MTHS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [12-18M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [12/L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [12/13] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [12-14] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [13-14 years] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [14] INT NULL,  -- Coverage: 17.8%, CONVERTED from nvarchar
    [L(14-16)] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [16] INT NULL,  -- Coverage: 13.3%, CONVERTED from nvarchar
    -- Adult Sizes
    [XS] INT NULL,  -- Coverage: 100.0%, CONVERTED from nvarchar
    [XS/S] INT NULL,  -- Coverage: 15.6%, CONVERTED from nvarchar
    [XS-PETITE] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [06/XS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [XXS/XS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [CD/XS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [C/XS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [D/XS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [XL] INT NULL,  -- Coverage: 100.0%, CONVERTED from nvarchar
    [L/XL] INT NULL,  -- Coverage: 24.4%, CONVERTED from nvarchar
    [14/XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [L-XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [AB/XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [CD/XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [C/XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [D/XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [XXL] INT NULL,  -- Coverage: 82.2%, CONVERTED from nvarchar
    [2XL] INT NULL,  -- Coverage: 15.6%, CONVERTED from nvarchar
    [XL/XXL] INT NULL,  -- Coverage: 6.7%, CONVERTED from nvarchar
    [16/XXL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [XL/2XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [XXL/3XL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [D/XXL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [3XL] INT NULL,  -- Coverage: 22.2%, CONVERTED from nvarchar
    [4XL] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    -- Numeric Adult
    [18] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    [18/24 MTHS] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [18-24M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [18/XXXL] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [20] INT NULL,  -- Coverage: 8.9%, CONVERTED from nvarchar
    [22] INT NULL,  -- Coverage: 8.9%, CONVERTED from nvarchar
    [24] INT NULL,  -- Coverage: 6.7%, CONVERTED from nvarchar
    [25] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [26] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [27] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [28] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    [28-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [29] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [30-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [31] INT NULL,  -- Coverage: 13.3%, CONVERTED from nvarchar
    [31-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [31-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [31/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [31-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [31/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [32-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32/34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32/36] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [33] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    [33-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [33-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [33/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [33-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [33/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [34-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34/34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [35] INT NULL,  -- Coverage: 8.9%, CONVERTED from nvarchar
    [35-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [35-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [35/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [35-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [35/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [36-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36/34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [38-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38-32L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38/34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38/36] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [40-30L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40-31L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40/32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40/30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [42] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    [43] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [44] INT NULL,  -- Coverage: 6.7%, CONVERTED from nvarchar
    [45] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [46] INT NULL,  -- Coverage: 6.7%, CONVERTED from nvarchar
    [48] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [50] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [52] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [54] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [56] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [58] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [60] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    -- One Size
    [OS] INT NULL,  -- Coverage: 24.4%, CONVERTED from nvarchar
    [ONE SIZE] INT NULL,  -- Coverage: 24.4%, CONVERTED from nvarchar
    [One_Size] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar (renamed to avoid duplicate)
    [One Sz] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    -- Other Sizes
    [S] INT NULL,  -- Coverage: 100.0%, CONVERTED from nvarchar
    [M] INT NULL,  -- Coverage: 100.0%, CONVERTED from nvarchar
    [L] INT NULL,  -- Coverage: 100.0%, CONVERTED from nvarchar
    [XXS] INT NULL,  -- Coverage: 64.4%, CONVERTED from nvarchar
    [S/M] INT NULL,  -- Coverage: 26.7%, CONVERTED from nvarchar
    [M/L] INT NULL,  -- Coverage: 20.0%, CONVERTED from nvarchar
    [XXXL] INT NULL,  -- Coverage: 17.8%, CONVERTED from nvarchar
    [2X] INT NULL,  -- Coverage: 15.6%, CONVERTED from nvarchar
    [3X] INT NULL,  -- Coverage: 13.3%, CONVERTED from nvarchar
    [1X] INT NULL,  -- Coverage: 11.1%, CONVERTED from nvarchar
    [4X] INT NULL,  -- Coverage: 6.7%, CONVERTED from nvarchar
    [XXXS] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [S/P] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [S+] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [1Y] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [2Y] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [3Y] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [4Y] INT NULL,  -- Coverage: 4.4%, CONVERTED from nvarchar
    [S-PETITE] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [S-M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32C] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32D] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [4XT] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32DD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32DDD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34C] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [30x32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [0w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [2w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [One_Sz] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34D] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34DD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [4w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32x32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [6w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34DDD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [32x34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36C] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [8w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [10w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [O/S] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34x32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [31x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36D] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [12w] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [34x34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36DD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36DDD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36x32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38C] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38D] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [36x34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40x30] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38DD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38x32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38DDD] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [38x34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40x32] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [40x34] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [AB/S] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [AB/M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [CD/S] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [CD/M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [CD/L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [C/S] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [C/M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [C/L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [D/S] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [D/M] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar
    [D/L] INT NULL,  -- Coverage: 2.2%, CONVERTED from nvarchar

    -- GROUP 3: ADDITIONAL ORDER DETAILS
    -- HIGH_COVERAGE (95%+)
    [TOTAL QTY] SMALLINT NULL,  -- Coverage: 100.0%, CHANGED from nvarchar
    [DESTINATION] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [DESTINATION WAREHOUSE] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [ALLOCATION (CHANNEL)] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [SHOP NAME] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [SHOP CODE] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [COLLECTION DELIVERY] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [ETA CUSTOMER WAREHOUSE DATE] DATETIME2 NULL,  -- Coverage: 100.0%, CHANGED from nvarchar
    [EX FACTORY DATE] DATETIME2 NULL,  -- Coverage: 100.0%, CHANGED from nvarchar
    [DELIVERY TERMS] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [PLANNED DELIVERY METHOD] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [NOTES] NVARCHAR(1000) NULL,  -- Coverage: 100.0%
    [ORDER TYPE] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [VALIDATION] NVARCHAR(100) NULL,  -- Coverage: 97.8%
    [VALIDATION2] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [VALIDATION3] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [VALIDATION4] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER PRICE] DECIMAL(10,4) NULL,  -- Coverage: 100.0%, CHANGED from nvarchar (increased precision)
    [USA ONLY LSTP 75% EX WORKS] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [EX WORKS (USD)] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [ADMINISTRATION FEE] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [DESIGN FEE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [FX CHARGE] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [HANDLING] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [PNP] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [SURCHARGE FEE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [DISCOUNT] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [FINAL FOB (USD)] DECIMAL(17,4) NULL,  -- Coverage: 100.0%, CHANGED from nvarchar
    [HS CODE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [US DUTY RATE] DECIMAL(10,6) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [US DUTY] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [FREIGHT] DECIMAL(18,4) NULL,  -- Coverage: 97.8%, CHANGED from TINYINT to handle large decimals
    [US TARIFF RATE] DECIMAL(10,6) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [US TARIFF] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [DDP US (USD)] DECIMAL(17,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar
    [UK DUTY RATE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [UK FREIGHT] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [UK INSURANCE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [UK CIF] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [UK DUTY] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [DDP UK (USD)] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [CAN DUTY RATE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [CAN DUTY] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [DDP CAN (USD)] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [SMS PRICE USD] DECIMAL(10,4) NULL,  -- Coverage: 97.8%, CHANGED from nvarchar (increased precision)
    [FINAL PRICES Y/N] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [NOTES FOR PRICE] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    [∆] NVARCHAR(255) NULL,  -- Coverage: 97.8%
    -- MEDIUM_COVERAGE (10-95%)
    [INFOR ADDRESS ID] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    [TRACKING NUMBER] NVARCHAR(255) NULL,  -- Coverage: 80.0%
    [INFOR DELIVERY CODE] NVARCHAR(255) NULL,  -- Coverage: 20.0%
    -- LOW_COVERAGE (<10%)
    [COUNTRY OF ORIGIN] NVARCHAR(100) NULL,  -- Coverage: 4.4%
    [DELIVERY CODE (MODL)] DECIMAL(18,4) NULL,  -- Coverage: 6.7%, CHANGED from TINYINT to handle large decimals
    [COUNTRY OF ORIGN] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [FX CHARGE 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [INFOR EX-WORKS 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [AU Product 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [AU PnP 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [AU Price 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [AU Discount 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [US Product 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [US PnP 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [US Duty 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [US Tariff 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [TARIFF RELIEF DISCOUNT (20%)] DECIMAL(17,4) NULL,  -- Coverage: 2.2%, CHANGED from nvarchar
    [US Price 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [FOB TO USE ON PRODUCT INVOICE] DECIMAL(17,4) NULL,  -- Coverage: 2.2%, CHANGED from nvarchar
    [US Discount 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [US Price w/ Discount] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [CAN Product 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [ADDITIONAL TARIFF RATE] DECIMAL(17,4) NULL,  -- Coverage: 2.2%, CHANGED from nvarchar
    [CAN PnP 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [CAN Duty 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [ADDITIONAL TARIFF %] NVARCHAR(255) NULL,  -- Coverage: 2.2%
    [ADDITIONAL TARIFF] DECIMAL(10,4) NULL,  -- Coverage: 2.2%, CHANGED from nvarchar (increased precision)
    [CAN Price 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [ADDITIONAL TARIFF VALUE] DECIMAL(18,4) NULL,  -- Coverage: 2.2%, CHANGED from TINYINT to handle large decimals
    [CAN Discount 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [TARIFF RATE CHARGED TO AAG] NVARCHAR(255) NULL,  -- Coverage: 2.2%
    [CAN Price w/ Discount] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [TARIFF LOSS] NVARCHAR(255) NULL,  -- Coverage: 2.2%
    [UK Product 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [UK PnP 4 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [INVOICE METHOD] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [UK Duty 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [UK Price 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [UK Discount 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [UK Price w/ Discount] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [RMB price (ex. VAT)] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [RMB Discount 2 Dec] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [RMB Price w/ Discount] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [PRICING NOTES] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [NASC TO ROC PRICE (RMB) (inc VAT)] DECIMAL(10,4) NULL,  -- Coverage: 2.2%, CHANGED from nvarchar (increased precision)
    [FINANCE EST (USD)] DECIMAL(18,4) NULL,  -- Coverage: 2.2%, CHANGED from TINYINT to handle large decimals
    [Warehouse] NVARCHAR(100) NULL,  -- Coverage: 6.7%
    [NASC TO WHITE FOX (USD)] DECIMAL(10,4) NULL,  -- Coverage: 2.2%, CHANGED from nvarchar (increased precision)
    [INVOICE MONTH] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [INVOICE YEAR] SMALLINT NULL,  -- Coverage: 2.2%, CHANGED from nvarchar
    [ORTP (ORDER TYPE)] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [HDPR] NVARCHAR(255) NULL,  -- Coverage: 8.9%
    [PATTERN/STYLE NAME] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [RRP] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [PFI EXCHANGE RATE] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [FOB (AUD)] DECIMAL(10,4),  -- Coverage: 2.2%
    [BUAR (BUSINESS AREA UNIT)] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [MARGIN] NVARCHAR(255) NULL,  -- Coverage: 2.2%
    [ADID] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    -- METADATA
    [_SOURCE_TABLE] NVARCHAR(255) NULL,  -- Coverage: 100.0%

    -- Delta sync columns (NEW - enable change detection and Monday.com sync)
    -- NOTE: row_hash populated by application logic using TOML configuration
    -- Hash algorithm and columns defined in sync_order_list.toml
    row_hash            CHAR(64) NULL,  -- Populated by application logic, not computed column
    sync_state          VARCHAR(10) NOT NULL DEFAULT ('NEW'),
    last_synced_at      DATETIME2 NULL,
    monday_item_id      BIGINT NULL,
    
    -- Audit columns
    created_at          DATETIME2 DEFAULT GETUTCDATE(),
    updated_at          DATETIME2 DEFAULT GETUTCDATE()
);

-- Index for efficient hash-based change detection
CREATE INDEX IX_swp_ORDER_LIST_V2_hash ON dbo.swp_ORDER_LIST_V2 (row_hash);
CREATE INDEX IX_swp_ORDER_LIST_V2_sync_state ON dbo.swp_ORDER_LIST_V2 (sync_state);
CREATE INDEX IX_swp_ORDER_LIST_V2_monday_item_id ON dbo.swp_ORDER_LIST_V2 (monday_item_id);

-- Phase 1 specific indexes for GREYSON PO 4755 testing
CREATE INDEX IX_swp_ORDER_LIST_V2_customer_po ON dbo.swp_ORDER_LIST_V2 ([CUSTOMER NAME], [PO NUMBER]);
CREATE INDEX IX_swp_ORDER_LIST_V2_aag_order ON dbo.swp_ORDER_LIST_V2 ([AAG ORDER NUMBER]);

-- COMPLETE SCHEMA SUMMARY:
-- Total columns: 417
-- Group 1 (Order Details): 56 columns
-- Group 2 (Garment Sizes): 251 columns (ALL INT)
-- Group 3 (Additional Details): 110 columns
-- Total type changes required: 279
-- Size categories in Group 2: 6