-- FUWA FUWA e-Shop 資料庫 schema（Phase 2 草稿，PostgreSQL 16+）
-- 由 ER Diagram 轉換而來；Phase 3 會再補上初始資料與 trigger。

CREATE EXTENSION IF NOT EXISTS btree_gist;   -- EXCLUDE 約束需要用 = 比較整數欄位

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
    total              NUMERIC(10,0)  NOT NULL CHECK (total >= 0),
    status             VARCHAR(10)    NOT NULL DEFAULT 'received'
                       CHECK (status IN ('received', 'processing', 'shipping',
                                         'closed', 'cancelled', 'returned')),
    paid_at            TIMESTAMP      NOT NULL
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
    ),
    UNIQUE (discount_code, discount_type, start_date, end_date)   -- 給 product_discount 的複合外鍵用
);

CREATE TABLE product_discount (
    product_id     INT          NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    discount_code  VARCHAR(20)  NOT NULL,
    discount_type  VARCHAR(15)  NOT NULL DEFAULT 'special_event'
                   CHECK (discount_type = 'special_event'),
    start_date     DATE         NOT NULL,
    end_date       DATE         NOT NULL,
    PRIMARY KEY (product_id, discount_code),
    FOREIGN KEY (discount_code, discount_type, start_date, end_date)
        REFERENCES discount (discount_code, discount_type, start_date, end_date)
        ON UPDATE CASCADE ON DELETE CASCADE,
    -- BR-13：同一商品的特殊活動折扣期間不得重疊（含首尾兩日）
    EXCLUDE USING gist (product_id WITH =,
                        daterange(start_date, end_date, '[]') WITH &&)
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
    CHECK ((status = 'pending') = (processed_by IS NULL AND processed_at IS NULL)),
    CHECK ((status = 'rejected') = (reject_reason IS NOT NULL)),
    UNIQUE (return_id, order_id)   -- 給 return_item 的複合外鍵用
);

CREATE TABLE return_item (
    return_id      INT            NOT NULL,
    order_id       INT            NOT NULL,
    item_no        SMALLINT       NOT NULL,
    return_qty     INT            NOT NULL CHECK (return_qty > 0),
    refund_amount  NUMERIC(10,0)  CHECK (refund_amount >= 0),
    PRIMARY KEY (return_id, item_no),
    FOREIGN KEY (return_id, order_id) REFERENCES return_request (return_id, order_id) ON DELETE CASCADE,
    FOREIGN KEY (order_id, item_no)   REFERENCES order_item (order_id, item_no)
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
