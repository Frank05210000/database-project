"""直接測試金額計算與訂單交易服務（BR-09～BR-16、BR-19、BR-25、BR-26），不經過 HTTP。"""
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models import CartItem, Order, Product, User
from app.services import orders as svc
from app.services.pricing import quote

DAY = date(2026, 11, 22)  # 種子折扣：SHP-0001、SEA-0001(5%)、SEA-0002(10%)、EVT-0001(貓跳台 8 折)、EVT-0002(主食罐買2送1)


def test_quote_order_of_operations(db):
    can, tower = db.get(Product, 5), db.get(Product, 9)
    q = quote(db, [(can, 3), (tower, 1)], DAY)
    assert q.subtotal == 65 * 3 + 1680
    assert q.event_discount == 65 + 336           # 買 2 送 1 免 1 罐；8 折折 336
    assert q.seasonal_discount == 74 + 140        # 1474×5%=73.7→74；1400×10%=140（BR-12 連續疊加）
    assert q.tax_base == 1260
    assert q.tax == 63                            # 稅以兩項折扣後金額計算（BR-10）
    assert q.shipping_fee == 100 and q.shipping_discount == 100   # 1260 ≥ 1000 免運
    assert q.total == 1323
    assert q.total == q.subtotal - q.discount_total + q.tax + q.shipping_fee
    assert {a.discount_code for a in q.applied} == {"EVT-0001", "EVT-0002", "SEA-0001", "SEA-0002", "SHP-0001"}


def test_quote_below_free_shipping_and_outside_period(db):
    ball = db.get(Product, 1)
    q = quote(db, [(ball, 2)], date(2026, 9, 1))  # 9 月沒有季節性折扣，EVT-0003 已過期
    assert (q.subtotal, q.event_discount, q.seasonal_discount, q.tax, q.shipping_discount, q.total) == (360, 0, 0, 18, 0, 478)
    q = quote(db, [(ball, 2)], date(2026, 6, 30))  # 期間含最後一天（BR-14）
    assert q.event_discount == 54


def _cart(db, user_id, items):
    for pid, qty in items:
        db.add(CartItem(user_id=user_id, product_id=pid, quantity=qty))
    db.commit()


def test_checkout_cancel_restock(db):
    alice = db.get(User, 4)
    _cart(db, 4, [(5, 3), (9, 1)])
    order = svc.checkout(db, alice, "陳愛麗", "0912", "台北", order_time=datetime(2026, 11, 22, 10))
    db.commit()
    assert order.total == 1323 and order.status == "received"
    assert db.get(Product, 5).stock == 197 and db.get(Product, 9).stock == 14
    assert [h.status for h in order.history] == ["received"]
    svc.cancel_order(db, order, alice)
    db.commit()
    assert db.get(Product, 5).stock == 200
    db.refresh(order)
    assert [h.status for h in order.history] == ["received", "cancelled"]
    with pytest.raises(HTTPException):
        svc.cancel_order(db, order, alice)


def test_status_flow_trigger_rejects_skip(db):
    alice, staff = db.get(User, 4), db.get(User, 2)
    _cart(db, 4, [(1, 1)])
    order = svc.checkout(db, alice, "a", "b", "c")
    db.commit()
    with pytest.raises(HTTPException):
        svc.advance_status(db, order, staff, "shipping")
    # 繞過後端直接改資料庫，trigger 也會拒絕（BR-19）
    with pytest.raises(DBAPIError, match="BR-19"):
        db.execute(text("UPDATE orders SET status='closed' WHERE order_id=:o"), {"o": order.order_id})
    db.rollback()
    svc.advance_status(db, order, staff, "processing")
    db.commit()
    assert order.history[-1].changed_by == staff.user_id


def test_return_partial_then_full_refund(db):
    alice, staff = db.get(User, 4), db.get(User, 2)
    _cart(db, 4, [(5, 3), (9, 1)])
    order = svc.checkout(db, alice, "a", "b", "c", order_time=datetime(2026, 11, 22, 10))
    db.commit()
    svc.advance_status(db, order, staff, "processing")
    db.commit()
    by_pid = {it.product_id: it.item_no for it in order.items}
    rr = svc.create_return(db, order, "尺寸不合", [(by_pid[9], 1)])
    db.commit()
    with pytest.raises(HTTPException, match="BR-25"):
        svc.advance_status(db, order, staff, "shipping")       # 待審核時不能更新狀態
    svc.approve_return(db, rr, staff)
    db.commit()
    # (1323 − 0 實付運費) × 1344 ÷ 1474 = 1206.3 → 1206
    assert rr.items[0].refund_amount == 1206 and rr.refund_total == 1206
    assert order.status == "processing"                         # 部分退貨維持原狀態
    assert db.get(Product, 9).stock == 15
    with pytest.raises(HTTPException, match="BR-25"):
        svc.create_return(db, order, "again", [(by_pid[5], 1)])  # 每筆訂單只能申請一次


def test_full_return_in_processing_refunds_shipping(db):
    alice, staff = db.get(User, 4), db.get(User, 2)
    _cart(db, 4, [(1, 2)])
    order = svc.checkout(db, alice, "a", "b", "c", order_time=datetime(2026, 9, 1, 10))
    db.commit()
    assert order.total == 478
    svc.advance_status(db, order, staff, "processing")
    rr = svc.create_return(db, order, "不想要了", [(1, 2)])
    db.commit()
    svc.approve_return(db, rr, staff)
    db.commit()
    assert rr.items[0].refund_amount == 378 and rr.refund_total == 478   # 運費一併退還
    assert order.status == "returned"


def test_return_qty_over_purchase_rejected_by_trigger(db):
    alice, staff = db.get(User, 4), db.get(User, 2)
    _cart(db, 4, [(1, 1)])
    order = svc.checkout(db, alice, "a", "b", "c")
    svc.advance_status(db, order, staff, "processing")
    db.commit()
    with pytest.raises(HTTPException, match="BR-25"):
        svc.create_return(db, order, "x", [(1, 5)])
    db.execute(text("INSERT INTO return_request (order_id, reason) VALUES (:o, 'x')"), {"o": order.order_id})
    with pytest.raises(DBAPIError, match="BR-25"):
        db.execute(text("INSERT INTO return_item (order_id, item_no, return_qty) VALUES (:o, 1, 5)"), {"o": order.order_id})
    db.rollback()


def test_return_item_of_another_order_rejected(db):
    """退別張訂單的明細：(order_id, item_no) 外鍵參照 order_item，第 2 項不存在於這張訂單就被拒絕。"""
    alice, staff = db.get(User, 4), db.get(User, 2)
    db.add(CartItem(user_id=4, product_id=1, quantity=1))
    db.commit()
    o1 = svc.checkout(db, alice, "a", "b", "c")
    _cart(db, 4, [(2, 1), (3, 1)])
    o2 = svc.checkout(db, alice, "a", "b", "c")   # 這張有第 2 項
    svc.advance_status(db, o1, staff, "processing")
    db.commit()
    db.execute(text("INSERT INTO return_request (order_id, reason) VALUES (:o, 'x')"), {"o": o1.order_id})
    with pytest.raises(DBAPIError, match="return_item_order_id_item_no_fkey"):
        db.execute(text("INSERT INTO return_item (order_id, item_no, return_qty) VALUES (:o, 2, 1)"), {"o": o1.order_id})
    db.rollback()
    assert o2.order_id != o1.order_id


def test_event_discount_rules_enforced_by_trigger(db):
    """3NF 後 BR-13 由 trigger 檢查：期間重疊、季節性折扣掛商品、修改期間造成重疊都會被拒絕。"""
    # 期間重疊：EVT-0001 已套用在商品 9（2026-11-01～12-31）
    db.execute(text("INSERT INTO discount (discount_code, discount_type, description, start_date, end_date, rate) "
                    "VALUES ('EVT-T1', 'special_event', 't', '2026-12-31', '2027-01-15', 0.1)"))
    with pytest.raises(DBAPIError, match="BR-13.*EVT-0001"):
        db.execute(text("INSERT INTO product_discount VALUES (9, 'EVT-T1')"))
    db.rollback()
    # 季節性折扣不能掛到商品上
    with pytest.raises(DBAPIError, match="BR-13：只有特殊活動折扣"):
        db.execute(text("INSERT INTO product_discount VALUES (1, 'SEA-0001')"))
    db.rollback()
    # 不重疊的期間可以，之後把期間改成重疊會被拒絕
    db.execute(text("INSERT INTO discount (discount_code, discount_type, description, start_date, end_date, rate) "
                    "VALUES ('EVT-T2', 'special_event', 't', '2027-01-01', '2027-01-31', 0.1)"))
    db.execute(text("INSERT INTO product_discount VALUES (9, 'EVT-T2')"))
    db.commit()
    with pytest.raises(DBAPIError, match="BR-13.*EVT-0001"):
        db.execute(text("UPDATE discount SET start_date = '2026-12-20' WHERE discount_code = 'EVT-T2'"))
    db.rollback()


def test_checkout_rejects_over_stock_and_empty(db):
    alice = db.get(User, 4)
    with pytest.raises(HTTPException, match="BR-07"):
        svc.checkout(db, alice, "a", "b", "c")
    _cart(db, 4, [(14, 5)])
    db.execute(text("UPDATE product SET stock = 2 WHERE product_id = 14"))
    with pytest.raises(HTTPException, match="BR-06"):
        svc.checkout(db, alice, "a", "b", "c")
    db.rollback()
