-- Q3：各商店的平均評分、評論數與商品數，沒有評價的商店也列出（LEFT JOIN＋聚合＋ORDER BY）
SELECT s.name AS store_name,
       (SELECT COUNT(*) FROM product p WHERE p.store_id = s.store_id AND p.is_listed) AS listed_products,
       COUNT(r.order_id) AS review_count,
       ROUND(AVG(r.rating), 2) AS avg_rating
FROM store s
LEFT JOIN store_review r ON r.store_id = s.store_id
GROUP BY s.store_id, s.name
ORDER BY avg_rating DESC NULLS LAST, review_count DESC;
