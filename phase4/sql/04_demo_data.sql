-- FUWA FUWA e-Shop：示範交易資料（由 backend/scripts/gen_demo_data.py 產生，請勿手動修改）
-- 共 13 筆訂單，涵蓋 received、processing、shipping、closed、cancelled、returned 六種狀態，
-- 以及已核准（部分／全部）、已拒絕、待審核的退貨申請、商店評價與購物車。
-- 金額由後端金額計算服務產生（BR-09～BR-12），退款依 BR-26；依業務流程順序執行，所有 trigger 都會檢查。
-- 狀態歷程（order_status_history）由 trigger 自動寫入，這裡只把變更時間調整為情境中的時間。

-- 訂單 #1：alice 跨店（信義＋左營），未達免運，已完成
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (1, 4, '2026-09-05 10:12:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 810, 0, 41, 100, 'received', '2026-09-05 10:12:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (1, 1, 1, '彩虹啾啾球', 180, 2, 0),
    (1, 2, 6, '真皮項圈', 450, 1, 0);
UPDATE product SET stock = stock - 2 WHERE product_id = 1;
UPDATE product SET stock = stock - 1 WHERE product_id = 6;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 1;
UPDATE order_status_history SET changed_at = '2026-09-05 15:00:00' WHERE order_id = 1 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 1);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 1;
UPDATE order_status_history SET changed_at = '2026-09-06 10:12:00' WHERE order_id = 1 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 1);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'closed' WHERE order_id = 1;
UPDATE order_status_history SET changed_at = '2026-09-08 10:12:00' WHERE order_id = 1 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 1);
INSERT INTO store_review (order_id, store_id, rating, comment, reviewed_at) VALUES (1, 1, 5, '啾啾球超耐咬，狗狗玩了一整天！', '2026-09-09 10:12:00');
INSERT INTO store_review (order_id, store_id, rating, comment, reviewed_at) VALUES (1, 3, 4, '項圈質感很好，出貨稍慢。', '2026-09-09 10:12:00');

-- 訂單 #2：bob 台中店，已完成
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (2, 5, '2026-09-12 14:30:00', '張寶博', '0922-111-222', '新北市板橋區文化路一段 20 號', 980, 0, 49, 100, 'received', '2026-09-12 14:30:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (2, 1, 3, '柔順梳毛刷', 320, 1, 0),
    (2, 2, 8, '雞肉凍乾零食', 220, 3, 0);
UPDATE product SET stock = stock - 1 WHERE product_id = 3;
UPDATE product SET stock = stock - 3 WHERE product_id = 8;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 2;
UPDATE order_status_history SET changed_at = '2026-09-12 21:42:00' WHERE order_id = 2 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 2);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 2;
UPDATE order_status_history SET changed_at = '2026-09-13 14:30:00' WHERE order_id = 2 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 2);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'closed' WHERE order_id = 2;
UPDATE order_status_history SET changed_at = '2026-09-15 02:30:00' WHERE order_id = 2 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 2);
INSERT INTO store_review (order_id, store_id, rating, comment, reviewed_at) VALUES (2, 2, 4, '凍乾零食貓咪很愛，梳子也好用。', '2026-09-15 14:30:00');

-- 訂單 #3：alice 買寵物籠，滿 1000 免運，已完成
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (3, 4, '2026-09-20 20:05:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 2800, 100, 140, 100, 'received', '2026-09-20 20:05:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (3, 1, 4, '豪華寵物籠', 2800, 1, 0);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (3, 'SHP-0001', 100);
UPDATE product SET stock = stock - 1 WHERE product_id = 4;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 3;
UPDATE order_status_history SET changed_at = '2026-09-21 08:05:00' WHERE order_id = 3 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 3);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 3;
UPDATE order_status_history SET changed_at = '2026-09-22 08:05:00' WHERE order_id = 3 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 3);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'closed' WHERE order_id = 3;
UPDATE order_status_history SET changed_at = '2026-09-24 20:05:00' WHERE order_id = 3 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 3);

-- 訂單 #4：bob 信義店，已完成
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (4, 5, '2026-10-03 09:40:00', '張寶博', '0922-111-222', '新北市板橋區文化路一段 20 號', 630, 0, 32, 100, 'received', '2026-10-03 09:40:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (4, 1, 5, '鮭魚主食罐', 65, 6, 0),
    (4, 2, 13, '羽毛逗貓棒', 120, 2, 0);
UPDATE product SET stock = stock - 6 WHERE product_id = 5;
UPDATE product SET stock = stock - 2 WHERE product_id = 13;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 4;
UPDATE order_status_history SET changed_at = '2026-10-03 14:28:00' WHERE order_id = 4 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 4);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 4;
UPDATE order_status_history SET changed_at = '2026-10-04 09:40:00' WHERE order_id = 4 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 4);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'closed' WHERE order_id = 4;
UPDATE order_status_history SET changed_at = '2026-10-05 09:40:00' WHERE order_id = 4 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 4);
INSERT INTO store_review (order_id, store_id, rating, comment, reviewed_at) VALUES (4, 1, 3, '逗貓棒羽毛有點容易掉。', '2026-10-06 09:40:00');

-- 訂單 #5：alice 左營店，已完成後部分退貨（已核准）
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (5, 4, '2026-10-10 16:20:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 1690, 100, 85, 100, 'received', '2026-10-10 16:20:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (5, 1, 10, '雲朵寵物床', 990, 1, 0),
    (5, 2, 12, '溫和洗毛精', 350, 2, 0);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (5, 'SHP-0001', 100);
UPDATE product SET stock = stock - 1 WHERE product_id = 10;
UPDATE product SET stock = stock - 2 WHERE product_id = 12;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 5;
UPDATE order_status_history SET changed_at = '2026-10-10 21:08:00' WHERE order_id = 5 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 5);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 5;
UPDATE order_status_history SET changed_at = '2026-10-11 16:20:00' WHERE order_id = 5 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 5);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'closed' WHERE order_id = 5;
UPDATE order_status_history SET changed_at = '2026-10-12 16:20:00' WHERE order_id = 5 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 5);
INSERT INTO return_request (return_id, order_id, requested_at, reason) VALUES (1, 5, '2026-10-14 16:20:00', '洗毛精多買了一瓶，未拆封。');
INSERT INTO return_item (order_id, item_no, return_qty) VALUES (5, 2, 1);
UPDATE return_request SET status = 'approved', processed_by = 2, processed_at = '2026-10-15 16:20:00', refund_total = 368 WHERE return_id = 1;
UPDATE return_item SET refund_amount = 368 WHERE order_id = 5 AND item_no = 2;
UPDATE product SET stock = stock + 1 WHERE product_id = 12;

-- 訂單 #6：bob 下單後取消
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (6, 5, '2026-10-18 11:00:00', '張寶博', '0922-111-222', '新北市板橋區文化路一段 20 號', 380, 0, 19, 100, 'received', '2026-10-18 11:00:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (6, 1, 11, '反光牽繩', 380, 1, 0);
UPDATE product SET stock = stock - 1 WHERE product_id = 11;
SELECT set_config('app.user_id', '5', false);
UPDATE orders SET status = 'cancelled' WHERE order_id = 6;
UPDATE order_status_history SET changed_at = '2026-10-18 13:24:00' WHERE order_id = 6 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 6);
UPDATE product SET stock = stock + 1 WHERE product_id = 11;

-- 訂單 #7：alice 處理中全部退貨（核准後訂單改為 returned，運費一併退還）
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (7, 4, '2026-10-25 13:15:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 580, 0, 29, 100, 'received', '2026-10-25 13:15:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (7, 1, 2, '蝴蝶結髮飾', 150, 2, 0),
    (7, 2, 7, '保暖小毛帽', 280, 1, 0);
UPDATE product SET stock = stock - 2 WHERE product_id = 2;
UPDATE product SET stock = stock - 1 WHERE product_id = 7;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 7;
UPDATE order_status_history SET changed_at = '2026-10-25 20:27:00' WHERE order_id = 7 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 7);
INSERT INTO return_request (return_id, order_id, requested_at, reason) VALUES (2, 7, '2026-10-26 01:15:00', '尺寸不合，全部退貨。');
INSERT INTO return_item (order_id, item_no, return_qty) VALUES (7, 1, 2), (7, 2, 1);
UPDATE return_request SET status = 'approved', processed_by = 2, processed_at = '2026-10-26 13:15:00', refund_total = 709 WHERE return_id = 2;
UPDATE return_item SET refund_amount = 315 WHERE order_id = 7 AND item_no = 1;
UPDATE product SET stock = stock + 2 WHERE product_id = 2;
UPDATE return_item SET refund_amount = 294 WHERE order_id = 7 AND item_no = 2;
UPDATE product SET stock = stock + 1 WHERE product_id = 7;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'returned' WHERE order_id = 7;
UPDATE order_status_history SET changed_at = '2026-10-26 13:15:00' WHERE order_id = 7 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 7);

-- 訂單 #8：alice 已完成，退貨申請被拒絕
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (8, 4, '2026-10-28 19:45:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 350, 0, 18, 100, 'received', '2026-10-28 19:45:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (8, 1, 12, '溫和洗毛精', 350, 1, 0);
UPDATE product SET stock = stock - 1 WHERE product_id = 12;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 8;
UPDATE order_status_history SET changed_at = '2026-10-29 00:33:00' WHERE order_id = 8 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 8);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 8;
UPDATE order_status_history SET changed_at = '2026-10-29 19:45:00' WHERE order_id = 8 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 8);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'closed' WHERE order_id = 8;
UPDATE order_status_history SET changed_at = '2026-10-30 19:45:00' WHERE order_id = 8 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 8);
INSERT INTO return_request (return_id, order_id, requested_at, reason) VALUES (3, 8, '2026-11-06 19:45:00', '不喜歡味道。');
INSERT INTO return_item (order_id, item_no, return_qty) VALUES (8, 1, 1);
UPDATE return_request SET status = 'rejected', processed_by = 2, processed_at = '2026-11-07 19:45:00', reject_reason = '商品已開封使用，不符合退貨條件。' WHERE return_id = 3;

-- 訂單 #9：bob 貓跳台 8 折＋主食罐買 2 送 1＋冬季 95 折，配送中
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (9, 5, '2026-11-05 08:50:00', '張寶博', '0922-111-222', '新北市板橋區文化路一段 20 號', 1875, 575, 70, 100, 'received', '2026-11-05 08:50:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (9, 1, 5, '鮭魚主食罐', 65, 3, 65),
    (9, 2, 9, '貓抓板跳台', 1680, 1, 336);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (9, 'EVT-0002', 65),
    (9, 'EVT-0001', 336),
    (9, 'SEA-0001', 74),
    (9, 'SHP-0001', 100);
UPDATE product SET stock = stock - 3 WHERE product_id = 5;
UPDATE product SET stock = stock - 1 WHERE product_id = 9;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 9;
UPDATE order_status_history SET changed_at = '2026-11-05 13:38:00' WHERE order_id = 9 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 9);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 9;
UPDATE order_status_history SET changed_at = '2026-11-06 08:50:00' WHERE order_id = 9 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 9);

-- 訂單 #10：alice 季節折扣疊加，配送中，有待審核的退貨申請
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (10, 4, '2026-11-12 21:10:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 2330, 258, 109, 100, 'received', '2026-11-12 21:10:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (10, 1, 8, '雞肉凍乾零食', 220, 2, 44),
    (10, 2, 14, '自動餵食器', 1890, 1, 0);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (10, 'EVT-0004', 44),
    (10, 'SEA-0001', 114),
    (10, 'SHP-0001', 100);
UPDATE product SET stock = stock - 2 WHERE product_id = 8;
UPDATE product SET stock = stock - 1 WHERE product_id = 14;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 10;
UPDATE order_status_history SET changed_at = '2026-11-13 06:46:00' WHERE order_id = 10 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 10);
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'shipping' WHERE order_id = 10;
UPDATE order_status_history SET changed_at = '2026-11-14 01:58:00' WHERE order_id = 10 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 10);
INSERT INTO return_request (return_id, order_id, requested_at, reason) VALUES (4, 10, '2026-11-15 21:10:00', '零食包裝破損。');
INSERT INTO return_item (order_id, item_no, return_qty) VALUES (10, 2, 1);

-- 訂單 #11：bob 三店各一件，處理中
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (11, 5, '2026-11-18 10:30:00', '張寶博', '0922-111-222', '新北市板橋區文化路一段 20 號', 950, 138, 41, 100, 'received', '2026-11-18 10:30:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (11, 1, 1, '彩虹啾啾球', 180, 1, 0),
    (11, 2, 3, '柔順梳毛刷', 320, 1, 0),
    (11, 3, 6, '真皮項圈', 450, 1, 0);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (11, 'SEA-0001', 48),
    (11, 'SEA-0002', 90);
UPDATE product SET stock = stock - 1 WHERE product_id = 1;
UPDATE product SET stock = stock - 1 WHERE product_id = 3;
UPDATE product SET stock = stock - 1 WHERE product_id = 6;
SELECT set_config('app.user_id', '2', false);
UPDATE orders SET status = 'processing' WHERE order_id = 11;
UPDATE order_status_history SET changed_at = '2026-11-18 22:30:00' WHERE order_id = 11 AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = 11);

-- 訂單 #12：alice 新訂單，已接單
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (12, 4, '2026-11-20 15:00:00', '陳愛麗', '0912-345-678', '台北市中正區八德路一段 10 號', 1875, 715, 63, 100, 'received', '2026-11-20 15:00:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (12, 1, 5, '鮭魚主食罐', 65, 3, 65),
    (12, 2, 9, '貓抓板跳台', 1680, 1, 336);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (12, 'EVT-0002', 65),
    (12, 'EVT-0001', 336),
    (12, 'SEA-0001', 74),
    (12, 'SEA-0002', 140),
    (12, 'SHP-0001', 100);
UPDATE product SET stock = stock - 3 WHERE product_id = 5;
UPDATE product SET stock = stock - 1 WHERE product_id = 9;

-- 訂單 #13：bob 新訂單，已接單
INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, subtotal, discount_total, tax, shipping_fee, status, paid_at) VALUES (13, 5, '2026-11-21 22:40:00', '張寶博', '0922-111-222', '新北市板橋區文化路一段 20 號', 360, 52, 15, 100, 'received', '2026-11-21 22:40:00');
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES
    (13, 1, 13, '羽毛逗貓棒', 120, 3, 0);
INSERT INTO order_discount (order_id, discount_code, amount) VALUES
    (13, 'SEA-0001', 18),
    (13, 'SEA-0002', 34);
UPDATE product SET stock = stock - 3 WHERE product_id = 13;

-- 購物車（DR-04）
INSERT INTO cart_item (user_id, product_id, quantity, added_at) VALUES (4, 10, 1, '2026-11-21 23:00:00');
INSERT INTO cart_item (user_id, product_id, quantity, added_at) VALUES (4, 13, 2, '2026-11-21 23:02:00');
INSERT INTO cart_item (user_id, product_id, quantity, added_at) VALUES (5, 8, 1, '2026-11-22 08:15:00');

-- 讓 SERIAL 從示範資料之後繼續編號
SELECT setval('orders_order_id_seq', (SELECT MAX(order_id) FROM orders));
SELECT setval('return_request_return_id_seq', (SELECT MAX(return_id) FROM return_request));
SELECT set_config('app.user_id', '', false);
