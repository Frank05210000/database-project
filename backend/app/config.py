import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://fuwa:fuwa@localhost:5433/fuwa")
JWT_SECRET = os.getenv("JWT_SECRET", "fuwafuwa-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
