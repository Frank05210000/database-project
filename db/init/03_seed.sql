-- FUWA FUWA e-Shop：初始資料（DBS-F-002、BR-22）
-- 示範帳號密碼：admin/admin123、staff/staff123、manager/staff123、alice|bob|carol/customer123
-- 歷史訂單由後端 app/seed_orders.py 透過結帳流程產生（金額才會和 BR-09～BR-12 一致）。

-- ---------- 系統參數（BR-22） ----------
INSERT INTO system_setting (setting_key, setting_value, description) VALUES
    ('tax_rate',     '0.05', '營業稅率'),
    ('shipping_fee', '100',  '基本運費（新台幣元）');

-- ---------- 使用者與角色（BR-02：一位使用者可有多種角色） ----------
INSERT INTO users (loginid, name, password_hash, email, address, phone, is_active) VALUES
    ('admin',   '平台管理員',   '$2b$10$zGz5vK72Wt/er2j5.sy09.FraKj76WrwqVZmlEHcnGJB3uL/uwS1K', 'admin@fuwafuwa.tw',   '台北市大安區忠孝東路三段 1 號', '02-2771-2171', TRUE),
    ('staff',   '王小明',       '$2b$10$zZWKZD8Syv7gbgvWGv/2b.OwoFPSTW5XfL7HhhMXjne4apetBoYcC', 'staff@fuwafuwa.tw',   '台北市信義區松仁路 100 號',     '02-2720-0001', TRUE),
    ('manager', '林店長',       '$2b$10$zZWKZD8Syv7gbgvWGv/2b.OwoFPSTW5XfL7HhhMXjne4apetBoYcC', 'manager@fuwafuwa.tw', '台中市南屯區公益路二段 51 號',  '04-2320-0002', TRUE),
    ('alice',   '陳愛麗',       '$2b$10$We9RQjr9TVeQVS7UyjrTMOR83k4VlprGRLIanz979TGNF9AKaHVFK', 'alice@example.com',   '台北市中正區八德路一段 10 號',  '0912-345-678', TRUE),
    ('bob',     '張寶博',       '$2b$10$We9RQjr9TVeQVS7UyjrTMOR83k4VlprGRLIanz979TGNF9AKaHVFK', 'bob@example.com',     '新北市板橋區文化路一段 20 號',  '0922-111-222', TRUE),
    ('carol',   '李可蘿',       '$2b$10$We9RQjr9TVeQVS7UyjrTMOR83k4VlprGRLIanz979TGNF9AKaHVFK', 'carol@example.com',   '高雄市左營區博愛二路 30 號',    '0933-555-666', FALSE);

INSERT INTO user_role (user_id, role) VALUES
    (1, 'admin'),
    (2, 'staff'),
    (3, 'staff'), (3, 'admin'),
    (4, 'customer'),
    (5, 'customer'),
    (6, 'customer');

-- ---------- 商店 ----------
INSERT INTO store (name, address, email, phone) VALUES
    ('FUWA FUWA 台北信義店', '台北市信義區松仁路 100 號',    'xinyi@fuwafuwa.tw',    '02-2720-0001'),
    ('FUWA FUWA 台中公益店', '台中市南屯區公益路二段 51 號', 'gongyi@fuwafuwa.tw',   '04-2320-0002'),
    ('FUWA FUWA 高雄左營店', '高雄市左營區博愛二路 30 號',   'zuoying@fuwafuwa.tw',  '07-5560-0003');

-- ---------- 商品（分類：food、toy、accessory、care、home） ----------
INSERT INTO product (store_id, name, description, category, image_url, price, stock, is_listed) VALUES
    (1, '彩虹啾啾球',     '會發出啾啾聲的彈力球，耐咬材質，適合中小型犬。',           'toy',       '/images/ball.png',                         180,  60, TRUE),
    (1, '蝴蝶結髮飾',     '柔軟緞面蝴蝶結，附安全夾，拍照必備。',                     'accessory', '/images/bow.png',                          150,  80, TRUE),
    (2, '柔順梳毛刷',     '圓頭針梳不傷皮膚，梳開打結毛髮、減少掉毛。',               'care',      '/images/brush.png',                        320,  45, TRUE),
    (2, '豪華寵物籠',     '雙門設計、底盤可抽出清洗，適合兔子與小型犬。',             'home',      '/images/cage.png',                        2800,  12, TRUE),
    (1, '鮭魚主食罐',     '真實鮭魚肉塊，無穀配方，每罐 85g。',                       'food',      '/images/can.png',                           65, 200, TRUE),
    (3, '真皮項圈',       '植鞣牛皮製作，附名牌扣環，可調整長度。',                   'accessory', '/images/collar.png',                       450,  35, TRUE),
    (3, '保暖小毛帽',     '針織毛線帽，冬天出門保暖又可愛。',                         'accessory', '/images/hat.png',                          280,  40, TRUE),
    (2, '雞肉凍乾零食',   '100% 雞胸肉低溫凍乾，訓練獎勵好幫手。',                   'food',      '/images/products/freeze_dried_chicken.png', 220, 120, TRUE),
    (1, '貓抓板跳台',     '三層貓跳台結合劍麻抓柱，讓貓咪盡情攀爬。',                 'home',      '/images/products/cat_tower.png',          1680,  15, TRUE),
    (3, '雲朵寵物床',     '超柔軟絨毛睡窩，可拆洗，給毛孩一夜好眠。',                 'home',      '/images/products/pet_bed.png',             990,  25, TRUE),
    (2, '反光牽繩',       '夜間反光織帶，手把加厚防勒。',                             'accessory', '/images/products/leash.png',               380,  50, TRUE),
    (3, '溫和洗毛精',     '燕麥配方，低敏溫和，洗後毛髮蓬鬆柔順。',                   'care',      '/images/products/shampoo.png',             350,  70, TRUE),
    (1, '羽毛逗貓棒',     '天然羽毛加鈴鐺，陪貓咪玩出好心情。',                       'toy',       '/images/products/teaser_wand.png',         120,  90, TRUE),
    (2, '自動餵食器',     '定時定量出糧，App 遠端控制，出門也安心。',                 'home',      '/images/products/feeder.png',             1890,  10, TRUE),
    (3, '舊款陶瓷水碗',   '已停產的舊款水碗。',                                       'home',      '/images/can.png',                          250,   0, FALSE);

-- ---------- 折扣政策（DMS） ----------
-- 折扣代碼由系統產生（BR-18），後端用 discount_code_seq 產生「類型前綴-流水號」
CREATE SEQUENCE discount_code_seq START 100;

INSERT INTO discount (discount_code, discount_type, description, start_date, end_date, rate, min_amount, buy_qty, free_qty, is_active) VALUES
    ('SHP-0001', 'shipping',      '滿 1000 元免運',            '2026-01-01', '2026-12-31', NULL, 1000, NULL, NULL, TRUE),
    ('SEA-0001', 'seasonal',      '冬季暖心 95 折',            '2026-11-01', '2027-02-28', 0.050, NULL, NULL, NULL, TRUE),
    ('SEA-0002', 'seasonal',      '週年慶全館 9 折',           '2026-11-15', '2026-11-30', 0.100, NULL, NULL, NULL, TRUE),
    ('SEA-0003', 'seasonal',      '夏日清涼 92 折（已結束）',  '2026-07-01', '2026-08-31', 0.080, NULL, NULL, NULL, TRUE),
    ('EVT-0001', 'special_event', '貓跳台限時 8 折',           '2026-11-01', '2026-12-31', 0.200, NULL, NULL, NULL, TRUE),
    ('EVT-0002', 'special_event', '主食罐買 2 送 1',           '2026-11-01', '2026-12-31', NULL, NULL, 2, 1, TRUE),
    ('EVT-0003', 'special_event', '啾啾球 85 折（已結束）',    '2026-06-01', '2026-06-30', 0.150, NULL, NULL, NULL, TRUE),
    ('EVT-0004', 'special_event', '凍乾零食 9 折',             '2026-10-01', '2026-12-31', 0.100, NULL, NULL, NULL, TRUE);

INSERT INTO product_discount (product_id, discount_code) VALUES
    (9, 'EVT-0001'),
    (5, 'EVT-0002'),
    (1, 'EVT-0003'),
    (8, 'EVT-0004');
