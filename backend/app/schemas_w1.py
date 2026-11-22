"""W1（AAS / 平台管理 / STS / PMS）共用的輸入輸出格式與序列化函式。"""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from app.models import Product, User
from app.services.pricing import event_discount_for, event_discounts_for
from app.clock import tw_now, tw_today  # noqa: F401

Role = Literal["customer", "staff", "admin"]


# ---------- 使用者 ----------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    loginid: str
    name: str
    email: str
    address: str | None
    phone: str | None
    is_active: bool
    roles: list[str]
    store_id: int | None
    store_name: str | None
    created_at: datetime


def user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


LoginId = Annotated[str, Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.\-]+$")]
Password = Annotated[str, Field(min_length=6, max_length=72)]   # bcrypt 只看前 72 bytes
Name = Annotated[str, Field(min_length=1, max_length=50)]
Email = Annotated[EmailStr, Field(max_length=100)]
Address = Annotated[str | None, Field(max_length=200)]
Phone = Annotated[str | None, Field(max_length=20)]


class ProfileIn(BaseModel):
    name: Name
    email: Email
    address: Address = None
    phone: Phone = None


# ---------- 商品 ----------
_UNSET = object()


def event_discount_out(db: Session, product_id: int, on: date | None = None, d=_UNSET) -> dict | None:
    if d is _UNSET:
        d = event_discount_for(db, product_id, on or tw_today())
    if d is None:
        return None
    return {
        "discount_code": d.discount_code, "description": d.description,
        "rate": float(d.rate) if d.rate is not None else None,
        "buy_qty": d.buy_qty, "free_qty": d.free_qty,
        "start_date": d.start_date, "end_date": d.end_date,
    }


def product_out(db: Session, p: Product, on: date | None = None, events: dict | None = None) -> dict:
    """契約 §5 的 Product 物件；金額一律為整數。events 為預先批次查好的 {product_id: 特殊活動折扣}。"""
    event = (event_discount_out(db, p.product_id, on) if events is None
             else event_discount_out(db, p.product_id, on, events.get(p.product_id)))
    return {
        "product_id": p.product_id, "store_id": p.store_id, "store_name": p.store.name,
        "name": p.name, "description": p.description, "category": p.category, "image_url": p.image_url,
        "price": int(p.price), "stock": p.stock, "is_listed": p.is_listed,
        "created_at": p.created_at, "updated_at": p.updated_at,
        "event_discount": event,
    }


def products_out(db: Session, products, on: date | None = None) -> list[dict]:
    """商品列表序列化：特殊活動折扣一次批次查詢。"""
    products = list(products)
    on = on or tw_today()
    events = event_discounts_for(db, [p.product_id for p in products], on)
    return [product_out(db, p, on, events) for p in products]
