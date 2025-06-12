-- View: v_received_products
-- Description: All valid finished goods received from QuickData (last 60 days), with normalized fields

SELECT
    UPPER(LTRIM(RTRIM(a.customer_name))) AS Customer,
    UPPER(LTRIM(RTRIM(b.style_number))) AS Style,
    UPPER(LTRIM(RTRIM(b.color))) AS Color,
    UPPER(LTRIM(RTRIM(b.size))) AS Size,
    UPPER(LTRIM(RTRIM(b.ean))) AS SKUBarcode,
    b.order_no AS MO_Number,
    SUM(b.pcs_number) AS Qty,
    COALESCE(a.synchronize_time, a.recive_time) AS ReceivedDate
FROM
    [QuickData].[dbo].[V_finished_product_scan] a WITH (NOLOCK)
LEFT JOIN
    [QuickData].[dbo].[V_finished_product_scan_de] b WITH (NOLOCK)
    ON a.id = b.finished_product_scan_id
WHERE
    a.recycle = 0
    AND b.recycle = 0
    AND b.size <> 'CASE'
    AND COALESCE(a.synchronize_time, a.recive_time) IS NOT NULL
    AND (CASE
            WHEN a.recive_time > a.synchronize_time THEN a.recive_time
            ELSE a.synchronize_time
         END) > GETDATE() - 60
GROUP BY
    a.customer_name,
    b.style_number,
    b.color,
    b.order_no,
    b.size,
    b.ean,
    COALESCE(a.synchronize_time, a.recive_time);
