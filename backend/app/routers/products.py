"""PMS：商品瀏覽、搜尋與工作人員維護（PMS-F-001～PMS-F-008、BR-04、BR-06、BR-20）。"""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_optional_user, require_staff
from app.models import OrderItem, Product, Store, User
from app.schemas_w1 import product_out

router = APIRouter()


class ProductIn(BaseModel):
    store_id: int
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    category: str | None = Field(default=None, max_length=30)
    image_url: str | None = Field(default=None, max_length=300)
    price: int = Field(gt=0, description="BR-04：價格須大於 0")
    stock: int = Field(ge=0, description="BR-06：庫存不得為負數")
    is_listed: bool = True


def is_staff(user: User | None) -> bool:
    return user is not None and user.has_role("staff")


def escape_like(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_product_or_404(db: Session, product_id: int) -> Product:
    p = db.get(Product, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到這項商品")
    return p


def ensure_store(db: Session, store_id: int) -> None:
    if db.get(Store, store_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到這間商店")


@router.get("/")
def list_products(q: str | None = None, category: str | None = None, store_id: int | None = None,
                  sort: Literal["newest", "price_asc", "price_desc"] = "newest",
                  include_unlisted: bool = False,
                  db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    stmt = select(Product)
    if not (include_unlisted and is_staff(user)):   # 下架商品只有工作人員看得到
        stmt = stmt.where(Product.is_listed.is_(True))
    if q and q.strip():
        pat = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(or_(Product.name.ilike(pat, escape="\\"), Product.description.ilike(pat, escape="\\")))
    if category:
        stmt = stmt.where(Product.category == category)
    if store_id is not None:
        stmt = stmt.where(Product.store_id == store_id)
    order = {
        "newest": (Product.created_at.desc(), Product.product_id.desc()),
        "price_asc": (Product.price.asc(), Product.product_id.asc()),
        "price_desc": (Product.price.desc(), Product.product_id.asc()),
    }[sort]
    today = date.today()
    return [product_out(db, p, today) for p in db.scalars(stmt.order_by(*order))]


@router.get("/categories")
def categories(db: Session = Depends(get_db)) -> list[str]:
    return list(db.scalars(select(Product.category).distinct()
                           .where(Product.is_listed.is_(True), Product.category.is_not(None))
                           .order_by(Product.category)))


def also_bought(db: Session, product_id: int, limit: int = 4) -> list[Product]:
    """與此商品出現在同一筆訂單中次數最多的其他上架商品。"""
    mine = select(OrderItem.order_id).where(OrderItem.product_id == product_id)
    cnt = func.count(OrderItem.order_id)
    rows = db.execute(
        select(OrderItem.product_id, cnt)
        .join(Product, Product.product_id == OrderItem.product_id)
        .where(OrderItem.order_id.in_(mine), OrderItem.product_id != product_id, Product.is_listed.is_(True))
        .group_by(OrderItem.product_id).order_by(cnt.desc(), OrderItem.product_id).limit(limit)).all()
    return [db.get(Product, pid) for pid, _ in rows]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db),
                user: User | None = Depends(get_optional_user)):
    p = get_product_or_404(db, product_id)
    if not p.is_listed and not is_staff(user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到這項商品")
    today = date.today()
    out = product_out(db, p, today)
    out["also_bought"] = [product_out(db, x, today) for x in also_bought(db, product_id)]
    return out


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_product(body: ProductIn, db: Session = Depends(get_db), _: User = Depends(require_staff)):
    ensure_store(db, body.store_id)
    p = Product(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return product_out(db, p)


@router.put("/{product_id}")
def update_product(product_id: int, body: ProductIn, db: Session = Depends(get_db),
                   _: User = Depends(require_staff)):
    p = get_product_or_404(db, product_id)
    ensure_store(db, body.store_id)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)   # updated_at 由 trigger 更新
    return product_out(db, p)


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_staff)):
    p = get_product_or_404(db, product_id)
    referenced = db.scalar(select(func.count()).select_from(OrderItem).where(OrderItem.product_id == product_id))
    if referenced:
        # BR-20：已被訂單引用的商品不可刪除，改為下架
        p.is_listed = False
        db.commit()
        return {"deleted": False, "unlisted": True,
                "detail": "BR-20：商品已有訂單紀錄，無法刪除，已改為下架"}
    db.delete(p)
    db.commit()
    return {"deleted": True, "unlisted": False}
