-- V1：各商店每日銷售報表（RSS-F-001、BR-23）
-- 每筆訂單的總額依各商店商品「扣除特殊活動折扣後的金額」比例分攤；
-- 不計 cancelled、returned 的訂單；部分退貨從該商店扣除退款金額。
CREATE VIEW v_store_daily_sales AS
WITH line AS (
    SELECT oi.order_id, p.store_id,
           oi.unit_price * oi.quantity - oi.event_discount AS net
    FROM order_item oi
    JOIN product p ON p.product_id = oi.product_id
), share AS (
    SELECT order_id, store_id,
           SUM(net) AS store_net,
           SUM(SUM(net)) OVER (PARTITION BY order_id) AS order_net
    FROM line
    GROUP BY order_id, store_id
), refund AS (
    SELECT ri.order_id, p.store_id, SUM(ri.refund_amount) AS amount
    FROM return_item ri
    JOIN return_request rr ON rr.order_id = ri.order_id AND rr.status = 'approved'
    JOIN order_item oi ON oi.order_id = ri.order_id AND oi.item_no = ri.item_no
    JOIN product p ON p.product_id = oi.product_id
    GROUP BY ri.order_id, p.store_id
)
SELECT o.paid_at::date AS sales_date,
       s.store_id,
       s.name AS store_name,
       COUNT(*) AS order_count,
       SUM(ROUND(o.total * sh.store_net / NULLIF(sh.order_net, 0))
           - COALESCE(r.amount, 0)) AS sales_total
FROM v_orders o
JOIN share sh ON sh.order_id = o.order_id
JOIN store s ON s.store_id = sh.store_id
LEFT JOIN refund r ON r.order_id = o.order_id AND r.store_id = sh.store_id
WHERE o.status NOT IN ('cancelled', 'returned')
GROUP BY o.paid_at::date, s.store_id, s.name;

SELECT * FROM v_store_daily_sales ORDER BY sales_date DESC, sales_total DESC;
