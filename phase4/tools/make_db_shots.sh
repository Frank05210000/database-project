#!/bin/bash
# 重新產生 4.8 節的資料表截圖（需要已載入 sql/ 的 PostgreSQL 容器，預設名稱 fuwa-p4-db）
cd "$(dirname "$0")/.." || exit 1
C=${1:-fuwa-p4-db}; S=tools/shot.sh
$S $C img/db1_tables.png '\dt+'
$S $C img/db2_counts.png "SELECT relname AS table_name, n_live_tup AS rows
FROM pg_stat_user_tables ORDER BY relname;"
$S $C img/db3_orders.png "\\d orders"
$S $C img/db4_product_discount.png '\d product_discount'
$S $C img/db5_orders_data.png "SELECT order_id, user_id, status, subtotal, discount_total, tax, shipping_fee, total, paid_at::date
FROM v_orders ORDER BY order_id;"
$S $C img/db6_items.png "SELECT order_id, item_no, product_id, product_name, unit_price, quantity, event_discount
FROM order_item WHERE order_id IN (9, 10, 12) ORDER BY order_id, item_no;;SELECT * FROM order_status_history WHERE order_id = 7 ORDER BY seq_no;"
$S $C img/db7_returns.png "SELECT return_id, order_id, status, processed_by, refund_total, reject_reason FROM return_request ORDER BY return_id;;SELECT * FROM return_item ORDER BY order_id, item_no;"
$S $C img/db8_reject.png "UPDATE orders SET status = 'closed' WHERE order_id = 12;;INSERT INTO store_staff (user_id, store_id) VALUES (4, 1);;INSERT INTO product_discount (product_id, discount_code)
VALUES (9, 'EVT-0004');;INSERT INTO product_discount (product_id, discount_code) VALUES (2, 'SEA-0001');;INSERT INTO cart_item (user_id, product_id, quantity) VALUES (4, 1, 0);;INSERT INTO return_request (order_id, reason) VALUES (5, '再退一次');;INSERT INTO return_item (order_id, item_no, return_qty) VALUES (10, 9, 1);"
