"""STS：商店資訊與評價（STS-F-001～STS-F-004、BR-24）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_admin, require_customer
from app.models import Order, OrderItem, Product, Store, StoreReview, User
from app.schemas_w1 import Email, product_out

router = APIRouter()


class StoreIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1, max_length=200)
    email: Email
    phone: str = Field(min_length=1, max_length=20)


class ReviewIn(BaseModel):
    order_id: int
    rating: int = Field(ge=1, le=5, description="BR-24：評分須為 1 至 5 的整數")
    comment: str | None = Field(default=None, max_length=500)


def store_stats(db: Session) -> dict[int, tuple[int, float | None, int]]:
    products = dict(db.execute(select(Product.store_id, func.count())
                               .where(Product.is_listed.is_(True)).group_by(Product.store_id)).all())
    reviews = {sid: (avg, n) for sid, avg, n in db.execute(
        select(StoreReview.store_id, func.avg(StoreReview.rating), func.count()).group_by(StoreReview.store_id))}
    out = {}
    for sid in db.scalars(select(Store.store_id)):
        avg, n = reviews.get(sid, (None, 0))
        out[sid] = (products.get(sid, 0), round(float(avg), 1) if avg is not None else None, n)
    return out


def store_out(s: Store, st: tuple[int, float | None, int]) -> dict:
    return {"store_id": s.store_id, "name": s.name, "address": s.address, "email": s.email, "phone": s.phone,
            "product_count": st[0], "avg_rating": st[1], "review_count": st[2]}


def review_out(r: StoreReview) -> dict:
    return {"order_id": r.order_id, "store_id": r.store_id, "rating": r.rating, "comment": r.comment,
            "reviewed_at": r.reviewed_at, "customer_name": r.order.user.name}


def get_store_or_404(db: Session, store_id: int) -> Store:
    s = db.get(Store, store_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到這間商店")
    return s


@router.get("/")
def list_stores(db: Session = Depends(get_db)):
    stats = store_stats(db)
    return [store_out(s, stats[s.store_id]) for s in db.scalars(select(Store).order_by(Store.store_id))]


@router.get("/{store_id}")
def get_store(store_id: int, db: Session = Depends(get_db)):
    s = get_store_or_404(db, store_id)
    out = store_out(s, store_stats(db)[store_id])
    products = db.scalars(select(Product).where(Product.store_id == store_id, Product.is_listed.is_(True))
                          .order_by(Product.product_id))
    out["products"] = [product_out(db, p) for p in products]
    reviews = db.scalars(select(StoreReview).where(StoreReview.store_id == store_id)
                         .order_by(StoreReview.reviewed_at.desc(), StoreReview.order_id.desc()))
    out["reviews"] = [review_out(r) for r in reviews]
    return out


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_store(body: StoreIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """平台管理員新增商店（擴充 STS-F-002：SRS 只寫到修改，新增是為了讓平台能擴充門市）。"""
    s = Store(name=body.name, address=body.address, email=body.email, phone=body.phone)
    db.add(s)
    db.commit()
    db.refresh(s)
    return store_out(s, (0, None, 0))


@router.put("/{store_id}")
def update_store(store_id: int, body: StoreIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    s = get_store_or_404(db, store_id)
    s.name, s.address, s.email, s.phone = body.name, body.address, body.email, body.phone
    db.commit()
    return store_out(s, store_stats(db)[store_id])


@router.post("/{store_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(store_id: int, body: ReviewIn, db: Session = Depends(get_db),
                  user: User = Depends(require_customer)):
    get_store_or_404(db, store_id)
    order = db.get(Order, body.order_id)
    if order is None or order.user_id != user.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到這筆訂單")
    # BR-24 由後端先檢查，資料庫 trigger store_review_insert 與主鍵會再檢查一次
    if order.status != "closed":
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-24：只能評價狀態為 closed 的訂單")
    bought_here = db.scalar(select(func.count()).select_from(OrderItem)
                            .join(Product, Product.product_id == OrderItem.product_id)
                            .where(OrderItem.order_id == order.order_id, Product.store_id == store_id))
    if not bought_here:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-24：這筆訂單沒有購買該商店的商品")
    if db.get(StoreReview, (order.order_id, store_id)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-24：每筆訂單對每間商店只能評價一次")
    r = StoreReview(order_id=order.order_id, store_id=store_id, rating=body.rating, comment=body.comment)
    db.add(r)
    db.commit()
    db.refresh(r)
    return review_out(r)
