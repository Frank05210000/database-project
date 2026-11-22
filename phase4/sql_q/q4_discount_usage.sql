-- Q4：各折扣政策的使用次數與折抵總額，含從未被使用的折扣（LEFT JOIN＋GROUP BY＋ORDER BY）
SELECT d.discount_code, d.discount_type, d.start_date, d.end_date,
       COUNT(od.order_id) AS used_orders,
       COALESCE(SUM(od.amount), 0) AS total_amount
FROM discount d
LEFT JOIN order_discount od ON od.discount_code = d.discount_code
GROUP BY d.discount_code, d.discount_type, d.start_date, d.end_date
ORDER BY total_amount DESC, d.discount_code;
