"""測試 RSS 報表統計 API（BR-23、RSS-F-001～005）。"""
from datetime import datetime
from decimal import Decimal

import pytest
from app.models import CartItem, Product, User
from app.services import orders as order_svc
from app.services.pricing import round_half_up


def _cart(db, user_id: int, items: list[tuple[int, int]]):
    for pid, qty in items:
        db.add(CartItem(user_id=user_id, product_id=pid, quantity=qty))
    db.commit()


def test_customer_forbidden_on_rss_endpoints(client, alice_h):
    """顧客角色存取 RSS 報表端點應回 403；未登入應回 401。"""
    assert client.get("/api/reports/sales").status_code == 401
    assert client.get("/api/reports/top-products").status_code == 401
    assert client.get("/api/reports/summary").status_code == 401

    assert client.get("/api/reports/sales", headers=alice_h).status_code == 403
    assert client.get("/api/reports/top-products", headers=alice_h).status_code == 403
    assert client.get("/api/reports/summary", headers=alice_h).status_code == 403


def test_cancelled_orders_excluded_from_sales(client, staff_h, db):
    """已取消（cancelled）的訂單不計入銷售報表（BR-23、RSS-F-001）。"""
    alice = db.get(User, 4)
    _cart(db, 4, [(1, 2)])  # Store 1, Product 1
    order = order_svc.checkout(db, alice, "陳愛麗", "0912", "台北", order_time=datetime(2026, 11, 22, 10))
    db.commit()

    order_svc.cancel_order(db, order, alice)
    db.commit()

    r = client.get(
        "/api/reports/sales?period=day&date_from=2026-11-22&date_to=2026-11-22",
        headers=staff_h,
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 0

    # summary 亦不計入銷售額，但 orders_by_status 應反映 cancelled
    r_sum = client.get(
        "/api/reports/summary?date_from=2026-11-22&date_to=2026-11-22",
        headers=staff_h,
    )
    assert r_sum.status_code == 200
    sdata = r_sum.json()
    assert sdata["sales_total"] == 0
    assert sdata["orders_by_status"]["cancelled"] == 1
    assert sdata["order_count"] == 1


def test_fully_returned_orders_excluded_from_sales(client, staff_h, db):
    """整筆退貨（returned）的訂單亦不計入銷售報表（BR-23）。"""
    alice, staff = db.get(User, 4), db.get(User, 2)
    _cart(db, 4, [(1, 2)])
    order = order_svc.checkout(db, alice, "陳愛麗", "0912", "台北", order_time=datetime(2026, 11, 22, 10))
    db.commit()

    order_svc.advance_status(db, order, staff, "processing")
    db.commit()

    rr = order_svc.create_return(db, order, "全部退貨", [(1, 2)])
    db.commit()

    order_svc.approve_return(db, rr, staff)
    db.commit()
    assert order.status == "returned"

    r = client.get(
        "/api/reports/sales?period=day&date_from=2026-11-22&date_to=2026-11-22",
        headers=staff_h,
    )
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_multistore_order_split_and_rounding(client, staff_h, db):
    """跨店訂單依商品淨額比例分攤給各店，各店銷售總額加總等於訂單總額（±1 四捨五入誤差，BR-23）。

    Store 1: Product 1 (彩虹啾啾球, 180 元, 1 件)
    Store 2: Product 3 (柔順梳毛刷, 320 元, 1 件)
    """
    alice = db.get(User, 4)
    _cart(db, 4, [(1, 1), (3, 1)])
    order = order_svc.checkout(db, alice, "陳愛麗", "0912", "台北", order_time=datetime(2026, 11, 22, 11))
    db.commit()

    it1 = [it for it in order.items if it.product_id == 1][0]
    it2 = [it for it in order.items if it.product_id == 3][0]
    net1 = it1.unit_price * it1.quantity - it1.event_discount
    net2 = it2.unit_price * it2.quantity - it2.event_discount
    order_net = net1 + net2

    share1 = int(round_half_up(Decimal(order.total) * net1 / order_net))
    share2 = int(round_half_up(Decimal(order.total) * net2 / order_net))
    assert abs(share1 + share2 - int(order.total)) <= 1

    r = client.get(
        "/api/reports/sales?period=day&date_from=2026-11-22&date_to=2026-11-22",
        headers=staff_h,
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2

    row_s1 = [row for row in rows if row["store_id"] == 1][0]
    row_s2 = [row for row in rows if row["store_id"] == 2][0]

    assert row_s1["store_name"] == "FUWA FUWA 台北信義店"
    assert row_s1["order_count"] == 1
    assert row_s1["sales_total"] == share1

    assert row_s2["store_name"] == "FUWA FUWA 台中公益店"
    assert row_s2["order_count"] == 1
    assert row_s2["sales_total"] == share2

    assert abs(row_s1["sales_total"] + row_s2["sales_total"] - int(order.total)) <= 1

    # 驗證指定 store_id 篩選
    r_filtered = client.get(
        "/api/reports/sales?period=day&date_from=2026-11-22&date_to=2026-11-22&store_id=1",
        headers=staff_h,
    )
    assert r_filtered.status_code == 200
    f_rows = r_filtered.json()
    assert len(f_rows) == 1
    assert f_rows[0]["store_id"] == 1
    assert f_rows[0]["sales_total"] == share1


def test_partial_return_subtracts_from_correct_store(client, staff_h, db):
    """部分商品退貨時，退款金額僅從該商品所屬商店的銷售總額扣除（BR-23）。"""
    alice, staff = db.get(User, 4), db.get(User, 2)
    # Store 1: Product 1 (180 元, 1 件)
    # Store 2: Product 3 (320 元, 1 件)
    _cart(db, 4, [(1, 1), (3, 1)])
    order = order_svc.checkout(db, alice, "陳愛麗", "0912", "台北", order_time=datetime(2026, 11, 22, 12))
    db.commit()

    it1 = [it for it in order.items if it.product_id == 1][0]
    it2 = [it for it in order.items if it.product_id == 3][0]
    net1 = it1.unit_price * it1.quantity - it1.event_discount
    net2 = it2.unit_price * it2.quantity - it2.event_discount
    order_net = net1 + net2
    init_share1 = int(round_half_up(Decimal(order.total) * net1 / order_net))
    init_share2 = int(round_half_up(Decimal(order.total) * net2 / order_net))

    # 推進至 processing 並申請退貨 Store 1 的商品 1
    order_svc.advance_status(db, order, staff, "processing")
    db.commit()

    rr = order_svc.create_return(db, order, "不要了", [(it1.item_no, 1)])
    db.commit()

    order_svc.approve_return(db, rr, staff)
    db.commit()

    refund_amount = int(rr.items[0].refund_amount)
    assert refund_amount > 0

    r = client.get(
        "/api/reports/sales?period=day&date_from=2026-11-22&date_to=2026-11-22",
        headers=staff_h,
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2

    row_s1 = [row for row in rows if row["store_id"] == 1][0]
    row_s2 = [row for row in rows if row["store_id"] == 2][0]

    # Store 1 扣除退款
    assert row_s1["sales_total"] == init_share1 - refund_amount
    # Store 2 不受影響
    assert row_s2["sales_total"] == init_share2


def test_day_week_month_grouping_with_monday_boundary(client, staff_h, db):
    """驗證日、週、月的分組邏輯，週報表以週一至週日為一週（RSS-F-002）。

    2026-11-02 為週一（W45 開始日）
    2026-11-08 為週日（W45 結束日）
    2026-11-09 為週一（W46 開始日）
    """
    alice = db.get(User, 4)

    # 訂單 1: 2026-11-02（週一）
    _cart(db, 4, [(1, 1)])
    o1 = order_svc.checkout(db, alice, "A", "09", "T", order_time=datetime(2026, 11, 2, 10))
    db.commit()

    # 訂單 2: 2026-11-08（週日，與訂單 1 同一週 W45）
    _cart(db, 4, [(1, 1)])
    o2 = order_svc.checkout(db, alice, "A", "09", "T", order_time=datetime(2026, 11, 8, 15))
    db.commit()

    # 訂單 3: 2026-11-09（下週週一，進入 W46）
    _cart(db, 4, [(1, 1)])
    o3 = order_svc.checkout(db, alice, "A", "09", "T", order_time=datetime(2026, 11, 9, 9))
    db.commit()

    # 1. 依日 (day)
    r_day = client.get(
        "/api/reports/sales?period=day&date_from=2026-11-01&date_to=2026-11-15",
        headers=staff_h,
    )
    assert r_day.status_code == 200
    rows_day = r_day.json()
    day_starts = [r["period_start"] for r in rows_day]
    assert day_starts == ["2026-11-02", "2026-11-08", "2026-11-09"]
    for r in rows_day:
        assert r["period_label"] == r["period_start"]
        assert r["order_count"] == 1

    # 2. 依週 (week)
    r_week = client.get(
        "/api/reports/sales?period=week&date_from=2026-11-01&date_to=2026-11-15",
        headers=staff_h,
    )
    assert r_week.status_code == 200
    rows_week = r_week.json()
    assert len(rows_week) == 2

    # W45 (11/02–11/08)
    w45 = rows_week[0]
    assert w45["period_start"] == "2026-11-02"
    assert w45["period_label"] == "2026-W45 (11/02–11/08)"
    assert w45["order_count"] == 2
    assert w45["sales_total"] == int(o1.total + o2.total)

    # W46 (11/09–11/15)
    w46 = rows_week[1]
    assert w46["period_start"] == "2026-11-09"
    assert w46["period_label"] == "2026-W46 (11/09–11/15)"
    assert w46["order_count"] == 1
    assert w46["sales_total"] == int(o3.total)

    # 3. 依月 (month)
    r_month = client.get(
        "/api/reports/sales?period=month&date_from=2026-11-01&date_to=2026-11-30",
        headers=staff_h,
    )
    assert r_month.status_code == 200
    rows_month = r_month.json()
    assert len(rows_month) == 1
    m = rows_month[0]
    assert m["period_start"] == "2026-11-01"
    assert m["period_label"] == "2026-11"
    assert m["order_count"] == 3
    assert m["sales_total"] == int(o1.total + o2.total + o3.total)


def test_top_products_and_summary(client, staff_h, db):
    """測試 /top-products 暢銷排行（含 limit、store_id 篩選）與 /summary 總覽（含待審核退貨）。"""
    alice, bob = db.get(User, 4), db.get(User, 5)

    # Alice 買 3 件商品 1 (Store 1)
    _cart(db, 4, [(1, 3)])
    order1 = order_svc.checkout(db, alice, "A", "09", "T", order_time=datetime(2026, 11, 22, 10))
    db.commit()

    # Bob 買 1 件商品 3 (Store 2) 與 1 件商品 1 (Store 1)
    _cart(db, 5, [(3, 1), (1, 1)])
    order2 = order_svc.checkout(db, bob, "B", "09", "T", order_time=datetime(2026, 11, 22, 11))
    db.commit()

    # 推進 order1 狀態並建立 pending 退貨申請
    staff = db.get(User, 2)
    order_svc.advance_status(db, order1, staff, "processing")
    db.commit()
    order_svc.create_return(db, order1, "測試退貨申請", [(1, 1)])
    db.commit()

    # 查 top-products
    r_top = client.get(
        "/api/reports/top-products?date_from=2026-11-01&date_to=2026-11-30",
        headers=staff_h,
    )
    assert r_top.status_code == 200
    top = r_top.json()
    assert len(top) >= 2
    # 商品 1 總銷量 4 件，應排第一
    assert top[0]["product_id"] == 1
    assert top[0]["quantity"] == 4
    # 商品 3 銷量 1 件
    assert top[1]["product_id"] == 3
    assert top[1]["quantity"] == 1

    # 查 top-products 指定 limit=1
    r_top_limit = client.get(
        "/api/reports/top-products?date_from=2026-11-01&date_to=2026-11-30&limit=1",
        headers=staff_h,
    )
    assert r_top_limit.status_code == 200
    assert len(r_top_limit.json()) == 1

    # 查 top-products 指定 store_id=2
    r_top_s2 = client.get(
        "/api/reports/top-products?date_from=2026-11-01&date_to=2026-11-30&store_id=2",
        headers=staff_h,
    )
    assert r_top_s2.status_code == 200
    top_s2 = r_top_s2.json()
    assert len(top_s2) == 1
    assert top_s2[0]["product_id"] == 3

    # 查 summary
    r_sum = client.get(
        "/api/reports/summary?date_from=2026-11-01&date_to=2026-11-30",
        headers=staff_h,
    )
    assert r_sum.status_code == 200
    summary = r_sum.json()
    assert summary["order_count"] == 2
    assert summary["customer_count"] == 2
    assert summary["orders_by_status"]["processing"] == 1
    assert summary["orders_by_status"]["received"] == 1
    assert summary["pending_returns"] == 1
    assert summary["sales_total"] > 0
