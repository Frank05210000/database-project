"""全系統端對端煙霧測試：對「已啟動」的整套系統（./start.sh）經由前端的 /api proxy 走完主要流程。

    cd backend && .venv/bin/python scripts/e2e_smoke.py [http://localhost:5173]

會建立一個新的顧客帳號與一筆訂單（不影響示範資料的其他紀錄）。每一步印出 PASS/FAIL，失敗時結束碼為 1。
"""
import sys
import uuid

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173").rstrip("/") + "/api"
c = httpx.Client(base_url=BASE, timeout=15)
failures = 0


def check(name: str, cond: bool, info="") -> None:
    global failures
    print(("PASS " if cond else "FAIL ") + name + (f"  ({info})" if info and not cond else ""))
    failures += 0 if cond else 1


def login(loginid: str, pw: str) -> dict:
    r = c.post("/auth/login", json={"loginid": loginid, "password": pw})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---- 顧客：註冊、登入、搜尋 ----
uid = "e2e" + uuid.uuid4().hex[:6]
r = c.post("/auth/register", json={"loginid": uid, "name": "E2E 測試", "password": "e2e123",
                                   "email": f"{uid}@example.com", "address": "台北市", "phone": "0900"})
check("US-02 註冊顧客", r.status_code == 201, r.text)
check("BR-01 重複 loginid 被拒絕", c.post("/auth/register", json={"loginid": uid, "name": "x", "password": "e2e123",
      "email": "x@example.com", "address": "x"}).status_code == 409)
cust = login(uid, "e2e123")
check("停用帳號不能登入（carol）", c.post("/auth/login", json={"loginid": "carol", "password": "customer123"}).status_code == 403)
r = c.get("/products/", params={"q": "貓"})
check("US-01 關鍵字搜尋", r.status_code == 200 and any("貓" in p["name"] for p in r.json()), r.text[:200])

# ---- 購物車與結帳 ----
r = c.post("/cart/items", headers=cust, json={"product_id": 9, "quantity": 1})
q = r.json()["quote"]
check("SCS 加入購物車並計算報價", r.status_code == 200 and q["total"] == q["subtotal"] - q["discount_total"] + q["tax"] + q["shipping_fee"], q)
check("BR-06 超過庫存被拒絕", c.post("/cart/items", headers=cust, json={"product_id": 14, "quantity": 999}).status_code == 409)
check("BR-05 數量 0 被拒絕", c.put("/cart/items/9", headers=cust, json={"quantity": 0}).status_code in (409, 422))
pre = c.get("/orders/checkout-preview", headers=cust).json()
check("US-05 結帳預覽含折扣/稅/運費", all(k in pre["quote"] for k in ("event_discount", "seasonal_discount", "tax", "shipping_fee")))
r = c.post("/orders/", headers=cust, json={"recipient_name": "E2E", "recipient_phone": "0900", "recipient_address": "台北"})
check("OMS 建立訂單", r.status_code == 201, r.text)
order = r.json()
oid = order["order_id"]
check("新訂單狀態為 received", order["status"] == "received")
check("BR-07 空購物車不能結帳", c.post("/orders/", headers=cust, json={"recipient_name": "E2E", "recipient_phone": "0900",
                                                                    "recipient_address": "台北"}).status_code == 409)

# ---- 工作人員：狀態、退貨、報表、折扣 ----
staff = login("staff", "staff123")
check("BR-21 顧客不能更新訂單狀態", c.post(f"/orders/{oid}/status", headers=cust, json={"status": "processing"}).status_code == 403)
check("BR-19 不可跳過狀態", c.post(f"/orders/{oid}/status", headers=staff, json={"status": "shipping"}).status_code == 409)
r = c.post(f"/orders/{oid}/status", headers=staff, json={"status": "processing"})
check("US-13 工作人員推進到 processing", r.status_code == 200 and r.json()["status"] == "processing")
check("BR-19 processing 不能取消", c.post(f"/orders/{oid}/cancel", headers=cust).status_code == 409)
r = c.post("/returns/", headers=cust, json={"order_id": oid, "reason": "E2E", "items": [{"item_no": 1, "return_qty": 1}]})
check("US-10 申請退貨", r.status_code == 201, r.text)
rid = r.json()["return_id"]
check("BR-25 待審核時不能更新狀態", c.post(f"/orders/{oid}/status", headers=staff, json={"status": "shipping"}).status_code == 409)
check("BR-25 不能重複申請退貨", c.post("/returns/", headers=cust, json={"order_id": oid, "reason": "x",
                                                                  "items": [{"item_no": 1, "return_qty": 1}]}).status_code == 409)
r = c.post(f"/returns/{rid}/approve", headers=staff)
ret = r.json()
check("BR-26 processing 全部退貨連運費一起退", r.status_code == 200 and ret["refund_total"] == order["total"]
      and ret["order_status"] == "returned", ret)
r = c.get("/reports/sales", headers=staff, params={"period": "month", "date_from": "2026-09-01", "date_to": "2026-12-31"})
check("US-17 月報表", r.status_code == 200 and len(r.json()) > 0)
r = c.post("/discounts/", headers=staff, json={"discount_type": "special_event", "description": "E2E 重疊",
                                               "start_date": "2026-12-01", "end_date": "2026-12-10",
                                               "rate": 0.1, "product_ids": [9]})
check("BR-13 特殊活動折扣期間重疊被拒絕並提示代碼", r.status_code == 409 and "EVT-0001" in r.text, r.text)

# ---- 平台管理員 ----
admin = login("admin", "admin123")
check("BR-21 工作人員不能管理帳號", c.get("/admin/users", headers=staff).status_code == 403)
me = c.get("/auth/me", headers=cust).json()
r = c.put(f"/admin/users/{me['user_id']}/roles", headers=admin, json={"roles": ["customer", "staff"]})
check("US-19 指派角色", r.status_code == 200 and "staff" in r.json()["roles"])
check("角色立即生效", c.get("/orders/", headers=cust).status_code == 200)
r = c.patch(f"/admin/users/{me['user_id']}/status", headers=admin, json={"is_active": False})
check("US-19 停用帳號", r.status_code == 200 and r.json()["is_active"] is False)
check("停用後舊 token 失效", c.get("/auth/me", headers=cust).status_code == 401)
check("管理員不能移除自己的 admin 角色", c.put("/admin/users/1/roles", headers=admin, json={"roles": ["staff"]}).status_code == 409)

print(f"\n{'全部通過' if failures == 0 else f'{failures} 項失敗'}")
sys.exit(1 if failures else 0)
