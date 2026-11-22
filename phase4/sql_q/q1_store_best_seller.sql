-- Q1：每間商店銷售量最高的商品（巢狀查詢＋檢視表 V2）
SELECT v.store_name, v.product_name, v.sold_qty, v.revenue
FROM v_product_sales v
WHERE v.sold_qty = (SELECT MAX(v2.sold_qty)
                    FROM v_product_sales v2
                    WHERE v2.store_id = v.store_id)
ORDER BY v.store_name;
