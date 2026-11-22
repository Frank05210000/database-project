"""工作人員隸屬商店：資料庫約束、管理員指派與跨店權限（BR-21）。"""
import psycopg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.deps import staff_store_id
from app.models import User
from tests.conftest import INIT_DIR, TEST_DSN, login

PRODUCT = {"store_id": 1, "name": "店員測試商品", "price": 100, "stock": 5}
EVENT = {"discount_type": "special_event", "description": "店員測試活動",
         "start_date": "2030-01-01", "end_date": "2030-01-31", "rate": 0.1,
         "product_ids": [1]}
PERIOD = {"date_from": "2026-01-01", "date_to": "2026-12-31"}


@pytest.fixture
def demo_data():
    """直接接在每次重建的 01～03 後載入，驗證硬編碼編號沒有衝突。"""
    with psycopg.connect(TEST_DSN) as conn:
        conn.execute((INIT_DIR / "04_demo_data.sql").read_text())


@pytest.mark.parametrize("sql", [
    "INSERT INTO store_staff (user_id, store_id) VALUES (4, 1)",
    "UPDATE store_staff SET user_id = 4 WHERE user_id = 7",
])
def test_trigger_rejects_non_staff(db, sql):
    with pytest.raises(DBAPIError, match="BR-21"):
        db.execute(text(sql))
        db.commit()
    db.rollback()


def test_removing_staff_role_deletes_store_row(db):
    db.execute(text("INSERT INTO user_role (user_id, role) VALUES (7, 'customer')"))
    db.execute(text("DELETE FROM user_role WHERE user_id = 7 AND role = 'staff'"))
    db.commit()
    assert db.execute(text("SELECT store_id FROM store_staff WHERE user_id = 7")).scalar() is None
    assert staff_store_id(db, db.get(User, 7)) is None


@pytest.mark.parametrize("loginid,store_id", [
    ("staff_xinyi", 1), ("staff_gongyi", 2), ("staff_zuoying", 3),
    ("staff", None), ("manager", None),
])
def test_seed_accounts_expose_store(client, admin_h, db, loginid, store_id):
    headers = login(client, loginid, "staff123")
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["store_id"] == store_id
    assert (me["store_name"] is None) == (store_id is None)
    assert staff_store_id(db, db.get(User, me["user_id"])) == store_id
    users = client.get("/api/admin/users", headers=admin_h).json()
    assert next(u for u in users if u["loginid"] == loginid)["store_name"] == me["store_name"]


def test_admin_sets_changes_and_clears_store(client, admin_h, staff_h):
    for sid in (1, 2, None):
        r = client.put("/api/admin/users/2/store", headers=admin_h, json={"store_id": sid})
        assert r.status_code == 200, r.text
        assert r.json()["store_id"] == sid
        # 同一張 token 立即反映指派與解除隸屬
        assert client.get("/api/auth/me", headers=staff_h).json()["store_id"] == sid
        expected = 201 if sid in (None, 1) else 403
        assert client.post("/api/products/", headers=staff_h, json=PRODUCT).status_code == expected
    me = client.get("/api/auth/me", headers=staff_h).json()
    assert me["store_name"] is None


def test_admin_store_assignment_validation(client, admin_h, xinyi_h, alice_h):
    r = client.put("/api/admin/users/4/store", headers=admin_h, json={"store_id": 1})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-21")
    assert client.put("/api/admin/users/4/store", headers=admin_h,
                      json={"store_id": None}).status_code == 409
    assert client.put("/api/admin/users/7/store", headers=admin_h,
                      json={"store_id": 999}).status_code == 404
    assert client.put("/api/admin/users/999/store", headers=admin_h,
                      json={"store_id": 1}).status_code == 404
    for headers in (xinyi_h, alice_h):
        assert client.put("/api/admin/users/7/store", headers=headers,
                          json={"store_id": None}).status_code == 403


def test_admin_creates_staff_with_store(client, admin_h):
    body = {"loginid": "new_staff", "name": "新店員", "email": "new_staff@fuwafuwa.tw",
            "password": "staff123", "roles": ["staff"], "store_id": 3}
    r = client.post("/api/admin/users", headers=admin_h, json=body)
    assert r.status_code == 201, r.text
    assert r.json()["store_id"] == 3 and "左營" in r.json()["store_name"]
    r = client.post("/api/admin/users", headers=admin_h,
                    json={**body, "loginid": "new_customer", "roles": ["customer"]})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-21")
    assert client.post("/api/admin/users", headers=admin_h,
                       json={**body, "loginid": "unknown_store", "store_id": 999}).status_code == 404


def test_role_removal_cleans_store_via_api(client, admin_h, xinyi_h, db):
    r = client.put("/api/admin/users/7/roles", headers=admin_h, json={"roles": ["customer"]})
    assert r.status_code == 200, r.text
    assert r.json()["store_id"] is None and r.json()["store_name"] is None
    assert db.execute(text("SELECT 1 FROM store_staff WHERE user_id = 7")).scalar() is None
    assert client.post("/api/products/", headers=xinyi_h, json=PRODUCT).status_code == 403


def test_store_staff_product_scope(client, xinyi_h):
    r = client.post("/api/products/", headers=xinyi_h, json={**PRODUCT, "store_id": 2})
    assert r.status_code == 403 and r.json()["detail"] == "只能管理自己商店的商品"
    r = client.post("/api/products/", headers=xinyi_h, json=PRODUCT)
    assert r.status_code == 201, r.text
    pid = r.json()["product_id"]
    assert client.put(f"/api/products/{pid}", headers=xinyi_h,
                      json={**PRODUCT, "name": "本店更新"}).status_code == 200
    # 不能改別店商品，也不能把本店商品移到別店
    assert client.put("/api/products/3", headers=xinyi_h, json=PRODUCT).status_code == 403
    assert client.put(f"/api/products/{pid}", headers=xinyi_h,
                      json={**PRODUCT, "store_id": 2}).status_code == 403
    assert client.delete("/api/products/3", headers=xinyi_h).status_code == 403
    assert client.delete(f"/api/products/{pid}", headers=xinyi_h).status_code == 200


def test_order_list_detail_and_status_scope(client, xinyi_h, staff_h, demo_data):
    r = client.get("/api/orders/", headers=xinyi_h)
    assert r.status_code == 200, r.text
    assert {o["order_id"] for o in r.json()} == {1, 4, 7, 9, 11, 12, 13}
    assert len(client.get("/api/orders/", headers=staff_h).json()) == 13
    # 跨店訂單包含信義商品，店員可看完整訂單
    assert client.get("/api/orders/11", headers=xinyi_h).status_code == 200
    assert client.get("/api/orders/2", headers=xinyi_h).status_code == 404
    assert client.post("/api/orders/2/status", headers=xinyi_h,
                       json={"status": "processing"}).status_code == 404
    assert client.post("/api/orders/13/status", headers=xinyi_h,
                       json={"status": "processing"}).status_code == 200
    assert client.get("/api/orders/2", headers=staff_h).status_code == 200


def test_return_scope(client, xinyi_h, staff_h, demo_data):
    r = client.get("/api/returns/", headers=xinyi_h)
    assert r.status_code == 200, r.text
    assert [rr["return_id"] for rr in r.json()] == [2]
    assert client.get("/api/returns/2", headers=xinyi_h).status_code == 200
    assert client.get("/api/returns/4", headers=xinyi_h).status_code == 404
    assert client.post("/api/returns/4/approve", headers=xinyi_h).status_code == 404
    assert client.post("/api/returns/4/reject", headers=xinyi_h,
                       json={"reject_reason": "測試"}).status_code == 404
    assert client.get("/api/returns/4", headers=staff_h).status_code == 200
    gongyi_h = login(client, "staff_gongyi", "staff123")
    assert client.post("/api/returns/4/reject", headers=gongyi_h,
                       json={"reject_reason": "商品未符合退貨條件"}).status_code == 200


@pytest.mark.parametrize("loginid,sid", [("staff_xinyi", 1), ("staff_gongyi", 2), ("staff_zuoying", 3)])
def test_reports_force_own_store(client, staff_h, demo_data, loginid, sid):
    headers = login(client, loginid, "staff123")
    for path in ("sales", "top-products"):
        r = client.get(f"/api/reports/{path}", headers=headers,
                       params={**PERIOD, "store_id": sid % 3 + 1})
        expected = client.get(f"/api/reports/{path}", headers=staff_h,
                              params={**PERIOD, "store_id": sid}).json()
        assert r.status_code == 200, r.text
        assert r.json() == expected and r.json()
        assert {row["store_id"] for row in r.json()} == {sid}
    summary = client.get("/api/reports/summary", headers=headers, params=PERIOD).json()
    sales = client.get("/api/reports/sales", headers=headers, params=PERIOD).json()
    orders = client.get("/api/orders/", headers=headers).json()
    returns = client.get("/api/returns/", headers=headers).json()
    assert summary["order_count"] == len(orders)
    assert sum(summary["orders_by_status"].values()) == len(orders)
    assert summary["sales_total"] == sum(row["sales_total"] for row in sales)
    assert summary["pending_returns"] == sum(rr["status"] == "pending" for rr in returns)
    assert summary["customer_count"] == len({o["customer"]["user_id"] for o in orders})


@pytest.mark.parametrize("dtype,code", [("seasonal", "SEA-0001"), ("shipping", "SHP-0001")])
def test_global_discounts_only_hq(client, xinyi_h, staff_h, dtype, code):
    body = {**EVENT, "discount_type": dtype, "product_ids": None}
    if dtype == "shipping":
        body.update(rate=None, min_amount=1000)
    r = client.post("/api/discounts/", headers=xinyi_h, json=body)
    assert r.status_code == 403
    assert r.json()["detail"] == "運費與季節性折扣只能由總部工作人員管理"
    assert client.put(f"/api/discounts/{code}", headers=xinyi_h,
                      json={"is_active": False}).status_code == 403
    assert client.delete(f"/api/discounts/{code}", headers=xinyi_h).status_code == 403
    assert client.post("/api/discounts/", headers=staff_h, json=body).status_code == 201
    assert client.put(f"/api/discounts/{code}", headers=staff_h,
                      json={"is_active": False}).status_code == 200
    assert client.delete(f"/api/discounts/{code}", headers=staff_h).status_code == 200


def test_special_event_scope(client, xinyi_h, staff_h):
    assert client.get("/api/discounts/", headers=xinyi_h).status_code == 200
    assert client.post("/api/discounts/", headers=xinyi_h,
                       json={**EVENT, "product_ids": [1, 3]}).status_code == 403
    r = client.post("/api/discounts/", headers=xinyi_h, json=EVENT)
    assert r.status_code == 201, r.text
    code = r.json()["discount_code"]
    assert client.put(f"/api/discounts/{code}", headers=xinyi_h,
                      json={"product_ids": [1, 3]}).status_code == 403
    assert client.put(f"/api/discounts/{code}", headers=xinyi_h,
                      json={"description": "本店活動更新"}).status_code == 200
    assert client.put("/api/discounts/EVT-0004", headers=xinyi_h,
                      json={"product_ids": [1]}).status_code == 403
    assert client.delete("/api/discounts/EVT-0004", headers=xinyi_h).status_code == 403
    assert client.delete(f"/api/discounts/{code}", headers=xinyi_h).status_code == 200
    # 總部可以建立跨店活動
    assert client.post("/api/discounts/", headers=staff_h,
                       json={**EVENT, "product_ids": [1, 3]}).status_code == 201


@pytest.mark.parametrize("loginid", ["staff", "manager"])
def test_hq_product_scope_unchanged(client, loginid):
    headers = login(client, loginid, "staff123")
    r = client.post("/api/products/", headers=headers, json={**PRODUCT, "store_id": 2})
    assert r.status_code == 201, r.text
    pid = r.json()["product_id"]
    assert client.put(f"/api/products/{pid}", headers=headers,
                      json={**PRODUCT, "store_id": 3}).status_code == 200
    assert client.delete(f"/api/products/{pid}", headers=headers).status_code == 200


def test_demo_data_applies_without_id_collisions(db, demo_data):
    assert db.execute(text("SELECT count(*) FROM users")).scalar() == 9
    assert db.execute(text("SELECT count(*) FROM orders")).scalar() == 13
    assert db.execute(text("SELECT count(*) FROM return_request")).scalar() == 4
    assert db.execute(text("SELECT user_id, store_id FROM store_staff ORDER BY user_id")).all() == [
        (7, 1), (8, 2), (9, 3)]
