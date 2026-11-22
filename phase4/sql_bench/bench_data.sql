-- Section 7 效能實測用的測試資料（僅供量測，不是真實資料）
-- 匯入已執行 01～04 的獨立測試資料庫：
--   psql -U fuwa -d fuwa -f bench_data.sql
-- 規模：依 4.5 節估計的一年訂單量（20,000 位顧客、109,500 筆訂單、約 33 萬筆明細），
-- 商品數放大到 10 萬項，讓關鍵字搜尋的差異看得出來。
-- 為了快速匯入，以 session_replication_role = replica 暫停 trigger 與外鍵檢查；
-- 產生的資料仍符合所有 CHECK 限制。
BEGIN;
SET LOCAL session_replication_role = replica;
SELECT setseed(0.42);

-- 20,000 位測試顧客
INSERT INTO users (loginid, name, password_hash, email, is_active)
SELECT 'bench' || g, 'Test customer ' || g, 'x', 'bench' || g || '@example.com', true
FROM generate_series(1, 20000) g;
INSERT INTO user_role (user_id, role)
SELECT user_id, 'customer' FROM users WHERE loginid LIKE 'bench%';

-- 10 萬項商品：名稱由形容詞、材質、品項隨機組合，約 0.2% 含有搜尋用的關鍵字「貓抓板」
WITH w AS (
  SELECT ARRAY['柔軟','耐咬','防水','可愛','加大','迷你','輕量','經典','豪華','自動'] AS adj,
         ARRAY['棉質','木製','矽膠','麻繩','不鏽鋼','陶瓷','羊毛','竹編'] AS mat,
         ARRAY['寵物床','飼料碗','逗貓棒','牽繩','項圈','玩具球','睡墊','水壺','梳子','背包','貓砂盆','磨爪板'] AS item
)
INSERT INTO product (store_id, name, description, category, price, stock, is_listed)
SELECT 1 + (g % 3),
       adj[1 + (random() * 9)::int] || mat[1 + (random() * 7)::int] ||
         CASE WHEN random() < 0.002 THEN '貓抓板' ELSE item[1 + (random() * 11)::int] END || ' #' || g,
       '適合各種體型的寵物，材質安全無毒，可手洗，使用前請詳閱說明。商品編號 ' || g,
       '測試', 50 + (random() * 2000)::int, (random() * 100)::int, random() < 0.9
FROM generate_series(1, 100000) g, w;

-- 109,500 筆訂單，平均分布在過去一年，狀態皆為 closed（金額符合 CHECK）
INSERT INTO orders (user_id, order_time, recipient_name, recipient_phone, recipient_address,
                    subtotal, discount_total, tax, shipping_fee, status, paid_at)
SELECT u.user_id, t, 'Test recipient', '0900000000', 'Test address', s, 0, round(s * 0.05), 100, 'closed', t
FROM (SELECT g, now() - random() * interval '365 days' AS t, 300 + (random() * 3000)::int AS s,
             (SELECT min(user_id) FROM users WHERE loginid LIKE 'bench%') + (random() * 19999)::int AS uid
      FROM generate_series(1, 109500) g) x
JOIN users u ON u.user_id = x.uid;

-- 每筆訂單 3 項明細
INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount)
SELECT o.order_id, k, 16 + (o.order_id * 7919 + k * 31337) % 99999, 'Test product', 100, 1, 0   -- 同一筆訂單的三項商品不重複
FROM orders o CROSS JOIN generate_series(1, 3) k
WHERE o.recipient_name = 'Test recipient';

COMMIT;
ANALYZE;
