


Select a.CODE,
  b.MOQ_CATEGORY_LABEL,
       c.MOQ_TYPE,
       c.MOQ_PRICE,
       d.SURCHARGE_CATEGORY_LABEL,
       e.SURCHARGE_TYPE,
       e.SURCHARGE_PRICE
from FM_fabric_list a
  LEFT JOIN [dbo].[FM_fabric_supplier_moq]         b ON a.SUPPLIER_MOQ         = b.F_SUPPLIER_MOQ_ID
  LEFT JOIN [dbo].[FM_fabric_supplier_moq_list]       c ON a.SUPPLIER_MOQ         = c.F_SUPPLIER_MOQ_ID
  LEFT JOIN [dbo].[FM_fabric_supplier_surcharge]      d ON a.SUPPLIER_SURCHARGE   = d.F_SUPPLIER_SURCHARGE_ID
  LEFT JOIN [dbo].[FM_fabric_supplier_surcharge_list] e ON a.SUPPLIER_SURCHARGE   = e.F_SUPPLIER_SURCHARGE_ID


  Select * from FM_fabric_list;
  Select * from FM_fabric_supplier_moq;
  Select * from FM_fabric_supplier_moq_list;
  Select * from [dbo].[FM_fabric_supplier_surcharge];
  Select * from [dbo].[FM_fabric_supplier_surcharge_list];




WITH CustomerPlannerCTE AS (
    SELECT *
    FROM (VALUES
        ('AESCAPE', 'Zoey Cheng 程东红', '74522471'),
        ('AIME LEON DORE', 'Zoey Cheng 程东红', '74522471'),
        ('ALWRLD', 'Nina Ma 马珊珊', '74522468'),
        ('ASRV', 'Zoey Cheng 程东红', '74522471'),
        ('BAD BIRDIE', 'Nina Ma 马珊珊', '74522468'),
        ('BANDIT', 'Zoey Cheng 程东红', '74522471'),
        ('BOGGI MILANO', 'Lancy Su 苏美兰', '74522477'),
        ('BORN PRIMITIVE', 'Lancy Su 苏美兰', '74522477'),
        ('FEETURES', 'Lancy Su 苏美兰', '74522477'),
        ('GREYSON', 'Zoey Cheng 程东红', '74522471'),
        ('JOHNNIE O', 'Lancy Su 苏美兰', '74522477'),
        ('LAMBS', 'Zoey Cheng 程东红', '74522471'),
        ('MACK WELDON', 'Nina Ma 马珊珊', '74522468'),
        ('PELOTON', 'Lancy Su 苏美兰', '74522477'),
        ('RHONE', 'Zoey Cheng 程东红', '74522471'),
        ('RHYTHM', 'Nina Ma 马珊珊', '74522468'),
        ('SOULCYCLE', 'Nina Ma 马珊珊', '74522468'),
        ('SPIRITUAL GANGSTER', 'Nina Ma 马珊珊', '74522468'),
        ('SUN DAY RED', 'Nina Ma 马珊珊', '74522468'),
        ('TAYLORMADE', 'Nina Ma 马珊珊', '74522468'),
        ('TITLE NINE', 'Lancy Su 苏美兰', '74522477'),
        ('TRACKSMITH', 'Lancy Su 苏美兰', '74522477'),
        ('UNE PIECE', 'Nina Ma 马珊珊', '74522468')
    ) AS cte (Customer, Planner, PlannerID)
)

SELECT
    p.[Item ID] AS monday_item_id,
    p.[CUSTOMER] AS monday_customer,
    p.Planner, 
    cte.Planner as CTE_Planner,
    cte.PlannerID as PLANNER
FROM MON_COO_Planning p
JOIN CustomerPlannerCTE cte ON p.[CUSTOMER] = cte.Customer
and left(p.[Planner],3) != left(cte.Planner,3)


