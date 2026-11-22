"""Codex 交叉驗證後補上的測試：金額邊界、直接改資料庫的 UPDATE 漏洞、操作者檢查與併發。"""
import threading
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db import SessionLocal, set_actor
from app.models import CartItem, Product, ReturnRequest, User
from app.services import orders as svc
from app.services.pricing import quote
from tests.conftest import login

DAY = date(2026, 11, 22)


def clean_discounts(db, *rows):
    """停用種子折扣，換成測試自己的折扣（期間很長，不受日期影響）。"""
    db.execute(text("UPDATE discount SET is_active = false"))
    for code, dtype, rate, min_amount, buy, free in rows:
        db.execute(text("INSERT INTO discount (discount_code, discount_type, description, start_date, end_date, "
                        "rate, min_amount, buy_qty, free_qty) VALUES (:c, :t, 'test', '2000-01-01', '2099-12-31', "
                        ":r, :m, :b, :f)"), {"c": code, "t": dtype, "r": rate, "m": min_amount, "b": buy, "f": free})
    db.commit()


def new_product(db, price: int, stock: int = 100) -> Product:
    pid = db.execute(text("INSERT INTO product (store_id, name, price, stock) VALUES (1, 'T', :p, :s) "
                          "RETURNING product_id"), {"p": price, "s": stock}).scalar()
    db.commit()
    return db.get(Product, pid)


# ---------------- 金額邊界（BR-10、BR-12、BR-16） ----------------

def test_buy_x_get_y_groups_and_remainder(db):
    clean_discounts(db, ("EVT-T", "special_event", None, None, 2, 1))
    p = new_product(db, 100)
    db.execute(text("INSERT INTO product_discount VALUES (:p, 'EVT-T')"), {"p": p.product_id})
    db.commit()
    assert quote(db, [(p, 2)], DAY).event_discount == 0      # 不足一組
    assert quote(db, [(p, 3)], DAY).event_discount == 100    # 剛好一組
    assert quote(db, [(p, 5)], DAY).event_discount == 100    # 一組＋餘 2 件
    assert quote(db, [(p, 7)], DAY).event_discount == 200    # 兩組＋餘 1 件


def test_free_shipping_threshold_uses_discounted_amount(db):
    clean_discounts(db, ("SHP-T", "shipping", None, 1000, None, None))
    assert quote(db, [(new_product(db, 1000), 1)], DAY).shipping_discount == 100    # 剛好達門檻
    assert quote(db, [(new_product(db, 999), 1)], DAY).shipping_discount == 0
    clean_discounts(db, ("SHP-T2", "shipping", None, 1000, None, None), ("SEA-T", "seasonal", 0.1, None, None, None))
    q = quote(db, [(new_product(db, 1050), 1)], DAY)                                # 小計過門檻，折扣後 945 未達
    assert (q.subtotal, q.tax_base, q.shipping_discount) == (1050, 945, 0)


def test_multiple_shipping_policies_any_threshold(db):
    clean_discounts(db, ("SHP-A", "shipping", None, 2000, None, None), ("SHP-B", "shipping", None, 500, None, None))
    q = quote(db, [(new_product(db, 600), 1)], DAY)
    assert q.shipping_discount == 100
    assert [a.discount_code for a in q.applied] == ["SHP-B"]


def test_tax_rounds_half_up(db):
    clean_discounts(db)
    assert quote(db, [(new_product(db, 10), 1)], DAY).tax == 1       # 0.5 → 1
    assert quote(db, [(new_product(db, 30), 1)], DAY).tax == 2       # 1.5 → 2


# ---------------- DMS 驗證（BR-15、BR-16、BR-17） ----------------

@pytest.mark.parametrize("body", [
    {"discount_type": "seasonal", "rate": 0},
    {"discount_type": "seasonal", "rate": 1},
    {"discount_type": "special_event", "buy_qty": 0, "free_qty": 1, "product_ids": [1]},
    {"discount_type": "special_event", "buy_qty": 2, "product_ids": [1]},
    {"discount_type": "special_event", "rate": 0.1, "buy_qty": 2, "free_qty": 1, "product_ids": [1]},
    {"discount_type": "special_event", "product_ids": [1]},
    {"discount_type": "seasonal", "rate": 0.1, "product_ids": [1]},
])
def test_invalid_discount_rules_rejected(client, staff_h, body):
    payload = {"description": "x", "start_date": "2030-01-01", "end_date": "2030-01-31", **body}
    assert client.post("/api/discounts/", headers=staff_h, json=payload).status_code in (409, 422)


def test_second_return_after_rejection_rejected(client, alice_h, staff_h, db):
    alice, staff = db.get(User, 4), db.get(User, 2)
    db.add(CartItem(user_id=4, product_id=1, quantity=1))
    db.commit()
    o = svc.checkout(db, alice, "a", "b", "c")
    svc.advance_status(db, o, staff, "processing")
    db.commit()
    body = {"order_id": o.order_id, "reason": "x", "items": [{"item_no": 1, "return_qty": 1}]}
    rid = client.post("/api/returns/", headers=alice_h, json=body).json()["return_id"]
    assert client.post(f"/api/returns/{rid}/reject", headers=staff_h, json={"reject_reason": "不符"}).status_code == 200
    r = client.post("/api/returns/", headers=alice_h, json=body)
    assert r.status_code == 409 and "BR-25" in r.text


# ---------------- 直接改資料庫的漏洞（trigger） ----------------

def _processing_order(db, items=((1, 2),)):
    alice, staff = db.get(User, 4), db.get(User, 2)
    for pid, q in items:
        db.add(CartItem(user_id=4, product_id=pid, quantity=q))
    db.commit()
    o = svc.checkout(db, alice, "a", "b", "c")
    svc.advance_status(db, o, staff, "processing")
    db.commit()
    return o


def test_status_update_requires_staff_actor(db):
    o = _processing_order(db)
    with pytest.raises(DBAPIError, match="BR-21：變更訂單狀態須以 app.user_id"):
        db.execute(text("UPDATE orders SET status='shipping' WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()
    set_actor(db, 4)  # 顧客不能推進狀態
    with pytest.raises(DBAPIError, match="BR-21：只有工作人員"):
        db.execute(text("UPDATE orders SET status='shipping' WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()


def test_cancel_only_by_owner(db):
    db.add(CartItem(user_id=4, product_id=1, quantity=1))
    db.commit()
    o = svc.checkout(db, db.get(User, 4), "a", "b", "c")
    db.commit()
    set_actor(db, 5)  # bob 不能取消 alice 的訂單
    with pytest.raises(DBAPIError, match="BR-21：只有下單的顧客"):
        db.execute(text("UPDATE orders SET status='cancelled' WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()


def test_returned_requires_approved_return(db):
    o = _processing_order(db)
    set_actor(db, 2)
    with pytest.raises(DBAPIError, match="BR-19：沒有已核准的退貨申請"):
        db.execute(text("UPDATE orders SET status='returned' WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()


def test_return_item_and_request_updates_guarded(db):
    o = _processing_order(db)
    rr = svc.create_return(db, o, "x", [(1, 1)])
    db.commit()
    with pytest.raises(DBAPIError, match="BR-25：退貨數量"):
        db.execute(text("UPDATE return_item SET return_qty = 9 WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()
    svc.approve_return(db, db.get(ReturnRequest, rr.return_id), db.get(User, 2))
    db.commit()
    with pytest.raises(DBAPIError, match="BR-25：退貨申請已處理"):
        db.execute(text("UPDATE return_request SET refund_total = 0 WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()
    with pytest.raises(DBAPIError, match="BR-25：已處理的退貨申請"):
        db.execute(text("UPDATE return_item SET return_qty = 2 WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()


def test_review_update_cannot_move_to_unpurchased_store(db):
    o = _processing_order(db)  # 只買了商店 1 的商品
    staff = db.get(User, 2)
    svc.advance_status(db, o, staff, "shipping")
    svc.advance_status(db, o, staff, "closed")
    db.commit()
    db.execute(text("INSERT INTO store_review (order_id, store_id, rating) VALUES (:o, 1, 5)"), {"o": o.order_id})
    db.commit()
    with pytest.raises(DBAPIError, match="BR-24"):
        db.execute(text("UPDATE store_review SET store_id = 2 WHERE order_id=:o"), {"o": o.order_id})
    db.rollback()


def test_customer_deletion_blocked_when_referenced(db):
    db.add(CartItem(user_id=4, product_id=1, quantity=1))
    db.commit()
    svc.checkout(db, db.get(User, 4), "a", "b", "c")
    db.commit()
    with pytest.raises(DBAPIError):                       # BR-20：有訂單的顧客不能刪除
        db.execute(text("DELETE FROM users WHERE user_id = 4"))
    db.rollback()


def test_staff_cannot_use_admin_endpoints(client, staff_h):
    assert client.get("/api/admin/users", headers=staff_h).status_code == 403
    assert client.post("/api/admin/users", headers=staff_h, json={}).status_code in (403, 422)


# ---------------- 併發（兩個資料庫連線同時操作） ----------------

def _run_parallel(*fns):
    barrier = threading.Barrier(len(fns))
    results = [None] * len(fns)

    def wrap(i, fn):
        s = SessionLocal()
        try:
            barrier.wait()
            results[i] = fn(s)
            s.commit()
        except (HTTPException, DBAPIError) as e:
            s.rollback()
            results[i] = e
        finally:
            s.close()

    threads = [threading.Thread(target=wrap, args=(i, f)) for i, f in enumerate(fns)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def test_concurrent_checkout_same_cart_creates_one_order(db):
    db.add(CartItem(user_id=4, product_id=1, quantity=2))
    db.commit()
    stock_before = db.get(Product, 1).stock

    def go(s):
        return svc.checkout(s, s.get(User, 4), "a", "b", "c").order_id

    results = _run_parallel(go, go)
    assert sum(isinstance(r, int) for r in results) == 1
    assert any(isinstance(r, HTTPException) and "BR-07" in r.detail for r in results)
    db.expire_all()
    assert db.get(Product, 1).stock == stock_before - 2


def test_concurrent_double_approve_only_once(db):
    o = _processing_order(db)
    rid = svc.create_return(db, o, "x", [(1, 2)]).return_id
    db.commit()
    stock_before = db.get(Product, 1).stock

    def go(s):
        return svc.approve_return(s, s.get(ReturnRequest, rid), s.get(User, 2)).status

    results = _run_parallel(go, go)
    assert results.count("approved") == 1
    db.expire_all()
    assert db.get(Product, 1).stock == stock_before + 2      # 只回補一次


def test_concurrent_cancel_and_checkout_keep_stock_correct(db):
    db.add(CartItem(user_id=4, product_id=1, quantity=3))
    db.commit()
    o = svc.checkout(db, db.get(User, 4), "a", "b", "c")
    db.add(CartItem(user_id=5, product_id=1, quantity=1))
    db.commit()
    stock_before = db.get(Product, 1).stock

    results = _run_parallel(
        lambda s: svc.cancel_order(s, s.get(type(o), o.order_id), s.get(User, 4)).status,
        lambda s: svc.checkout(s, s.get(User, 5), "a", "b", "c").order_id)
    assert results[0] == "cancelled" and isinstance(results[1], int)
    db.expire_all()
    assert db.get(Product, 1).stock == stock_before + 3 - 1


def test_concurrent_admins_cannot_disable_each_other(db):
    """admin(1) 與 manager(3) 是僅有的兩位管理員，同時停用對方時至少一筆要失敗。"""
    def disable(uid):
        def fn(s):
            s.execute(text("UPDATE users SET is_active = false WHERE user_id = :u"), {"u": uid})
            s.commit()
            return "ok"
        return fn

    results = _run_parallel(disable(3), disable(1))
    assert results.count("ok") == 1
    db.expire_all()
    assert db.execute(text("SELECT count(*) FROM users u JOIN user_role r USING (user_id) "
                           "WHERE r.role = 'admin' AND u.is_active")).scalar() == 1


def test_login_unaffected(client):
    assert login(client, "alice", "customer123")
