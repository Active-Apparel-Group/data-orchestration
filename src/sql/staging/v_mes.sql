

/** use QuickData */

Select order_no as [MO Number], style_no, closed_time_t, state, order_number, prep_number, cut_number, sew_number, finish_number, sample_number, defect_number, 
remain_number, cut_fdate, sew_fdate, finish_fdate, customer_name, customer_no
      ,[Package scan]
      ,[Bucket Scan]
      ,[PNP Receive]
      ,[big_ironing]
  FROM [QuickData].[dbo].[rpt_operational_performance]