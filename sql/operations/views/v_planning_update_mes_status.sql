WITH status_cte AS (
    SELECT
        [MO Number] as MO_Number,
        state,
        closed_time_t,
        cut_number,
        sew_number,
        finish_number,
        PNP_Receive,
        coalesce([Cutting WIP], 0) as "QTY WIP CUT",
        coalesce([Sewing WIP], 0) as "QTY WIP SEW",
        coalesce([Finishing WIP], 0) as "QTY WIP FIN",
        coalesce([defect_number], 0) as "QTY SCRAP",
        coalesce([cut_number], 0) as "QTY CUT",
        coalesce([sew_number], 0) as "QTY SEW",
        coalesce([finish_number], 0) as "QTY FINISH",
        coalesce([prep_number], 0) as "Precut Quantity", 
        CASE
            WHEN LOWER(state) LIKE '%closed%' THEN 6
            WHEN cut_number > 0 AND sew_number = 0 THEN 5
            WHEN sew_number > 0 AND finish_number = 0 THEN 4
            WHEN finish_number > 0 AND PNP_Receive < finish_number THEN 3
            WHEN PNP_Receive > 0
                 AND finish_number > 0
                 AND PNP_Receive >= finish_number THEN 2
            ELSE 1
        END AS status_rank,
        CASE
            WHEN LOWER(state) LIKE '%closed%' THEN 'COMPLETE'
            WHEN cut_number > 0 AND sew_number = 0 THEN 'CUTTING'
            WHEN sew_number > 0 AND finish_number = 0 THEN 'SEWING'
            WHEN finish_number > 0 AND PNP_Receive < finish_number THEN 'FINISHING'
            WHEN PNP_Receive > 0
                 AND finish_number > 0
                 AND PNP_Receive >= finish_number THEN 'PNP RECEIVED'
            ELSE 'NOT STARTED'
        END AS computed_status
    FROM dbo.MES_operational_performance
),
ranked AS (
    SELECT
        MO_Number,
        state,
        closed_time_t,
        computed_status,
        cut_number,
        sew_number,
        finish_number,
        PNP_Receive,
        [QTY WIP CUT],
        [QTY WIP SEW],
        [QTY WIP FIN],
        [QTY SCRAP],
        [QTY CUT],
        [QTY SEW],
        [QTY FINISH],
        [Precut Quantity],
        ROW_NUMBER() OVER (
            PARTITION BY MO_Number
            ORDER BY status_rank DESC
        ) AS rn
    FROM status_cte
)
SELECT
    [Item ID] AS [monday_item_id],
    r.MO_Number,
    r.state as [MES MO Status],
    r.closed_time_t,
    r.computed_status as [PRODUCTION STATUS],
    r.cut_number,
    r.sew_number,
    r.finish_number,
    r.PNP_Receive,
    r.[QTY WIP CUT],
    r.[QTY WIP SEW],
    r.[QTY WIP FIN],
    r.[QTY SCRAP],
    r.[QTY SCRAP],
    r.[QTY CUT],
    r.[QTY SEW],
    r.[QTY FINISH],
    r.[Precut Quantity],
    p.[PRODUCTION STATUS] AS existing_status
FROM ranked r
JOIN dbo.MON_COO_Planning p
  ON p.[MO NUMBER] = r.MO_Number
 AND p.[ORDER TYPE] <> 'CANCELLED'
 AND p.[Factory Country] = 'China'
WHERE r.rn = 1
  AND (p.[PRODUCTION STATUS] IS NULL or p.[QTY WIP CUT] IS NULL OR p.[QTY WIP SEW] IS NULL or p.[QTY WIP FIN] IS NULL or p.[QTY SCRAP] IS NULL
       OR p.[PRODUCTION STATUS] <> r.computed_status
       OR r.[QTY WIP CUT] <> p.[QTY WIP CUT]
       or r.[QTY WIP SEW] <> p.[QTY WIP SEW]
       or r.[QTY WIP FIN] <> p.[QTY WIP FIN]
       or r.[QTY SCRAP] <> p.[QTY SCRAP])
ORDER BY r.MO_Number;
