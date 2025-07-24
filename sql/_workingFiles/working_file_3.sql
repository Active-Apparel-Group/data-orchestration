


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



