SELECT [Item ID],
      [CUSTOMER] AS Customer
      ,[AAG ORDER NUMBER] AS Order_Number
      ,[PO NUMBER] AS Customer_PO
      ,[AAG SEASON] AS Season
      ,[MO NUMBER] AS MO_Number
      ,[STYLE] AS Style
      ,[COLOR] AS Color
      ,[TOTAL QTY] AS Qty
      ,[DELIVERY TERMS] as Incoterms
      ,[PLANNED DELIVERY METHOD] as Shipping_Method
      ,[QTY PACKED NOT SHIPPED] -- from v_packed_products.sql
      ,[QTY SHIPPED] -- from v_shipped.sql
      ,[ORDER TYPE]
      ,[DESTINATION]
      ,[DESTINATION WAREHOUSE]
  FROM [dbo].[MON_CustMasterSchedule]


  -- Other columns below are not part of the standardized mapping, but are retained for reference:
      /*
      [Title]
      ,[UpdateDate]
      ,[Group]
      ,[Subitems]
      ,[ORDER DATE PO RECEIVED]
      ,[CUSTOMER SEASON]
      ,[DROP]
      ,[STYLE DESCRIPTION]
      ,[CATEGORY]
      ,[PATTERN ID]
      ,[UNIT OF MEASURE]
      ,[XS]
      ,[S]
      ,[M]
      ,[L]
      ,[XL]
      ,[XXL]
      ,[XXXL]
      ,[4XT]
      ,[QTY PACKED NOT SHIPPED]
      ,[QTY SHIPPED]
      ,[ORDER TYPE]
      ,[DESTINATION]
      ,[DESTINATION WAREHOUSE]
      ,[CUSTOMER REQ IN DC DATE]
      ,[CUSTOMER EX FACTORY DATE]
      ,[DELIVERY TERMS]
      ,[PLANNED DELIVERY METHOD]
      ,[NOTES]
      ,[CUSTOMER PRICE]
      ,[USA ONLY LSTP 75% EX WORKS]
      ,[EX WORKS (USD)]
      ,[ADMINISTRATION FEE]
      ,[DESIGN FEE]
      ,[FX CHARGE]
      ,[HANDLING]
      ,[SURCHARGE FEE]
      ,[DISCOUNT]
      ,[FINAL FOB (USD)]
      ,[HS CODE]
      ,[US DUTY RATE]
      ,[US DUTY]
      ,[FREIGHT]
      ,[US TARIFF RATE]
      ,[US TARIFF]
      ,[DDP US (USD)]
      ,[SMS PRICE USD]
      ,[FINAL PRICES Y/N]
      ,[NOTES FOR PRICE]
      ,[Item ID]
      ,[PLANNING BOARD]
      ,[EX-FTY (Change Request)]
      ,[REQUESTED XFD STATUS]
      ,[EX-FTY (Forecast)]
      ,[EX-FTY (Partner PO)]
      ,[EX-FTY (Revised LS)]
      ,[PRODUCTION TYPE]
      ,[AQL INSPECTION]
      ,[AQL TYPE]
      ,[PLANNED CUT DATE]
      ,[PRODUCTION STATUS]
      ,[FACTORY COUNTRY]
      ,[FACTORY]
      ,[ALLOCATION STATUS]
      ,[PRODUCTION QTY]
      ,[TRIM ETA DATE]
      ,[FABRIC ETA DATE]
      ,[TRIM STATUS]
      ,[FABRIC STATUS]
      ,[PPS CMT DUE]
      ,[PPS CMT RCV DATE]
      ,[PPS STATUS]
      ,[ORDER STATUS]
      ,[WIP]
      */