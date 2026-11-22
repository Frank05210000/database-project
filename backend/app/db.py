from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app import config

engine = (create_engine(config.DATABASE_URL, poolclass=NullPool) if config.SERVERLESS
          else create_engine(config.DATABASE_URL, pool_pre_ping=True))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_actor(db: Session, user_id: int) -> None:
    """讓 trigger 知道是誰在操作（order_status_history.changed_by）。只在目前交易內有效。"""
    db.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user_id)})
