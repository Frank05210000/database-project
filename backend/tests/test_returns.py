"""OMS 退貨 API（BR-25、BR-26、OMS-F-011、OMS-F-012）。

訂單：柔順梳毛刷 ×2（EVT-9001 8 折）＋ 彩虹啾啾球 ×1，全館 9 折，未達免運。
  小計 820、特殊活動折扣 128、季節性折扣 69、稅 31、運費 100 → 總額 754
  BR-26 分攤基數 = 754 − 實付運費 100 = 654；全部商品扣除特殊活動折扣後 = 512 + 180 = 692
"""
from sqlalchemy import text

from tests.test_scs_oms import ALICE, BOB, STAFF, H, advance, place_order, stable_discounts, stock


def setup_order(client, db, *statuses) -> tuple[int, dict[int, int]]:
    stable_discounts(db)
    o = place_order(client)
    assert o["total"] == 754
    advance(client, o["order_id"], *statuses)
    return o["order_id"], {i["product_id"]: i["item_no"] for i in o["items"]}


def request_return(client, oid, items, uid=ALICE, reason="尺寸不合"):
    return client.post("/api/returns/", json={"order_id": oid, "reason": reason,
                                              "items": [{"item_no": n, "return_qty": q} for n, q in items]},
                       headers=H(uid))


def test_return_on_received_order_rejected(client, db):
    oid, no = setup_order(client, db)
    r = request_return(client, oid, [(no[1], 1)])
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-25")


def test_return_validation(client, db):
    oid, no = setup_order(client, db, "processing")
    r = request_return(client, oid, [(no[3], 3)])            # 買 2 退 3
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-25")
    assert request_return(client, oid, [(no[3], 0)]).status_code == 409
    assert request_return(client, oid, [(99, 1)]).status_code == 409
    assert request_return(client, oid, []).status_code == 409
    assert request_return(client, oid, [(no[3], 1)], reason="  ").status_code == 422
    assert request_return(client, oid, [(no[3], 1)], uid=BOB).status_code == 403   # 別人的訂單
    assert request_return(client, oid, [(no[3], 1)], uid=STAFF).status_code == 403  # 需 customer
    assert request_return(client, 99999, [(1, 1)]).status_code == 404


def test_second_return_request_rejected(client, db):
    oid, no = setup_order(client, db, "processing")
    assert request_return(client, oid, [(no[3], 1)]).status_code == 201
    r = request_return(client, oid, [(no[1], 1)])
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-25")


def test_reject_requires_reason_then_reject(client, db):
    oid, no = setup_order(client, db, "processing", "shipping")
    rid = request_return(client, oid, [(no[3], 1)]).json()["return_id"]
    r = client.post(f"/api/returns/{rid}/reject", json={"reject_reason": "  "}, headers=H(STAFF))
    assert r.status_code in (409, 422)
    assert client.post(f"/api/returns/{rid}/reject", json={}, headers=H(STAFF)).status_code in (409, 422)
    assert client.post(f"/api/returns/{rid}/reject", json={"reject_reason": "x"}, headers=H(ALICE)).status_code == 403
    r = client.post(f"/api/returns/{rid}/reject", json={"reject_reason": "商品已使用"}, headers=H(STAFF))
    assert r.status_code == 200
    rr = r.json()
    assert rr["status"] == "rejected" and rr["reject_reason"] == "商品已使用"
    assert rr["processed_by_name"] == "王小明" and rr["processed_at"] and rr["refund_total"] is None
    assert rr["order_status"] == "shipping"
    # 已處理不可再核准；訂單可以繼續推進，但不能再申請
    assert client.post(f"/api/returns/{rid}/approve", headers=H(STAFF)).status_code == 409
    o = advance(client, oid, "closed")
    assert o["return_request"]["status"] == "rejected" and o["can_return"] is False


def test_approve_partial_keeps_status(client, db):
    oid, no = setup_order(client, db, "processing", "shipping")
    s3 = stock(db, 3)
    r = request_return(client, oid, [(no[3], 1)])
    assert r.status_code == 201
    rr = r.json()
    assert rr["status"] == "pending" and rr["order_total"] == 754 and rr["customer"]["loginid"] == "alice"
    assert rr["items"] == [{"item_no": no[3], "product_name": "柔順梳毛刷", "unit_price": 320, "quantity": 2,
                            "return_qty": 1, "refund_amount": None}]
    rid = rr["return_id"]
    assert client.post(f"/api/returns/{rid}/approve", headers=H(ALICE)).status_code == 403
    r = client.post(f"/api/returns/{rid}/approve", headers=H(STAFF))
    assert r.status_code == 200, r.text
    rr = r.json()
    # 654 × (512 × 1/2) ÷ 692 = 241.9 → 242；運費不退
    assert rr["status"] == "approved" and rr["refund_total"] == 242 and rr["items"][0]["refund_amount"] == 242
    assert rr["order_status"] == "shipping"
    db.expire_all()
    assert stock(db, 3) == s3 + 1
    o = client.get(f"/api/orders/{oid}", headers=H(ALICE)).json()
    assert o["status"] == "shipping" and o["next_status"] == "closed" and o["return_status"] == "approved"
    assert o["return_request"]["refund_total"] == 242


def test_approve_full_return_closed(client, db):
    oid, no = setup_order(client, db, "processing", "shipping", "closed")
    s3, s1 = stock(db, 3), stock(db, 1)
    rid = request_return(client, oid, [(no[3], 2), (no[1], 1)]).json()["return_id"]
    rr = client.post(f"/api/returns/{rid}/approve", headers=H(STAFF)).json()
    refunds = {i["item_no"]: i["refund_amount"] for i in rr["items"]}
    # 654×512/692 = 483.9 → 484；654×180/692 = 170.1 → 170；closed 時運費不退
    assert refunds == {no[3]: 484, no[1]: 170} and rr["refund_total"] == 654
    assert rr["order_status"] == "returned"
    db.expire_all()
    assert stock(db, 3) == s3 + 2 and stock(db, 1) == s1 + 1
    o = client.get(f"/api/orders/{oid}", headers=H(STAFF)).json()
    assert o["status"] == "returned" and o["next_status"] is None
    assert [h["status"] for h in o["history"]][-1] == "returned"


def test_approve_full_return_processing_refunds_shipping(client, db):
    oid, no = setup_order(client, db, "processing")
    rid = request_return(client, oid, [(no[3], 2), (no[1], 1)]).json()["return_id"]
    rr = client.post(f"/api/returns/{rid}/approve", headers=H(STAFF)).json()
    assert rr["refund_total"] == 654 + 100 and rr["order_status"] == "returned"   # processing 全退：運費一併退還


def test_return_listing_and_access(client, db):
    oid, no = setup_order(client, db, "processing")
    rid = request_return(client, oid, [(no[1], 1)]).json()["return_id"]
    b = place_order(client, BOB, ((2, 1),))["order_id"]
    advance(client, b, "processing")
    rid_b = request_return(client, b, [(1, 1)], uid=BOB).json()["return_id"]
    client.post(f"/api/returns/{rid_b}/reject", json={"reject_reason": "超過退貨期限"}, headers=H(STAFF))

    assert [r["return_id"] for r in client.get("/api/returns/mine", headers=H(ALICE)).json()] == [rid]
    assert [r["return_id"] for r in client.get("/api/returns/mine", headers=H(BOB)).json()] == [rid_b]
    all_ = client.get("/api/returns/", headers=H(STAFF)).json()
    assert [r["return_id"] for r in all_] == [rid, rid_b]            # 待審核排前面
    assert [r["return_id"] for r in client.get("/api/returns/", params={"status": "pending"},
                                                 headers=H(STAFF)).json()] == [rid]
    assert client.get("/api/returns/", params={"status": "bogus"}, headers=H(STAFF)).status_code == 422
    assert client.get("/api/returns/", headers=H(ALICE)).status_code == 403
    assert client.get(f"/api/returns/{rid}", headers=H(ALICE)).status_code == 200
    assert client.get(f"/api/returns/{rid}", headers=H(STAFF)).status_code == 200
    assert client.get(f"/api/returns/{rid}", headers=H(BOB)).status_code == 403
    assert client.get("/api/returns/9999", headers=H(STAFF)).status_code == 404


def test_db_trigger_blocks_second_request(db, client):
    """繞過 API 直接寫入，UNIQUE(order_id) 也會擋下第二筆（BR-25）。"""
    oid, no = setup_order(client, db, "processing")
    request_return(client, oid, [(no[1], 1)])
    import pytest
    from sqlalchemy.exc import DBAPIError
    with pytest.raises(DBAPIError):
        db.execute(text("INSERT INTO return_request (order_id, reason) VALUES (:o, 'again')"), {"o": oid})
    db.rollback()
