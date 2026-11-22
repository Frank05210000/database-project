"""AAS 帳號與平台管理（AAS-F-001～AAS-F-008、BR-01、BR-02、BR-21）。"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import login

NEW_USER = {"loginid": "dora", "name": "朵拉", "password": "secret1", "email": "dora@example.com",
            "address": "台南市東區大學路 1 號", "phone": "0955-000-111"}


# ---------- 註冊與登入 ----------
def test_register_then_login(client):
    r = client.post("/api/auth/register", json=NEW_USER)
    assert r.status_code == 201, r.text
    u = r.json()
    assert u["loginid"] == "dora" and u["roles"] == ["customer"] and u["is_active"] is True
    assert "password_hash" not in u and u["created_at"]
    r = client.post("/api/auth/login", json={"loginid": "dora", "password": "secret1"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["user"]["user_id"] == u["user_id"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["name"] == "朵拉"


def test_register_duplicate_loginid_rejected(client):
    r = client.post("/api/auth/register", json={**NEW_USER, "loginid": "alice"})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-01")


def test_register_validation(client):
    assert client.post("/api/auth/register", json={**NEW_USER, "password": "123"}).status_code == 422
    assert client.post("/api/auth/register", json={**NEW_USER, "email": "not-an-email"}).status_code == 422


def test_login_wrong_password_and_unknown_user(client):
    assert client.post("/api/auth/login", json={"loginid": "alice", "password": "nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"loginid": "ghost", "password": "x"}).status_code == 401


def test_disabled_account_cannot_login(client):
    r = client.post("/api/auth/login", json={"loginid": "carol", "password": "customer123"})
    assert r.status_code == 403 and r.json()["detail"] == "帳號已停用"


def test_me_requires_login(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_update_profile_and_password(client, alice_h):
    r = client.put("/api/auth/me", headers=alice_h,
                   json={"name": "陳愛麗二號", "email": "alice2@example.com", "address": "新地址", "phone": None})
    assert r.status_code == 200 and r.json()["name"] == "陳愛麗二號" and r.json()["phone"] is None
    r = client.put("/api/auth/me/password", headers=alice_h,
                   json={"old_password": "wrong", "new_password": "newpass1"})
    assert r.status_code == 400
    r = client.put("/api/auth/me/password", headers=alice_h,
                   json={"old_password": "customer123", "new_password": "newpass1"})
    assert r.status_code == 200
    assert client.post("/api/auth/login", json={"loginid": "alice", "password": "customer123"}).status_code == 401
    login(client, "alice", "newpass1")


# ---------- 平台管理：授權 ----------
def test_admin_endpoints_require_admin(client, alice_h, staff_h):
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/users", headers=alice_h).status_code == 403
    assert client.get("/api/admin/stats", headers=staff_h).status_code == 403
    manager_h = login(client, "manager", "staff123")    # staff＋admin
    assert client.get("/api/admin/users", headers=manager_h).status_code == 200


# ---------- 平台管理：查詢與統計 ----------
def test_list_and_search_users(client, admin_h):
    users = client.get("/api/admin/users", headers=admin_h).json()
    assert [u["loginid"] for u in users] == ["admin", "staff", "manager", "alice", "bob", "carol"]
    assert next(u for u in users if u["loginid"] == "manager")["roles"] == ["staff", "admin"]
    r = client.get("/api/admin/users", params={"q": "example.com"}, headers=admin_h).json()
    assert {u["loginid"] for u in r} == {"alice", "bob", "carol"}
    r = client.get("/api/admin/users", params={"q": "王小"}, headers=admin_h).json()
    assert [u["loginid"] for u in r] == ["staff"]
    r = client.get("/api/admin/users", params={"role": "admin"}, headers=admin_h).json()
    assert {u["loginid"] for u in r} == {"admin", "manager"}
    r = client.get("/api/admin/users", params={"is_active": "false"}, headers=admin_h).json()
    assert [u["loginid"] for u in r] == ["carol"]
    assert client.get("/api/admin/users/4", headers=admin_h).json()["loginid"] == "alice"
    assert client.get("/api/admin/users/999", headers=admin_h).status_code == 404


def test_stats(client, admin_h):
    assert client.get("/api/admin/stats", headers=admin_h).json() == {
        "users": 6, "customers": 3, "staff": 2, "admins": 2, "inactive": 1}


# ---------- 平台管理：新增與修改 ----------
def test_admin_creates_user_with_any_roles(client, admin_h):
    r = client.post("/api/admin/users", headers=admin_h,
                    json={**NEW_USER, "loginid": "eve", "roles": ["admin", "staff"]})
    assert r.status_code == 201, r.text
    assert r.json()["roles"] == ["staff", "admin"]
    eve_h = login(client, "eve", "secret1")
    assert client.get("/api/admin/stats", headers=eve_h).status_code == 200


def test_admin_create_user_violations(client, admin_h):
    r = client.post("/api/admin/users", headers=admin_h, json={**NEW_USER, "loginid": "bob", "roles": ["customer"]})
    assert r.status_code == 409 and r.json()["detail"].startswith("BR-01")
    r = client.post("/api/admin/users", headers=admin_h, json={**NEW_USER, "roles": ["boss"]})
    assert r.status_code == 422
    r = client.post("/api/admin/users", headers=admin_h, json={**NEW_USER, "roles": []})
    assert r.status_code == 409


def test_admin_updates_user_and_resets_password(client, admin_h):
    r = client.put("/api/admin/users/5", headers=admin_h,
                   json={"name": "張寶博", "email": "bob.new@example.com", "address": "新北", "phone": "0900",
                         "password": "reset99"})
    assert r.status_code == 200 and r.json()["email"] == "bob.new@example.com"
    login(client, "bob", "reset99")
    # 不給 password 時不改密碼
    client.put("/api/admin/users/5", headers=admin_h, json={"name": "Bob", "email": "b@example.com"})
    login(client, "bob", "reset99")


# ---------- 平台管理：角色 ----------
def test_role_assignment_takes_effect_immediately(client, admin_h, bob_h):
    product = {"store_id": 1, "name": "測試商品", "price": 100, "stock": 5}
    assert client.post("/api/products/", headers=bob_h, json=product).status_code == 403
    r = client.put("/api/admin/users/5/roles", headers=admin_h, json={"roles": ["customer", "staff"]})
    assert r.status_code == 200 and r.json()["roles"] == ["customer", "staff"]
    # 同一張 token，不必重新登入
    assert client.post("/api/products/", headers=bob_h, json=product).status_code == 201
    r = client.put("/api/admin/users/5/roles", headers=admin_h, json={"roles": ["staff"]})
    assert r.json()["roles"] == ["staff"]
    r = client.post("/api/stores/1/reviews", headers=bob_h, json={"order_id": 1, "rating": 5})
    assert r.status_code == 403   # 已不是顧客（BR-21）


def test_roles_replace_violations(client, admin_h):
    r = client.put("/api/admin/users/1/roles", headers=admin_h, json={"roles": ["staff"]})
    assert r.status_code == 409 and "自己" in r.json()["detail"]
    assert client.put("/api/admin/users/4/roles", headers=admin_h, json={"roles": []}).status_code == 409
    assert client.put("/api/admin/users/4/roles", headers=admin_h, json={"roles": ["root"]}).status_code == 422
    assert client.put("/api/admin/users/99/roles", headers=admin_h, json={"roles": ["staff"]}).status_code == 404
    # 自己保留 admin、再加 staff 是可以的
    r = client.put("/api/admin/users/1/roles", headers=admin_h, json={"roles": ["admin", "staff"]})
    assert r.status_code == 200 and r.json()["roles"] == ["staff", "admin"]


def test_manager_can_remove_admin_from_other_admin_but_db_keeps_one(client, admin_h, db):
    manager_h = login(client, "manager", "staff123")
    # manager 拿掉 admin 的 admin 角色：仍有 manager 一位啟用中的管理員 → 允許
    r = client.put("/api/admin/users/1/roles", headers=manager_h, json={"roles": ["staff"]})
    assert r.status_code == 200
    assert client.get("/api/admin/users", headers=admin_h).status_code == 403
    # 直接改資料庫拿掉最後一位管理員 → deferred trigger 在 commit 時拒絕
    db.execute(text("DELETE FROM user_role WHERE user_id = 3 AND role = 'admin'"))
    with pytest.raises(DBAPIError, match="至少要保留一位"):
        db.commit()
    db.rollback()


# ---------- 平台管理：停用與啟用 ----------
def test_deactivate_rejects_existing_token_and_login(client, admin_h, alice_h):
    assert client.get("/api/auth/me", headers=alice_h).status_code == 200
    r = client.patch("/api/admin/users/4/status", headers=admin_h, json={"is_active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert client.get("/api/auth/me", headers=alice_h).status_code == 401
    assert client.post("/api/auth/login", json={"loginid": "alice", "password": "customer123"}).status_code == 403
    client.patch("/api/admin/users/4/status", headers=admin_h, json={"is_active": True})
    login(client, "alice", "customer123")


def test_enable_disabled_user(client, admin_h):
    r = client.patch("/api/admin/users/6/status", headers=admin_h, json={"is_active": True})
    assert r.status_code == 200
    login(client, "carol", "customer123")


def test_admin_cannot_deactivate_self(client, admin_h):
    r = client.patch("/api/admin/users/1/status", headers=admin_h, json={"is_active": False})
    assert r.status_code == 409 and "自己" in r.json()["detail"]
    assert client.get("/api/auth/me", headers=admin_h).status_code == 200


def test_deactivated_admin_token_rejected_and_self_rule(client, admin_h):
    manager_h = login(client, "manager", "staff123")
    assert client.patch("/api/admin/users/1/status", headers=manager_h, json={"is_active": False}).status_code == 200
    assert client.get("/api/admin/stats", headers=admin_h).status_code == 401
    # manager 現在是唯一啟用中的管理員，也不能停用自己
    assert client.patch("/api/admin/users/3/status", headers=manager_h, json={"is_active": False}).status_code == 409
