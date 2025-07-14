-- Table: dbo.timeline_TNA_Greyson_FA25_D1
-- Database: ORDERS
-- Purpose: [Add description of table purpose]
-- Dependencies: [List any dependent tables/views]

CREATE TABLE [dbo].[timeline_TNA_Greyson_FA25_D1] (
    [Activity] NVARCHAR(MAX) NULL,
    [Timeline] NVARCHAR(MAX) NULL,
    [Season] NVARCHAR(MAX) NULL,
    [Subitems] NVARCHAR(MAX) NULL,
    [Phase] NVARCHAR(MAX) NULL,
    [Responsible] NVARCHAR(MAX) NULL,
    [Team] NVARCHAR(MAX) NULL,
    [DURATION] BIGINT NULL,
    [Baseline_Start] DATE NULL,
    [Baseline_Finish] DATE NULL,
    [Deadline] DATE NULL,
    [Actual_Start] DATE NULL,
    [Actual_Finish] DATE NULL,
    [Delay_Days] BIGINT NULL,
    [STATUS] NVARCHAR(MAX) NULL,
    [Customer] NVARCHAR(MAX) NULL,
    [numbeOfStyles] BIGINT NULL,
    [numberOfStylesReady] BIGINT NULL,
    [numberOfStylesReadyOnTime] BIGINT NULL,
    [percStylesReady] FLOAT NULL,
    [percStylesOnTime] FLOAT NULL
);
