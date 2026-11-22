-- FUWA FUWA e-Shop 資料庫 schema（Phase 3，PostgreSQL 16+）
-- 以 phase2/schema.sql 為基礎，Phase 3／4 的修改：
--   * 新增 return_request.refund_total（DR-13 退款總額，核准退貨時依 BR-26 算好存起來）
--   * 正規化到 3NF：product_discount 移除重複的 discount_type／期間欄位（原本部分相依於 discount_code）；
--     return_item 以 (order_id, item_no) 為主鍵、移除 return_id（原本 return_id → order_id 造成部分相依）。
--     BR-13 期間不重疊改由 02_triggers.sql 的 trigger 檢查。
--     orders 刪除 total 欄位（由 subtotal、discount_total、tax、shipping_fee 決定，屬遞移相依），改由檢視表 v_orders 計算。
-- trigger 見 02_triggers.sql，初始資料見 03_seed.sql。

-- ---------- 使用者與角色 ----------
CREATE TABLE users (
    user_id        SERIAL        PRIMARY KEY,
    loginid        VARCHAR(30)   NOT NULL UNIQUE,
    name           VARCHAR(50)   NOT NULL,
    password_hash  VARCHAR(100)  NOT NULL,
    email          VARCHAR(100)  NOT NULL,
    address        VARCHAR(200),
    phone          VARCHAR(20),
    is_active      BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP     NOT NULL DEFAULT now()
);

CREATE TABLE user_role (
    user_id  INT          NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role     VARCHAR(10)  NOT NULL CHECK (role IN ('customer', 'staff', 'admin')),
    PRIMARY KEY (user_id, role)
);

-- ---------- 商店與商品 ----------
CREATE TABLE store (
    store_id  SERIAL        PRIMARY KEY,
    name      VARCHAR(50)   NOT NULL,
    address   VARCHAR(200)  NOT NULL,
    email     VARCHAR(100)  NOT NULL,
    phone     VARCHAR(20)   NOT NULL
);

-- 工作人員至多隸屬一間商店；沒有紀錄表示總部工作人員
CREATE TABLE store_staff (
    user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    store_id INT NOT NULL REFERENCES store(store_id)
);

CREATE TABLE product (
    product_id   SERIAL         PRIMARY KEY,
    store_id     INT            NOT NULL REFERENCES store(store_id),
    name         VARCHAR(100)   NOT NULL,
    description  TEXT,
    category     VARCHAR(30),
    image_url    VARCHAR(300),
    price        NUMERIC(10,0)  NOT NULL CHECK (price > 0),
    stock        INT            NOT NULL CHECK (stock >= 0),
    is_listed    BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP      NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP      NOT NULL DEFAULT now()
);

CREATE TABLE cart_item (
    user_id     INT        NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id  INT        NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    quantity    INT        NOT NULL CHECK (quantity > 0),
    added_at    TIMESTAMP  NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, product_id)
);

-- ---------- 訂單 ----------
CREATE TABLE orders (
    order_id           SERIAL         PRIMARY KEY,
    user_id            INT            NOT NULL REFERENCES users(user_id),
    order_time         TIMESTAMP      NOT NULL DEFAULT now(),
    recipient_name     VARCHAR(50)    NOT NULL,
    recipient_phone    VARCHAR(20)    NOT NULL,
    recipient_address  VARCHAR(200)   NOT NULL,
    subtotal           NUMERIC(10,0)  NOT NULL CHECK (subtotal >= 0),
    discount_total     NUMERIC(10,0)  NOT NULL DEFAULT 0 CHECK (discount_total >= 0),
    tax                NUMERIC(10,0)  NOT NULL CHECK (tax >= 0),
    shipping_fee       NUMERIC(10,0)  NOT NULL CHECK (shipping_fee >= 0),
    status             VARCHAR(10)    NOT NULL DEFAULT 'received'
                       CHECK (status IN ('received', 'processing', 'shipping',
                                         'closed', 'cancelled', 'returned')),
    paid_at            TIMESTAMP      NOT NULL,
    -- 訂單總額不存欄位（BR-09：total = subtotal − discount_total + tax + shipping_fee 是遞移相依），
    -- 由檢視表 v_orders 計算；這裡保證總額不為負
    CHECK (subtotal - discount_total + tax + shipping_fee >= 0)
);

CREATE TABLE order_item (
    order_id        INT            NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    item_no         SMALLINT       NOT NULL CHECK (item_no > 0),
    product_id      INT            NOT NULL REFERENCES product(product_id),
    product_name    VARCHAR(100)   NOT NULL,
    unit_price      NUMERIC(10,0)  NOT NULL CHECK (unit_price > 0),
    quantity        INT            NOT NULL CHECK (quantity > 0),
    event_discount  NUMERIC(10,0)  NOT NULL DEFAULT 0
                    CHECK (event_discount >= 0 AND event_discount <= unit_price * quantity),
    PRIMARY KEY (order_id, item_no),
    UNIQUE (order_id, product_id)
);

CREATE TABLE order_status_history (
    order_id    INT          NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    seq_no      SMALLINT     NOT NULL CHECK (seq_no > 0),
    status      VARCHAR(10)  NOT NULL
                CHECK (status IN ('received', 'processing', 'shipping',
                                  'closed', 'cancelled', 'returned')),
    changed_at  TIMESTAMP    NOT NULL DEFAULT now(),
    changed_by  INT          NOT NULL REFERENCES users(user_id),
    PRIMARY KEY (order_id, seq_no)
);

-- ---------- 折扣 ----------
CREATE TABLE discount (
    discount_code  VARCHAR(20)    PRIMARY KEY,
    discount_type  VARCHAR(15)    NOT NULL
                   CHECK (discount_type IN ('shipping', 'seasonal', 'special_event')),
    description    VARCHAR(200)   NOT NULL,
    start_date     DATE           NOT NULL,
    end_date       DATE           NOT NULL,
    rate           NUMERIC(4,3)   CHECK (rate > 0 AND rate < 1),
    min_amount     NUMERIC(10,0)  CHECK (min_amount > 0),
    buy_qty        SMALLINT       CHECK (buy_qty > 0),
    free_qty       SMALLINT       CHECK (free_qty > 0),
    is_active      BOOLEAN        NOT NULL DEFAULT TRUE,
    CHECK (start_date <= end_date),
    CHECK ((buy_qty IS NULL) = (free_qty IS NULL)),
    CHECK (
        (discount_type = 'shipping'      AND min_amount IS NOT NULL AND rate IS NULL AND buy_qty IS NULL) OR
        (discount_type = 'seasonal'      AND rate IS NOT NULL AND min_amount IS NULL AND buy_qty IS NULL) OR
        (discount_type = 'special_event' AND min_amount IS NULL AND (rate IS NULL) <> (buy_qty IS NULL))
    )
);

-- 特殊活動折扣適用的商品。期間只存在 discount；BR-13（期間不重疊）與「只有 special_event 能掛商品」
-- 由 trigger product_discount_check 與 discount_period_check 檢查（02_triggers.sql）
CREATE TABLE product_discount (
    product_id     INT          NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    discount_code  VARCHAR(20)  NOT NULL REFERENCES discount(discount_code) ON DELETE CASCADE,
    PRIMARY KEY (product_id, discount_code)
);

CREATE TABLE order_discount (
    order_id       INT            NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    discount_code  VARCHAR(20)    NOT NULL REFERENCES discount(discount_code),
    amount         NUMERIC(10,0)  NOT NULL CHECK (amount >= 0),
    PRIMARY KEY (order_id, discount_code)
);

-- ---------- 退貨 ----------
CREATE TABLE return_request (
    return_id      SERIAL        PRIMARY KEY,
    order_id       INT           NOT NULL UNIQUE REFERENCES orders(order_id),
    requested_at   TIMESTAMP     NOT NULL DEFAULT now(),
    reason         VARCHAR(300)  NOT NULL,
    status         VARCHAR(10)   NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'approved', 'rejected')),
    processed_by   INT           REFERENCES users(user_id),
    processed_at   TIMESTAMP,
    reject_reason  VARCHAR(300),
    refund_total   NUMERIC(10,0) CHECK (refund_total >= 0),   -- 核准後依 BR-26 計算
    CHECK ((status = 'pending') = (processed_by IS NULL AND processed_at IS NULL)),
    CHECK ((status = 'rejected') = (reject_reason IS NOT NULL))
);

-- 每筆訂單最多一筆退貨申請（return_request.order_id UNIQUE），所以 order_id 就能識別退貨申請
CREATE TABLE return_item (
    order_id       INT            NOT NULL REFERENCES return_request(order_id) ON DELETE CASCADE,
    item_no        SMALLINT       NOT NULL,
    return_qty     INT            NOT NULL CHECK (return_qty > 0),
    refund_amount  NUMERIC(10,0)  CHECK (refund_amount >= 0),
    PRIMARY KEY (order_id, item_no),
    FOREIGN KEY (order_id, item_no) REFERENCES order_item (order_id, item_no)   -- 只能退這張訂單的明細
);

-- ---------- 商店評價（選配） ----------
CREATE TABLE store_review (
    order_id     INT           NOT NULL REFERENCES orders(order_id),
    store_id     INT           NOT NULL REFERENCES store(store_id),
    rating       SMALLINT      NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment      VARCHAR(500),
    reviewed_at  TIMESTAMP     NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, store_id)
);

-- ---------- 系統參數 ----------
CREATE TABLE system_setting (
    setting_key    VARCHAR(30)   PRIMARY KEY,
    setting_value  VARCHAR(50)   NOT NULL,
    description    VARCHAR(100)
);

-- ---------- 檢視表 ----------
-- 訂單總額（BR-09）：total = 商品小計 − 折扣合計（特殊活動＋季節性＋運費折扣）+ 稅 + 基本運費
CREATE VIEW v_orders AS
SELECT o.*, o.subtotal - o.discount_total + o.tax + o.shipping_fee AS total
FROM orders o;
