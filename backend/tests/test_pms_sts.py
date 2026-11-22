"""PMS 商品與 STS 商店（PMS-F-001～PMS-F-008、STS-F-001～STS-F-004、BR-04、BR-06、BR-20、BR-24）。"""
from datetime import date

from app.models import CartItem, User
from app.services import orders as svc

NEW = {"store_id": 2, "name": "測試磨牙骨", "description": "耐咬牛皮骨", "category": "toy",
       "image_url": "/images/bone.png", "price": 199, "stock": 30, "is_listed": True}


def make_order(db, user_id: int, items: list[tuple[int, int]], to_status: str | None = None) -> int:
    for pid, qty in items:
        db.add(CartItem(user_id=user_id, product_id=pid, quantity=qty))
    db.commit()
    order = svc.checkout(db, db.get(User, user_id), "收件人", "0912", "台北")
    db.commit()
    staff = db.get(User, 2)
    path = ["processing", "shipping", "closed"]
    if to_status:
        for st in path[:path.index(to_status) + 1]:
            svc.advance_status(db, order, staff, st)
            db.commit()
    return order.order_id


# ---------- 商品瀏覽 ----------
def test_public_list_hides_unlisted(client, staff_h, alice_h):
    items = client.get("/api/products/").json()
    assert len(items) == 14 and all(p["is_listed"] for p in items)
    assert 15 not in {p["product_id"] for p in items}
    # 顧客帶 include_unlisted 也看不到
    assert len(client.get("/api/products/", params={"include_unlisted": True}, headers=alice_h).json()) == 14
    all_items = client.get("/api/products/", params={"include_unlisted": True}, headers=staff_h).json()
    assert len(all_items) == 15 and 15 in {p["product_id"] for p in all_items}


def test_product_shape_and_money_ints(client):
    p = next(x for x in client.get("/api/products/").json() if x["product_id"] == 1)
    assert set(p) >= {"product_id", "store_id", "store_name", "name", "description", "category", "image_url",
                      "price", "stock", "is_listed", "created_at", "updated_at", "event_discount"}
    assert p["price"] == 180 and isinstance(p["price"], int)
    assert p["store_name"] == "FUWA FUWA 台北信義店"


def test_search_filter_sort(client):
    names = [p["name"] for p in client.get("/api/products/", params={"q": "貓"}).json()]
    assert set(names) == {"貓抓板跳台", "羽毛逗貓棒"}
    # 比對描述
    r = client.get("/api/products/", params={"q": "燕麥"}).json()
    assert [p["name"] for p in r] == ["溫和洗毛精"]
    assert client.get("/api/products/", params={"q": "不存在的東西"}).json() == []
    # % 被跳脫成一般字元：只有描述含「100%」的凍乾符合
    assert [p["product_id"] for p in client.get("/api/products/", params={"q": "%"}).json()] == [8]
    r = client.get("/api/products/", params={"category": "food"}).json()
    assert {p["product_id"] for p in r} == {5, 8}
    r = client.get("/api/products/", params={"store_id": 3}).json()
    assert {p["product_id"] for p in r} == {6, 7, 10, 12}
    prices = [p["price"] for p in client.get("/api/products/", params={"sort": "price_asc"}).json()]
    assert prices == sorted(prices) and prices[0] == 65
    prices = [p["price"] for p in client.get("/api/products/", params={"sort": "price_desc"}).json()]
    assert prices == sorted(prices, reverse=True) and prices[0] == 2800
    assert client.get("/api/products/", params={"sort": "bogus"}).status_code == 422


def test_categories(client):
    assert client.get("/api/products/categories").json() == ["accessory", "care", "food", "home", "toy"]


def test_detail_with_event_discount(client):
    p = client.get("/api/products/9").json()
    ev = p["event_discount"]
    if ev is not None:   # 種子 EVT-0001（貓跳台 8 折）只在活動期間內有效
        assert ev["discount_code"] and set(ev) == {"discount_code", "description", "rate", "buy_qty",
                                                     "free_qty", "start_date", "end_date"}
    assert p["also_bought"] == []
    assert client.get("/api/products/999").status_code == 404


def test_event_discount_matches_pricing_service(client, db):
    from app.services.pricing import event_discount_for
    for pid in (5, 9, 1):
        d = event_discount_for(db, pid, date.today())
        ev = client.get(f"/api/products/{pid}").json()["event_discount"]
        assert (ev and ev["discount_code"]) == (d and d.discount_code)


def test_unlisted_detail_only_for_staff(client, staff_h, alice_h):
    assert client.get("/api/products/15").status_code == 404
    assert client.get("/api/products/15", headers=alice_h).status_code == 404
    r = client.get("/api/products/15", headers=staff_h)
    assert r.status_code == 200 and r.json()["is_listed"] is False


def test_also_bought(client, db):
    make_order(db, 4, [(1, 1), (2, 1), (5, 1)])
    make_order(db, 5, [(1, 1), (5, 2)])
    make_order(db, 5, [(3, 1)])
    r = client.get("/api/products/1").json()
    assert [p["product_id"] for p in r["also_bought"]] == [5, 2]


# ---------- 商品維護 ----------
def test_staff_create_update_product(client, staff_h):
    r = client.post("/api/products/", headers=staff_h, json=NEW)
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["price"] == 199 and p["store_name"] == "FUWA FUWA 台中公益店"
    r = client.put(f"/api/products/{p['product_id']}", headers=staff_h, json={**NEW, "price": 250, "stock": 0})
    assert r.status_code == 200 and r.json()["price"] == 250 and r.json()["stock"] == 0
    assert r.json()["updated_at"] >= p["updated_at"]
    assert client.get("/api/products/", params={"q": "磨牙骨"}).json()[0]["price"] == 250


def test_product_write_requires_staff(client, alice_h):
    assert client.post("/api/products/", json=NEW).status_code == 401
    assert client.post("/api/products/", headers=alice_h, json=NEW).status_code == 403
    assert client.put("/api/products/1", headers=alice_h, json=NEW).status_code == 403
    assert client.delete("/api/products/1", headers=alice_h).status_code == 403


def test_invalid_price_and_stock_rejected(client, staff_h):
    for bad in ({"price": 0}, {"price": -10}, {"stock": -1}):
        r = client.post("/api/products/", headers=staff_h, json={**NEW, **bad})
        assert r.status_code in (409, 422), r.text
    assert client.put("/api/products/1", headers=staff_h, json={**NEW, "price": 0}).status_code in (409, 422)
    assert client.post("/api/products/", headers=staff_h, json={**NEW, "store_id": 99}).status_code == 404


def test_db_rejects_bad_price_even_bypassing_api(db):
    import pytest
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    with pytest.raises(DBAPIError, match="product_price_check"):
        db.execute(text("UPDATE product SET price = 0 WHERE product_id = 1"))
    db.rollback()


def test_delete_unreferenced_product_hard_deletes(client, staff_h):
    pid = client.post("/api/products/", headers=staff_h, json=NEW).json()["product_id"]
    r = client.delete(f"/api/products/{pid}", headers=staff_h)
    assert r.status_code == 200 and r.json()["deleted"] is True and r.json()["unlisted"] is False
    assert client.get(f"/api/products/{pid}", headers=staff_h).status_code == 404


def test_delete_referenced_product_is_unlisted(client, staff_h, db):
    make_order(db, 4, [(13, 1)])
    r = client.delete("/api/products/13", headers=staff_h)
    assert r.status_code == 200
    assert r.json()["deleted"] is False and r.json()["unlisted"] is True
    p = client.get("/api/products/13", headers=staff_h).json()
    assert p["is_listed"] is False
    assert 13 not in {x["product_id"] for x in client.get("/api/products/").json()}


# ---------- 商店 ----------
def test_store_list_and_detail(client):
    stores = client.get("/api/stores/").json()
    assert [s["store_id"] for s in stores] == [1, 2, 3]
    s3 = stores[2]
    assert s3["product_count"] == 4 and s3["avg_rating"] is None and s3["review_count"] == 0  # 15 號下架不算
    d = client.get("/api/stores/3").json()
    assert {p["product_id"] for p in d["products"]} == {6, 7, 10, 12}
    assert d["reviews"] == []
    assert client.get("/api/stores/9").status_code == 404


def test_store_update_admin_only(client, admin_h, staff_h):
    body = {"name": "FUWA 新店名", "address": "台北市", "email": "new@fuwafuwa.tw", "phone": "02-1234"}
    assert client.put("/api/stores/1", headers=staff_h, json=body).status_code == 403
    r = client.put("/api/stores/1", headers=admin_h, json=body)
    assert r.status_code == 200 and r.json()["name"] == "FUWA 新店名"
    assert client.get("/api/products/1").json()["store_name"] == "FUWA 新店名"


def test_review_rules_br24(client, alice_h, bob_h, db):
    open_order = make_order(db, 4, [(1, 1)])                      # received
    r = client.post("/api/stores/1/reviews", headers=alice_h, json={"order_id": open_order, "rating": 5})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-24")

    closed = make_order(db, 4, [(1, 1), (3, 1)], to_status="closed")   # 店 1 與店 2
    # 別人的訂單
    assert client.post("/api/stores/1/reviews", headers=bob_h,
                       json={"order_id": closed, "rating": 5}).status_code == 404
    # 沒有在店 3 購買
    r = client.post("/api/stores/3/reviews", headers=alice_h, json={"order_id": closed, "rating": 5})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-24")
    # 評分範圍
    assert client.post("/api/stores/1/reviews", headers=alice_h,
                       json={"order_id": closed, "rating": 6}).status_code == 422

    r = client.post("/api/stores/1/reviews", headers=alice_h,
                    json={"order_id": closed, "rating": 4, "comment": "出貨很快"})
    assert r.status_code == 201, r.text
    assert r.json()["customer_name"] == "陳愛麗" and r.json()["rating"] == 4
    r = client.post("/api/stores/1/reviews", headers=alice_h, json={"order_id": closed, "rating": 5})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-24")
    assert client.post("/api/stores/2/reviews", headers=alice_h,
                       json={"order_id": closed, "rating": 5}).status_code == 201

    s1 = client.get("/api/stores/1").json()
    assert s1["review_count"] == 1 and s1["avg_rating"] == 4.0
    assert s1["reviews"][0]["comment"] == "出貨很快"


def test_review_requires_customer(client, staff_h):
    assert client.post("/api/stores/1/reviews", json={"order_id": 1, "rating": 5}).status_code == 401
    assert client.post("/api/stores/1/reviews", headers=staff_h, json={"order_id": 1, "rating": 5}).status_code == 403


def test_db_trigger_rejects_review_of_open_order(db):
    import pytest
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    oid = make_order(db, 4, [(1, 1)], to_status="shipping")
    with pytest.raises(DBAPIError, match="BR-24"):
        db.execute(text("INSERT INTO store_review (order_id, store_id, rating) VALUES (:o, 1, 5)"), {"o": oid})
    db.rollback()
