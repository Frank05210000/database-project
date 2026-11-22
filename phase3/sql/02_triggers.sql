-- FUWA FUWA e-Shop：trigger（Phase 2 SRS 4.3 節「需要 trigger 或交易處理的規則」）
-- BR-06 / BR-07 的結帳交易在後端 app/services/checkout.py 以 SELECT … FOR UPDATE 實作；
-- 以下 trigger 是資料庫層的最後一道防線，就算繞過後端直接改資料也會被拒絕。
-- 所有違規都以 RAISE EXCEPTION（SQLSTATE P0001）回報，訊息以規則編號開頭，後端轉成 HTTP 409。

-- 目前操作的使用者：後端在交易開始時執行 SET LOCAL app.user_id = <id>
CREATE OR REPLACE FUNCTION fn_actor() RETURNS INT AS $$
    SELECT NULLIF(current_setting('app.user_id', true), '')::INT
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION fn_has_role(p_user INT, p_role TEXT) RETURNS BOOLEAN AS $$
    SELECT EXISTS (SELECT 1 FROM user_role WHERE user_id = p_user AND role = p_role)
$$ LANGUAGE sql STABLE;

-- ---------- 工作人員商店隸屬（BR-21） ----------
CREATE OR REPLACE FUNCTION trg_store_staff_check() RETURNS trigger AS $$
BEGIN
    IF NOT fn_has_role(NEW.user_id, 'staff') THEN
        RAISE EXCEPTION 'BR-21：只有工作人員可以設定隸屬商店';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER store_staff_check BEFORE INSERT OR UPDATE ON store_staff
    FOR EACH ROW EXECUTE FUNCTION trg_store_staff_check();

CREATE OR REPLACE FUNCTION trg_staff_role_cleanup() RETURNS trigger AS $$
BEGIN
    IF OLD.role = 'staff' THEN
        DELETE FROM store_staff WHERE user_id = OLD.user_id;
    END IF;
    RETURN OLD;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER staff_role_cleanup AFTER DELETE ON user_role
    FOR EACH ROW EXECUTE FUNCTION trg_staff_role_cleanup();

-- ---------- 商品：自動更新 updated_at ----------
CREATE OR REPLACE FUNCTION trg_product_touch() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER product_touch BEFORE UPDATE ON product
    FOR EACH ROW EXECUTE FUNCTION trg_product_touch();

-- ---------- 購物車：只有顧客能加入（BR-21），數量不得超過庫存（BR-06） ----------
CREATE OR REPLACE FUNCTION trg_cart_item_check() RETURNS trigger AS $$
DECLARE v_stock INT; v_listed BOOLEAN;
BEGIN
    IF NOT fn_has_role(NEW.user_id, 'customer') THEN
        RAISE EXCEPTION 'BR-21：只有顧客可以使用購物車';
    END IF;
    SELECT stock, is_listed INTO v_stock, v_listed FROM product WHERE product_id = NEW.product_id;
    IF NOT v_listed THEN
        RAISE EXCEPTION 'PMS：商品已下架，不能加入購物車';
    END IF;
    IF NEW.quantity > v_stock THEN
        RAISE EXCEPTION 'BR-06：購買數量 % 超過目前庫存 %', NEW.quantity, v_stock;
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER cart_item_check BEFORE INSERT OR UPDATE ON cart_item
    FOR EACH ROW EXECUTE FUNCTION trg_cart_item_check();

-- ---------- 訂單：只有啟用中的顧客能下單（BR-21） ----------
CREATE OR REPLACE FUNCTION trg_orders_insert_check() RETURNS trigger AS $$
BEGIN
    IF NOT fn_has_role(NEW.user_id, 'customer') THEN
        RAISE EXCEPTION 'BR-21：只有顧客可以下單';
    END IF;
    IF NEW.status <> 'received' THEN
        RAISE EXCEPTION 'OMS-F-004：新訂單的狀態必須是 received';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER orders_insert_check BEFORE INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION trg_orders_insert_check();

-- ---------- 訂單狀態流轉（BR-19、BR-25） ----------
CREATE OR REPLACE FUNCTION trg_orders_status_check() RETURNS trigger AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;
    IF OLD.status IN ('cancelled', 'returned') THEN
        RAISE EXCEPTION 'BR-19：訂單已是最終狀態 %，不可再變更', OLD.status;
    END IF;
    IF NOT ((OLD.status, NEW.status) IN (('received', 'processing'), ('processing', 'shipping'),
                                         ('shipping', 'closed'), ('received', 'cancelled'))
            OR (NEW.status = 'returned' AND OLD.status IN ('processing', 'shipping', 'closed'))) THEN
        RAISE EXCEPTION 'BR-19：訂單狀態不可由 % 變更為 %', OLD.status, NEW.status;
    END IF;
    IF NEW.status IN ('processing', 'shipping', 'closed') AND EXISTS (
            SELECT 1 FROM return_request WHERE order_id = NEW.order_id AND status = 'pending') THEN
        RAISE EXCEPTION 'BR-25：訂單有待審核的退貨申請，不可更新狀態';
    END IF;
    IF NEW.status = 'returned' AND EXISTS (
            SELECT 1 FROM order_item oi
            WHERE oi.order_id = NEW.order_id
              AND oi.quantity > COALESCE((
                    SELECT SUM(ri.return_qty)
                    FROM return_item ri JOIN return_request rr ON rr.return_id = ri.return_id
                    WHERE rr.status = 'approved' AND ri.order_id = oi.order_id AND ri.item_no = oi.item_no), 0)) THEN
        RAISE EXCEPTION 'BR-19：訂單尚有商品未退貨，不可改為 returned';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER orders_status_check BEFORE UPDATE OF status ON orders
    FOR EACH ROW EXECUTE FUNCTION trg_orders_status_check();

-- 自動寫入狀態歷程（DR-07）：新增訂單與每次狀態變更都記一筆
CREATE OR REPLACE FUNCTION trg_orders_status_log() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;
    INSERT INTO order_status_history (order_id, seq_no, status, changed_at, changed_by)
    VALUES (NEW.order_id,
            COALESCE((SELECT MAX(seq_no) FROM order_status_history WHERE order_id = NEW.order_id), 0) + 1,
            NEW.status,
            CASE WHEN TG_OP = 'INSERT' THEN NEW.order_time ELSE now() END,
            COALESCE(fn_actor(), NEW.user_id));
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER orders_status_log AFTER INSERT OR UPDATE OF status ON orders
    FOR EACH ROW EXECUTE FUNCTION trg_orders_status_log();

-- ---------- 退貨申請（BR-25、BR-21） ----------
CREATE OR REPLACE FUNCTION trg_return_request_insert() RETURNS trigger AS $$
DECLARE v_status TEXT;
BEGIN
    SELECT status INTO v_status FROM orders WHERE order_id = NEW.order_id;
    IF v_status NOT IN ('processing', 'shipping', 'closed') THEN
        RAISE EXCEPTION 'BR-25：只有 processing、shipping、closed 的訂單可以申請退貨（目前為 %）', v_status;
    END IF;
    IF NEW.status <> 'pending' THEN
        RAISE EXCEPTION 'BR-25：新的退貨申請必須是 pending';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER return_request_insert BEFORE INSERT ON return_request
    FOR EACH ROW EXECUTE FUNCTION trg_return_request_insert();

CREATE OR REPLACE FUNCTION trg_return_request_update() RETURNS trigger AS $$
BEGIN
    IF OLD.status <> 'pending' AND NEW.status IS DISTINCT FROM OLD.status THEN
        RAISE EXCEPTION 'BR-25：退貨申請已處理（%），不可再變更', OLD.status;
    END IF;
    IF NEW.status <> 'pending' AND NOT fn_has_role(NEW.processed_by, 'staff') THEN
        RAISE EXCEPTION 'BR-21：只有工作人員可以處理退貨申請';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER return_request_update BEFORE UPDATE ON return_request
    FOR EACH ROW EXECUTE FUNCTION trg_return_request_update();

CREATE OR REPLACE FUNCTION trg_return_item_insert() RETURNS trigger AS $$
DECLARE v_qty INT; v_status TEXT;
BEGIN
    SELECT quantity INTO v_qty FROM order_item WHERE order_id = NEW.order_id AND item_no = NEW.item_no;
    IF NEW.return_qty > v_qty THEN
        RAISE EXCEPTION 'BR-25：退貨數量 % 超過購買數量 %', NEW.return_qty, v_qty;
    END IF;
    SELECT status INTO v_status FROM return_request WHERE return_id = NEW.return_id;
    IF v_status <> 'pending' THEN
        RAISE EXCEPTION 'BR-25：已處理的退貨申請不可再新增商品';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER return_item_insert BEFORE INSERT ON return_item
    FOR EACH ROW EXECUTE FUNCTION trg_return_item_insert();

-- ---------- 商店評價（BR-24，選配） ----------
CREATE OR REPLACE FUNCTION trg_store_review_insert() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM orders WHERE order_id = NEW.order_id AND status = 'closed') THEN
        RAISE EXCEPTION 'BR-24：只能評價狀態為 closed 的訂單';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM order_item oi JOIN product p ON p.product_id = oi.product_id
                   WHERE oi.order_id = NEW.order_id AND p.store_id = NEW.store_id) THEN
        RAISE EXCEPTION 'BR-24：這筆訂單沒有購買該商店的商品';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER store_review_insert BEFORE INSERT ON store_review
    FOR EACH ROW EXECUTE FUNCTION trg_store_review_insert();

-- ---------- 折扣代碼建立後不可修改（BR-18） ----------
CREATE OR REPLACE FUNCTION trg_discount_code_immutable() RETURNS trigger AS $$
BEGIN
    IF NEW.discount_code <> OLD.discount_code OR NEW.discount_type <> OLD.discount_type THEN
        RAISE EXCEPTION 'BR-18：折扣代碼與類型建立後不可修改';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER discount_code_immutable BEFORE UPDATE ON discount
    FOR EACH ROW EXECUTE FUNCTION trg_discount_code_immutable();

-- ---------- 至少保留一位啟用中的平台管理員 ----------
CREATE OR REPLACE FUNCTION trg_keep_one_admin() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM user_role r JOIN users u ON u.user_id = r.user_id
                   WHERE r.role = 'admin' AND u.is_active) THEN
        RAISE EXCEPTION 'AAS：系統至少要保留一位啟用中的平台管理員';
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER user_role_keep_admin AFTER DELETE ON user_role
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_keep_one_admin();
CREATE CONSTRAINT TRIGGER users_keep_admin AFTER UPDATE OF is_active ON users
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_keep_one_admin();
