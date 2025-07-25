-- GROUP 1: ORDER DETAILS SCHEMA
-- Generated from analysis of 45 customer ORDER_LIST tables
-- Columns ordered by coverage priority and original position

CREATE TABLE [dbo].[ORDER_LIST_GROUP1] (
    -- Auto-increment primary key
    [ID] INT IDENTITY(1,1) PRIMARY KEY,

    -- HIGH_COVERAGE (95%+)
    [AAG ORDER NUMBER] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [CUSTOMER NAME] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [ORDER DATE PO RECEIVED] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [PO NUMBER] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER ALT PO] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [AAG SEASON] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [CUSTOMER SEASON] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    [DROP] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [MONTH] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [RANGE / COLLECTION] NVARCHAR(255) NULL,  -- Coverage: 100.0%
    [PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT] NVARCHAR(255) NULL,  -- Coverage: 100.0%
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
    [UNIT OF MEASURE] NVARCHAR(100) NULL,  -- Coverage: 100.0%
    -- MEDIUM_COVERAGE (10-95%)
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
    -- LOW_COVERAGE (<10%)
    [FACILITY CODE] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [CUSTOMER CODE] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [Column2] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [Column1] NVARCHAR(100) NULL,  -- Coverage: 2.2%
    [AAG SEASON CODE] NVARCHAR(255) NULL,  -- Coverage: 6.7%
    [MAKE OR BUY FLAG] NVARCHAR(100) NULL,  -- Coverage: 4.4%
    [MAKE/BUY CODE] NVARCHAR(100) NULL,  -- Coverage: 6.7%
);

-- SCHEMA SUMMARY:
-- Total columns: 56
-- High coverage (95%+): 23
-- Medium coverage (10-95%): 26
-- Low coverage (<10%): 7
-- Type changes required: 0