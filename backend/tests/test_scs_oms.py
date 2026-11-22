"""SCS 購物車與 OMS 訂單 API（BR-05、BR-06、BR-07、BR-09～BR-12、BR-19、BR-21、BR-25）。

Token 直接由 security.create_token 產生，不依賴登入 API。
金額相關測試先停用種子折扣，改用期間很寬的自訂折扣，避免日期一過就失效。
"""
import pytest
from sqlalchemy import text

from app.security import create_token

STAFF, ALICE, BOB = 2, 4, 5


def H(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_token(user_id)}"}


def stable_discounts(db):
    """停用種子折扣，改用：EVT-9001 柔順梳毛刷(3) 8 折、SEA-9001 全館 9 折、SHP-9001 滿 1000 免運。"""
    db.execute(text("UPDATE discount SET is_active = false"))
    db.execute(text("""
        INSERT INTO discount (discount_code, discount_type, description, start_date, end_date, rate, min_amount)
        VALUES ('EVT-9001', 'special_event', '梳毛刷 8 折', '2000-01-01', '2099-12-31', 0.200, NULL),
               ('SEA-9001', 'seasonal', '全館 9 折', '2000-01-01', '2099-12-31', 0.100, NULL),
               ('SHP-9001', 'shipping', '滿 1000 免運', '2000-01-01', '2099-12-31', NULL, 1000)"""))
    db.execute(text("INSERT INTO product_discount (product_id, discount_code) VALUES (3, 'EVT-9001')"))
    db.commit()


def stock(db, pid: int) -> int:
    return db.execute(text("SELECT stock FROM product WHERE product_id = :p"), {"p": pid}).scalar()


def add(client, uid, pid, qty):
    return client.post("/api/cart/items", json={"product_id": pid, "quantity": qty}, headers=H(uid))


def place_order(client, uid=ALICE, items=((3, 2), (1, 1))) -> dict:
    for pid, qty in items:
        assert add(client, uid, pid, qty).status_code == 200
    r = client.post("/api/orders/", json={"recipient_name": "陳愛麗", "recipient_phone": "0912-345-678",
                                          "recipient_address": "台北市中正區"}, headers=H(uid))
    assert r.status_code == 201, r.text
    return r.json()


def advance(client, oid, *statuses):
    r = None
    for s in statuses:
        r = client.post(f"/api/orders/{oid}/status", json={"status": s}, headers=H(STAFF))
        assert r.status_code == 200, r.text
    return r.json() if r else None


# ---------- 購物車 ----------
def test_cart_crud_and_quote(client, db):
    stable_discounts(db)
    r = add(client, ALICE, 3, 1)
    assert r.status_code == 200
    r = add(client, ALICE, 3, 1)                      # 已在購物車則累加
    body = r.json()
    assert len(body["items"]) == 1 and body["items"][0]["quantity"] == 2
    p = body["items"][0]["product"]
    assert p["product_id"] == 3 and p["store_name"] == "FUWA FUWA 台中公益店" and p["price"] == 320
    assert p["event_discount"]["discount_code"] == "EVT-9001" and p["event_discount"]["rate"] == 0.2
    assert body["items"][0]["line_subtotal"] == 640

    body = add(client, ALICE, 1, 1).json()
    assert client.get("/api/cart/", headers=H(ALICE)).json() == body   # 寫入回傳與 GET 相同
    q = body["quote"]
    # 820 − 128（8 折）= 692；9 折折 69 → 623；稅 31；未滿 1000 運費 100
    assert (q["subtotal"], q["event_discount"], q["seasonal_discount"], q["tax_base"], q["tax"],
            q["shipping_fee"], q["shipping_discount"], q["total"]) == (820, 128, 69, 623, 31, 100, 0, 754)
    assert q["total"] == q["subtotal"] - q["discount_total"] + q["tax"] + q["shipping_fee"]
    assert {a["discount_code"] for a in q["applied_discounts"]} == {"EVT-9001", "SEA-9001"}

    body = client.put("/api/cart/items/1", json={"quantity": 5}, headers=H(ALICE)).json()
    assert {i["product"]["product_id"]: i["quantity"] for i in body["items"]} == {3: 2, 1: 5}
    body = client.delete("/api/cart/items/3", headers=H(ALICE)).json()
    assert [i["product"]["product_id"] for i in body["items"]] == [1]
    body = client.delete("/api/cart/", headers=H(ALICE)).json()
    assert body["items"] == [] and body["quote"]["total"] == 0


@pytest.mark.parametrize("qty", [0, -3])
def test_cart_rejects_non_positive_quantity(client, qty):
    r = add(client, ALICE, 1, qty)
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-05")
    add(client, ALICE, 1, 1)
    r = client.put("/api/cart/items/1", json={"quantity": qty}, headers=H(ALICE))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-05")


def test_cart_rejects_non_integer_quantity(client):
    assert add(client, ALICE, 1, 1.5).status_code == 422


def test_cart_quantity_over_stock(client):
    r = add(client, ALICE, 14, 11)                     # 自動餵食器庫存 10
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-06")
    assert add(client, ALICE, 14, 10).status_code == 200
    r = add(client, ALICE, 14, 1)                      # 累加後超過庫存
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-06")
    r = client.put("/api/cart/items/14", json={"quantity": 11}, headers=H(ALICE))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-06")


def test_cart_unlisted_and_missing_product(client):
    assert add(client, ALICE, 15, 1).status_code == 409   # 已下架
    assert add(client, ALICE, 999, 1).status_code == 404


def test_cart_requires_customer(client):
    assert client.get("/api/cart/").status_code == 401
    r = client.get("/api/cart/", headers=H(STAFF))
    assert r.status_code == 403 and "BR-21" in r.json()["detail"]
    assert add(client, STAFF, 1, 1).status_code == 403


# ---------- 結帳與訂單 ----------
def test_checkout_preview_and_happy_path(client, db):
    stable_discounts(db)
    add(client, ALICE, 3, 2)
    add(client, ALICE, 1, 1)
    r = client.get("/api/orders/checkout-preview", headers=H(ALICE))
    assert r.status_code == 200
    pv = r.json()
    assert pv["recipient"] == {"name": "陳愛麗", "phone": "0912-345-678", "address": "台北市中正區八德路一段 10 號"}
    assert pv["quote"]["total"] == 754 and pv["quote"]["tax"] == 31

    before3, before1 = stock(db, 3), stock(db, 1)
    r = client.post("/api/orders/", json={"recipient_name": "陳愛麗", "recipient_phone": "0912",
                                          "recipient_address": "台北"}, headers=H(ALICE))
    assert r.status_code == 201, r.text
    o = r.json()
    assert o["status"] == "received" and o["total"] == pv["quote"]["total"]
    assert (o["subtotal"], o["discount_total"], o["tax"], o["shipping_fee"], o["shipping_discount"]) == (820, 197, 31, 100, 0)
    assert o["total"] == o["subtotal"] - o["discount_total"] + o["tax"] + o["shipping_fee"]
    assert o["item_count"] == 3 and o["customer"]["loginid"] == "alice"
    assert [d["discount_code"] for d in o["discounts"]] == ["EVT-9001", "SEA-9001"]
    assert o["discounts"][0]["discount_type"] == "special_event" and o["discounts"][0]["amount"] == 128
    items = {i["product_id"]: i for i in o["items"]}
    assert items[3]["event_discount"] == 128 and items[3]["line_subtotal"] == 640
    assert items[3]["store_name"] == "FUWA FUWA 台中公益店" and items[3]["image_url"] == "/images/brush.webp"
    assert [h["status"] for h in o["history"]] == ["received"] and o["history"][0]["changed_by_name"] == "陳愛麗"
    assert o["next_status"] == "processing" and o["can_cancel"] and not o["can_return"]
    assert o["return_request"] is None

    db.expire_all()
    assert stock(db, 3) == before3 - 2 and stock(db, 1) == before1 - 1      # 庫存扣除
    assert client.get("/api/cart/", headers=H(ALICE)).json()["items"] == []  # 購物車清空

    oid = o["order_id"]
    o = advance(client, oid, "processing")
    assert o["can_cancel"] is False and o["can_return"] is True and o["next_status"] == "shipping"
    o = advance(client, oid, "shipping", "closed")
    assert o["status"] == "closed" and o["next_status"] is None
    assert [h["status"] for h in o["history"]] == ["received", "processing", "shipping", "closed"]
    assert [h["changed_by_name"] for h in o["history"][1:]] == ["王小明"] * 3

    mine = client.get("/api/orders/mine", headers=H(ALICE)).json()
    assert [m["order_id"] for m in mine] == [oid] and mine[0]["status"] == "closed"
    assert client.get("/api/orders/mine", headers=H(BOB)).json() == []


def test_free_shipping_discount_recorded(client, db):
    stable_discounts(db)
    o = place_order(client, items=((4, 1),))             # 2800 → 9 折 2520 ≥ 1000
    assert o["shipping_fee"] == 100 and o["shipping_discount"] == 100
    assert "SHP-9001" in [d["discount_code"] for d in o["discounts"]]
    assert o["total"] == 2520 + 126


def test_checkout_empty_cart(client):
    r = client.post("/api/orders/", json={"recipient_name": "a", "recipient_phone": "b", "recipient_address": "c"},
                    headers=H(ALICE))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-07")


def test_checkout_requires_recipient(client):
    add(client, ALICE, 1, 1)
    r = client.post("/api/orders/", json={"recipient_name": " ", "recipient_phone": "b", "recipient_address": "c"},
                    headers=H(ALICE))
    assert r.status_code == 422
    assert client.post("/api/orders/", json={"recipient_name": "a"}, headers=H(ALICE)).status_code == 422


def test_checkout_stock_dropped_after_adding(client, db):
    add(client, ALICE, 14, 5)
    db.execute(text("UPDATE product SET stock = 2 WHERE product_id = 14"))
    db.commit()
    r = client.post("/api/orders/", json={"recipient_name": "a", "recipient_phone": "b", "recipient_address": "c"},
                    headers=H(ALICE))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-06")
    db.expire_all()
    assert stock(db, 14) == 2


def test_status_cannot_skip(client):
    oid = place_order(client)["order_id"]
    r = client.post(f"/api/orders/{oid}/status", json={"status": "shipping"}, headers=H(STAFF))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-19")
    r = client.post(f"/api/orders/{oid}/status", json={"status": "cancelled"}, headers=H(STAFF))
    assert r.status_code == 409
    r = client.post(f"/api/orders/{oid}/status", json={"status": "processing"}, headers=H(ALICE))
    assert r.status_code == 403                         # 顧客不能改狀態


def test_customer_cancel(client, db):
    o = place_order(client)
    oid = o["order_id"]
    s3 = stock(db, 3)
    r = client.post(f"/api/orders/{oid}/cancel", headers=H(BOB))
    assert r.status_code == 403                         # 不能取消別人的訂單
    r = client.post(f"/api/orders/{oid}/cancel", headers=H(ALICE))
    assert r.status_code == 200
    o = r.json()
    assert o["status"] == "cancelled" and o["can_cancel"] is False and o["next_status"] is None
    assert [h["status"] for h in o["history"]] == ["received", "cancelled"]
    db.expire_all()
    assert stock(db, 3) == s3 + 2                       # 回補庫存
    r = client.post(f"/api/orders/{oid}/status", json={"status": "processing"}, headers=H(STAFF))
    assert r.status_code == 409                         # 最終狀態


def test_customer_cannot_cancel_processing(client):
    oid = place_order(client)["order_id"]
    advance(client, oid, "processing")
    r = client.post(f"/api/orders/{oid}/cancel", headers=H(ALICE))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-19")


def test_order_access_control(client):
    oid = place_order(client)["order_id"]
    assert client.get(f"/api/orders/{oid}", headers=H(ALICE)).status_code == 200
    assert client.get(f"/api/orders/{oid}", headers=H(STAFF)).status_code == 200
    assert client.get(f"/api/orders/{oid}", headers=H(BOB)).status_code in (403, 404)
    assert client.get(f"/api/orders/{oid}").status_code == 401
    assert client.get("/api/orders/99999", headers=H(STAFF)).status_code == 404
    assert client.get("/api/orders/", headers=H(ALICE)).status_code == 403   # 全部訂單僅 staff
    assert client.get("/api/orders/mine", headers=H(STAFF)).status_code == 403


def test_staff_list_filters(client, db):
    a = place_order(client, ALICE, ((1, 1),))["order_id"]
    b = place_order(client, BOB, ((2, 1),))["order_id"]
    advance(client, b, "processing")
    db.execute(text("UPDATE orders SET order_time = '2026-01-15 10:00' WHERE order_id = :o"), {"o": a})
    db.commit()

    def ids(**params):
        r = client.get("/api/orders/", params=params, headers=H(STAFF))
        assert r.status_code == 200, r.text
        return [o["order_id"] for o in r.json()]

    assert set(ids()) == {a, b}
    assert ids(status="processing") == [b]
    assert ids(q="bob") == [b] and ids(q="愛麗") == [a] and ids(q=str(a)) == [a]
    assert ids(date_from="2026-01-15", date_to="2026-01-15") == [a]
    assert ids(date_to="2026-01-14") == []
    s = client.get("/api/orders/", params={"q": "bob"}, headers=H(STAFF)).json()[0]
    assert s["customer"]["name"] == "張寶博" and s["has_return"] is False and s["return_status"] is None


def test_status_blocked_while_return_pending(client):
    o = place_order(client)
    oid = o["order_id"]
    advance(client, oid, "processing")
    r = client.post("/api/returns/", json={"order_id": oid, "reason": "破損",
                                           "items": [{"item_no": 1, "return_qty": 1}]}, headers=H(ALICE))
    assert r.status_code == 201
    o = client.get(f"/api/orders/{oid}", headers=H(STAFF)).json()
    assert o["next_status"] is None and o["can_return"] is False
    assert o["return_request"]["status"] == "pending" and o["has_return"] and o["return_status"] == "pending"
    r = client.post(f"/api/orders/{oid}/status", json={"status": "shipping"}, headers=H(STAFF))
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-25")
