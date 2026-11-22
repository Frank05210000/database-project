-- V2：各商品的銷售統計（RSS-F-004 暢銷商品）
CREATE VIEW v_product_sales AS
SELECT p.product_id, p.name AS product_name, s.store_id, s.name AS store_name,
       COUNT(DISTINCT oi.order_id) AS order_count,
       SUM(oi.quantity) AS sold_qty,
       SUM(oi.unit_price * oi.quantity - oi.event_discount) AS revenue
FROM order_item oi
JOIN orders o ON o.order_id = oi.order_id
JOIN product p ON p.product_id = oi.product_id
JOIN store s ON s.store_id = p.store_id
WHERE o.status NOT IN ('cancelled', 'returned')
GROUP BY p.product_id, p.name, s.store_id, s.name;

SELECT product_name, store_name, order_count, sold_qty, revenue
FROM v_product_sales
ORDER BY sold_qty DESC, revenue DESC
LIMIT 10;
