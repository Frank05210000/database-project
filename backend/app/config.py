import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://fuwa:fuwa@localhost:5433/fuwa")
# Neon／Vercel 給的是 postgres:// 或 postgresql://，SQLAlchemy 要指定 psycopg 驅動
for _prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(_prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(_prefix):]
# 在 Vercel（serverless）上每次請求用完就關閉連線，不保留連線池
SERVERLESS = bool(os.getenv("VERCEL"))
JWT_SECRET = os.getenv("JWT_SECRET", "fuwafuwa-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
