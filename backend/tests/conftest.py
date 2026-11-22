"""測試共用設定：每個測試都用一個全新的資料庫 fuwa_test（套用 db/init 的三個 SQL 檔）。

需要 docker compose 的 db 服務（localhost:5433）。執行：
    cd backend && .venv/bin/pytest
"""
import os
from pathlib import Path

import psycopg
import pytest

ADMIN_DSN = os.getenv("TEST_ADMIN_DSN", "postgresql://fuwa:fuwa@localhost:5433/postgres")
TEST_DB = os.getenv("TEST_DB_NAME", "fuwa_test")  # 並行跑測試時各自指定不同名稱
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", f"postgresql+psycopg://fuwa:fuwa@localhost:5433/{TEST_DB}")

INIT_DIR = Path(__file__).resolve().parents[2] / "db" / "init"
# 測試只用 schema、trigger 與基本種子資料（不含 04_demo_data.sql 的示範訂單），結果才可預期
SQL = "\n".join((INIT_DIR / f).read_text() for f in ("01_schema.sql", "02_triggers.sql", "03_seed.sql"))
TEST_DSN = os.environ["DATABASE_URL"].replace("+psycopg", "")


@pytest.fixture(scope="session", autouse=True)
def _create_test_db():
    with psycopg.connect(ADMIN_DSN, autocommit=True) as conn:
        conn.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
        conn.execute(f"CREATE DATABASE {TEST_DB}")
    yield


@pytest.fixture(autouse=True)
def fresh_db(_create_test_db):
    """每個測試前重建 schema 並灌入種子資料。"""
    from app.db import engine
    engine.dispose()
    with psycopg.connect(TEST_DSN, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.execute(SQL)
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    from app.db import SessionLocal
    s = SessionLocal()
    yield s
    s.close()


def login(client, loginid: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"loginid": loginid, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin_h(client):
    return login(client, "admin", "admin123")


@pytest.fixture
def staff_h(client):
    return login(client, "staff", "staff123")


@pytest.fixture
def alice_h(client):
    return login(client, "alice", "customer123")


@pytest.fixture
def bob_h(client):
    return login(client, "bob", "customer123")


@pytest.fixture
def xinyi_h(client):
    return login(client, "staff_xinyi", "staff123")
