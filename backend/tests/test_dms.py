"""測試 DMS 折扣管理 API（BR-13～BR-18、BR-20、DMS-F-001～009）。"""
from datetime import date, datetime
import re

import pytest
from app.models import CartItem, Discount, Product, User
from app.services import orders as order_svc
from tests.conftest import login


def test_public_active_discounts(client):
    """GET /active 是公開端點，無須登入即可取得今日有效的折扣。"""
    r = client.get("/api/discounts/active")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    codes = {d["discount_code"] for d in data}
    # 2026-11-22 有效的折扣
    assert "SHP-0001" in codes
    assert "SEA-0001" in codes
    assert "SEA-0002" in codes
    assert "EVT-0001" in codes
    assert "EVT-0002" in codes
    # SEA-0003 與 EVT-0003 在 2026 年夏季已結束，不應出現
    assert "SEA-0003" not in codes
    assert "EVT-0003" not in codes
    for d in data:
        assert d["is_current"] is True
        assert d["is_active"] is True
        assert "products" in d
        assert "used_count" in d


def test_customer_forbidden_on_staff_endpoints(client, alice_h):
    """顧客呼叫 staff 端點應被拒絕（403）。未登入應為 401。"""
    # 未登入
    assert client.get("/api/discounts/").status_code == 401
    assert client.post("/api/discounts/", json={}).status_code == 401

    # 顧客登入但權限不足
    assert client.get("/api/discounts/", headers=alice_h).status_code == 403
    assert client.post("/api/discounts/", headers=alice_h, json={}).status_code == 403
    assert client.get("/api/discounts/SHP-0001", headers=alice_h).status_code == 403
    assert client.put("/api/discounts/SHP-0001", headers=alice_h, json={}).status_code == 403
    assert client.delete("/api/discounts/SHP-0001", headers=alice_h).status_code == 403


def test_create_each_discount_type_and_code_format(client, staff_h):
    """建立運費、季節性與特殊活動折扣，並驗證代碼格式（BR-18）。"""
    # 1. 運費折扣
    r_shp = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "shipping",
            "description": "滿 1500 免運",
            "start_date": "2026-12-01",
            "end_date": "2026-12-31",
            "min_amount": 1500,
        },
    )
    assert r_shp.status_code == 201, r_shp.text
    d_shp = r_shp.json()
    assert re.match(r"^SHP-\d{4}$", d_shp["discount_code"])
    assert d_shp["discount_type"] == "shipping"
    assert d_shp["min_amount"] == 1500
    assert d_shp["rate"] is None
    assert d_shp["products"] == []

    # 2. 季節性折扣
    r_sea = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "seasonal",
            "description": "聖誕跨年全館 88 折",
            "start_date": "2026-12-20",
            "end_date": "2027-01-05",
            "rate": 0.120,
        },
    )
    assert r_sea.status_code == 201, r_sea.text
    d_sea = r_sea.json()
    assert re.match(r"^SEA-\d{4}$", d_sea["discount_code"])
    assert d_sea["discount_type"] == "seasonal"
    assert d_sea["rate"] == 0.12
    assert d_sea["min_amount"] is None

    # 3. 特殊活動折扣（折扣率）
    r_evt1 = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "反光牽繩 85 折",
            "start_date": "2027-01-01",
            "end_date": "2027-01-31",
            "rate": 0.150,
            "product_ids": [11],
        },
    )
    assert r_evt1.status_code == 201, r_evt1.text
    d_evt1 = r_evt1.json()
    assert re.match(r"^EVT-\d{4}$", d_evt1["discount_code"])
    assert d_evt1["discount_type"] == "special_event"
    assert d_evt1["rate"] == 0.15
    assert len(d_evt1["products"]) == 1
    assert d_evt1["products"][0]["product_id"] == 11
    assert d_evt1["products"][0]["name"] == "反光牽繩"

    # 4. 特殊活動折扣（買 X 送 Y）
    r_evt2 = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "柔順梳毛刷買 1 送 1",
            "start_date": "2027-01-01",
            "end_date": "2027-01-31",
            "buy_qty": 1,
            "free_qty": 1,
            "product_ids": [3],
        },
    )
    assert r_evt2.status_code == 201, r_evt2.text
    d_evt2 = r_evt2.json()
    assert re.match(r"^EVT-\d{4}$", d_evt2["discount_code"])
    assert d_evt2["buy_qty"] == 1
    assert d_evt2["free_qty"] == 1
    assert len(d_evt2["products"]) == 1
    assert d_evt2["products"][0]["product_id"] == 3


def test_invalid_rate_rejected(client, staff_h):
    """折扣率須介於 0 與 1 之間，1.5 應被拒絕（409，BR-15）。"""
    r = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "seasonal",
            "description": "無效折扣率",
            "start_date": "2026-12-01",
            "end_date": "2026-12-31",
            "rate": 1.5,
        },
    )
    assert r.status_code == 409
    assert "BR-15" in r.json()["detail"]


def test_start_greater_than_end_rejected(client, staff_h):
    """開始日期大於結束日期應被拒絕（409，BR-14）。"""
    r = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "seasonal",
            "description": "倒退日期",
            "start_date": "2026-12-31",
            "end_date": "2026-12-01",
            "rate": 0.1,
        },
    )
    assert r.status_code == 409
    assert "BR-14" in r.json()["detail"]


def test_shipping_without_min_amount_rejected(client, staff_h):
    """運費折扣若無門檻金額或 <= 0 應被拒絕（409，BR-17）。"""
    r1 = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "shipping",
            "description": "無門檻運費折扣",
            "start_date": "2026-12-01",
            "end_date": "2026-12-31",
        },
    )
    assert r1.status_code == 409
    assert "BR-17" in r1.json()["detail"]

    r2 = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "shipping",
            "description": "負門檻運費折扣",
            "start_date": "2026-12-01",
            "end_date": "2026-12-31",
            "min_amount": -100,
        },
    )
    assert r2.status_code == 409
    assert "BR-17" in r2.json()["detail"]


def test_special_event_overlap_existing_code_and_product_name(client, staff_h):
    """特殊活動折扣與同商品既有折扣重疊時，回 409 且訊息包含衝突代碼與商品名稱（BR-13、DMS-F-008）。

    種子資料：EVT-0001 套用於商品 9（貓抓板跳台），期間 2026-11-01 至 2026-12-31。
    """
    r = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "跳台限時破盤",
            "start_date": "2026-11-15",
            "end_date": "2026-11-25",
            "rate": 0.25,
            "product_ids": [9],
        },
    )
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "BR-13" in detail
    assert "EVT-0001" in detail
    assert "貓抓板跳台" in detail


def test_non_overlapping_period_accepted(client, staff_h):
    """相同商品但期間完全不重疊的特殊活動折扣應被接受（201）。"""
    r = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "跳台新年特惠",
            "start_date": "2027-01-01",
            "end_date": "2027-01-31",
            "rate": 0.15,
            "product_ids": [9],
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["discount_code"].startswith("EVT-")
    assert any(p["product_id"] == 9 for p in r.json()["products"])


def test_boundary_day_overlap_rejected(client, staff_h):
    """首尾兩日相交（start_date 等於既有 end_date，或 end_date 等於既有 start_date）亦屬重疊，應被拒絕（409）。"""
    # 1. start 等於 EVT-0001 的 end_date (2026-12-31)
    r1 = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "跨年邊界重疊",
            "start_date": "2026-12-31",
            "end_date": "2027-01-10",
            "rate": 0.15,
            "product_ids": [9],
        },
    )
    assert r1.status_code == 409
    assert "EVT-0001" in r1.json()["detail"]

    # 2. end 等於 EVT-0001 的 start_date (2026-11-01)
    r2 = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "開頭邊界重疊",
            "start_date": "2026-10-15",
            "end_date": "2026-11-01",
            "rate": 0.15,
            "product_ids": [9],
        },
    )
    assert r2.status_code == 409
    assert "EVT-0001" in r2.json()["detail"]


def test_delete_used_discount_rejected(client, staff_h, db):
    """已被訂單引用的折扣不可刪除（409，BR-20）。"""
    alice = db.get(User, 4)
    # Alice 購買商品 5 (主食罐)，觸發 EVT-0002 (買 2 送 1)
    db.add(CartItem(user_id=4, product_id=5, quantity=3))
    db.commit()
    order = order_svc.checkout(db, alice, "陳愛麗", "0912", "台北", order_time=datetime(2026, 11, 22, 10))
    db.commit()
    assert any(od.discount_code == "EVT-0002" for od in order.discounts)

    # 嘗試刪除 EVT-0002
    r = client.delete("/api/discounts/EVT-0002", headers=staff_h)
    assert r.status_code == 409
    assert "BR-20" in r.json()["detail"]


def test_delete_unused_discount_ok(client, staff_h):
    """未被訂單引用的折扣可正常刪除。"""
    # 建立一個新的未使用折扣
    r_create = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "seasonal",
            "description": "即將被刪除的折扣",
            "start_date": "2027-02-01",
            "end_date": "2027-02-28",
            "rate": 0.05,
        },
    )
    code = r_create.json()["discount_code"]

    # 刪除成功
    r_del = client.delete(f"/api/discounts/{code}", headers=staff_h)
    assert r_del.status_code == 200

    # 再查詢應為 404
    r_get = client.get(f"/api/discounts/{code}", headers=staff_h)
    assert r_get.status_code == 404


def test_code_and_type_immutability(client, staff_h):
    """PUT 時若修改 discount_code 或 discount_type 應被拒絕（409，BR-18）。"""
    r_code = client.put(
        "/api/discounts/SHP-0001",
        headers=staff_h,
        json={"discount_code": "SHP-9999"},
    )
    assert r_code.status_code == 409
    assert "BR-18" in r_code.json()["detail"]

    r_type = client.put(
        "/api/discounts/SHP-0001",
        headers=staff_h,
        json={"discount_type": "seasonal"},
    )
    assert r_type.status_code == 409
    assert "BR-18" in r_type.json()["detail"]


def test_list_and_update_discounts(client, staff_h):
    """測試 GET / 篩選條件與 PUT /{code} 正常更新。"""
    # 篩選 type
    r_type = client.get("/api/discounts/?type=seasonal", headers=staff_h)
    assert r_type.status_code == 200
    for d in r_type.json():
        assert d["discount_type"] == "seasonal"

    # 篩選 active_on
    r_act = client.get("/api/discounts/?active_on=2026-11-22", headers=staff_h)
    assert r_act.status_code == 200
    codes = {d["discount_code"] for d in r_act.json()}
    assert "SEA-0001" in codes
    assert "SEA-0003" not in codes

    # 關鍵字 q
    r_q = client.get("/api/discounts/?q=暖心", headers=staff_h)
    assert r_q.status_code == 200
    assert any(d["discount_code"] == "SEA-0001" for d in r_q.json())

    # PUT 正常更新描述與金額
    r_put = client.put(
        "/api/discounts/SHP-0001",
        headers=staff_h,
        json={"description": "滿 1200 免運", "min_amount": 1200},
    )
    assert r_put.status_code == 200
    assert r_put.json()["description"] == "滿 1200 免運"
    assert r_put.json()["min_amount"] == 1200


def test_put_update_dates_and_product_ids_with_overlap_checks(client, staff_h, db):
    """PUT 更新特殊活動折扣的日期與商品，驗證 cascade 及重疊檢查。"""
    # 1. EVT-0001 (商品 9, 原日期 2026-11-01..2026-12-31)
    # 更新日期為 2026-11-10..2026-12-20，應成功並串聯更新
    r_upd = client.put(
        "/api/discounts/EVT-0001",
        headers=staff_h,
        json={"start_date": "2026-11-10", "end_date": "2026-12-20"},
    )
    assert r_upd.status_code == 200, r_upd.text
    d = r_upd.json()
    assert d["start_date"] == "2026-11-10"
    assert d["end_date"] == "2026-12-20"

    # 2. 建立另一個在 2027-01-01..2027-01-31 的特殊活動折扣 EVT-new (商品 9)
    r_new = client.post(
        "/api/discounts/",
        headers=staff_h,
        json={
            "discount_type": "special_event",
            "description": "一月特惠",
            "start_date": "2027-01-01",
            "end_date": "2027-01-31",
            "rate": 0.1,
            "product_ids": [9],
        },
    )
    assert r_new.status_code == 201
    new_code = r_new.json()["discount_code"]

    # 3. 嘗試把 EVT-0001 的日期改為與 EVT-new 重疊 (2027-01-15..2027-02-15) -> 應被拒絕且訊息包含 new_code
    r_conflict = client.put(
        "/api/discounts/EVT-0001",
        headers=staff_h,
        json={"start_date": "2027-01-15", "end_date": "2027-02-15"},
    )
    assert r_conflict.status_code == 409
    assert new_code in r_conflict.json()["detail"]

    # 4. 把 EVT-new 的商品改為 [1] (彩虹啾啾球)，排除自身商品 9，應成功
    r_change_prod = client.put(
        f"/api/discounts/{new_code}",
        headers=staff_h,
        json={"product_ids": [1]},
    )
    assert r_change_prod.status_code == 200
    assert [p["product_id"] for p in r_change_prod.json()["products"]] == [1]
