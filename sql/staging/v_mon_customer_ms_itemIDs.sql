

SELECT [Item ID],
      [CUSTOMER] AS Customer
      ,[AAG ORDER NUMBER] AS Order_Number
      ,[PO NUMBER] AS Customer_PO
      ,[AAG SEASON] AS Season
      ,[MO NUMBER] AS MO_Number
      ,[STYLE] AS Style
      ,[COLOR] AS Color
      ,[DELIVERY TERMS] as Incoterms
      ,[PLANNED DELIVERY METHOD] as Shipping_Method
      ,[ORDER TYPE]
      ,[DESTINATION]
      ,[DESTINATION WAREHOUSE]
  FROM [dbo].[MON_CustMasterSchedule]