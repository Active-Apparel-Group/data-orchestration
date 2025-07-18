-- View: v_scanned_not_delivered
-- Description: Scanned units not yet delivered (no timestamps, not in PNP, scanned in last 30 days)

SELECT
    UPPER(LTRIM(RTRIM(a.customer_name))) AS Customer,
    UPPER(LTRIM(RTRIM(b.style_number))) AS Style,
    UPPER(LTRIM(RTRIM(b.color))) AS Color,
    UPPER(LTRIM(RTRIM(b.size))) AS Size,
    UPPER(LTRIM(RTRIM(b.ean))) AS SKUBarcode,
    b.order_no AS MO_Number,
    SUM(b.pcs_number) AS Qty
FROM
    QuickData.dbo.V_finished_product_scan a WITH (NOLOCK)
LEFT JOIN
    QuickData.dbo.V_finished_product_scan_de b WITH (NOLOCK)
    ON a.id = b.finished_product_scan_id
WHERE
    a.recycle = 0
    AND a.place_name <> 'PNP'
    AND b.recycle = 0
    AND a.synchronize_time IS NULL
    AND a.recive_time IS NULL
    AND a.create_time > GETDATE() - 30
GROUP BY
    a.customer_name,
    b.style_number,
    b.color,
    b.order_no,
    b.size,
    b.ean;
