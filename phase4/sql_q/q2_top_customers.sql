-- Q2：消費總額高於「顧客平均消費總額」的顧客（GROUP BY＋HAVING＋巢狀查詢）
SELECT u.loginid, u.name,
       COUNT(*) AS order_count,
       SUM(o.total) AS spent
FROM v_orders o
JOIN users u ON u.user_id = o.user_id
WHERE o.status NOT IN ('cancelled', 'returned')
GROUP BY u.user_id, u.loginid, u.name
HAVING SUM(o.total) > (SELECT AVG(t.spent)
                       FROM (SELECT SUM(total) AS spent
                             FROM v_orders
                             WHERE status NOT IN ('cancelled', 'returned')
                             GROUP BY user_id) t)
ORDER BY spent DESC;
